import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QToolBar, QVBoxLayout, QWidget, QInputDialog, QLineEdit, QMessageBox
)
from PyQt6.QtGui import (
    QPolygonF, QPen, QColor, QAction, QPainter, QCursor
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
import uuid


class ConnectionNode:
    def __init__(self, from_item, to_item, line_item):
        self.from_item = from_item
        self.to_item = to_item
        self.line_item = line_item
        self.next = None


class ConnectionList:
    def __init__(self):
        self.head = None

    def add_connection(self, from_item, to_item, line_item):
        new_node = ConnectionNode(from_item, to_item, line_item)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node

    def print_connections(self):
        current = self.head
        print("Conexiones:")
        while current:
            print(f"{current.from_item.shape_type} → {current.to_item.shape_type}")
            current = current.next

    def remove_connections_with(self, item):
        current = self.head
        prev = None

        while current:
            if current.from_item == item or current.to_item == item:
                # Remove the line from the scene
                if current.line_item.scene():
                    current.line_item.scene().removeItem(current.line_item)

                # Remove the node from the list
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
            else:
                prev = current
            current = current.next

    def update_connections_for_item(self, item):
        current = self.head
        while current:
            if current.from_item == item or current.to_item == item:
                start_pos = current.from_item.center()
                end_pos = current.to_item.center()
                current.line_item.setLine(QLineF(start_pos, end_pos))
            current = current.next


class FlowShape(QGraphicsItem):
    def __init__(self, shape_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = shape_type
        self.id = str(uuid.uuid4())
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                    QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._connections = []
        self._is_start_connector = False
        self._highlight_color = None
        self.text = ""

    def boundingRect(self):
        return QRectF(0, 0, 100, 60)

    def paint(self, painter: QPainter, option, widget):
        pen = QPen(Qt.GlobalColor.black, 2)
        if self._is_start_connector:
            pen = QPen(Qt.GlobalColor.green, 3)
        elif self._highlight_color:
            pen = QPen(self._highlight_color, 3)

        painter.setPen(pen)

        # Dibujar la figura según el tipo
        if self.shape_type == 'start_end':
            brush = QColor('lightgreen')
            painter.setBrush(brush)
            painter.drawEllipse(self.boundingRect())
        elif self.shape_type == 'process':
            brush = QColor('lightblue')
            painter.setBrush(brush)
            painter.drawRect(self.boundingRect())
        elif self.shape_type == 'decision':
            brush = QColor('orange')
            painter.setBrush(brush)
            points = [QPointF(50, 0), QPointF(100, 30), QPointF(50, 60), QPointF(0, 30)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'input_output':
            brush = QColor('plum')
            painter.setBrush(brush)
            points = [QPointF(20, 0), QPointF(100, 0), QPointF(80, 60), QPointF(0, 60)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'connector':
            brush = QColor('gray')
            painter.setBrush(brush)
            painter.drawEllipse(35, 15, 30, 30)

        # Dibujar el texto si existe
        if self.text:
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            text_rect = self.boundingRect().adjusted(5, 5, -5, -5)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)

    def add_connection(self, line_id):
        if line_id not in self._connections:
            self._connections.append(line_id)

    def remove_connection(self, line_id):
        if line_id in self._connections:
            self._connections.remove(line_id)

    def set_as_start_connector(self, is_start):
        self._is_start_connector = is_start
        self.update()

    def highlight(self, color):
        self._highlight_color = color
        self.update()

    def center(self):
        return self.scenePos() + QPointF(self.boundingRect().width() / 2,
                                        self.boundingRect().height() / 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if scene and hasattr(scene, 'connections'):
                scene.connections.update_connections_for_item(self)
        return super().itemChange(change, value)


class FlowScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.selected_shape = None
        self.connection_mode = False
        self.text_mode = False  # Nuevo modo para agregar texto
        self.first_item = None
        self.connections = ConnectionList()
        self._temp_line = None


    def set_text_mode(self, enabled):
        self.text_mode = enabled
        self.connection_mode = False
        self.selected_shape = None
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None

    def set_shape_type(self, shape_type):

        self.text_mode = False
        self.selected_shape = shape_type
        self.connection_mode = False
        self.first_item = None
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None

    def set_connection_mode(self, enabled):
        self.selected_shape = None
        self.connection_mode = enabled
        if not enabled and self.first_item:
            self.first_item.set_as_start_connector(False)
            self.first_item = None
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        
        if self.selected_shape:
            shape = FlowShape(self.selected_shape)
            shape.setPos(event.scenePos())
            self.addItem(shape)
            return
            
        elif self.connection_mode:
            # Lógica existente para conexiones
            if isinstance(item, FlowShape):
                if self.first_item is None:
                    self.first_item = item
                    self.first_item.set_as_start_connector(True)
                else:
                    second_item = item
                    if second_item != self.first_item:
                        self.create_connection(self.first_item, second_item)
                    self.first_item.set_as_start_connector(False)
                    self.first_item = None
            elif self.first_item:
                self.first_item.set_as_start_connector(False)
                self.first_item = None
            return
                
        elif self.text_mode and isinstance(item, FlowShape):
            # Lógica para agregar texto
            text, ok = QInputDialog.getText(
                None, 
                "Agregar texto", 
                f"Ingrese el texto para la figura:", 
                QLineEdit.EchoMode.Normal,
                item.text
            )
            if ok:
                item.text = text
                item.update()  # Forzar redibujado
            return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.connection_mode and self.first_item:
            if not self._temp_line:
                self._temp_line = QGraphicsLineItem()
                self._temp_line.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine))
                self.addItem(self._temp_line)

            start_pos = self.first_item.center()
            end_pos = event.scenePos()
            self._temp_line.setLine(QLineF(start_pos, end_pos))

        super().mouseMoveEvent(event)

    def create_connection(self, from_item, to_item):
        line_id = str(uuid.uuid4())

        line = QGraphicsLineItem()
        line.setPen(QPen(Qt.GlobalColor.black, 2))
        self.addItem(line)

        # Actualizar la posición inicial de la línea
        start_pos = from_item.center()
        end_pos = to_item.center()
        line.setLine(QLineF(start_pos, end_pos))
        # Poner la linea detras de las figuras
        line.setZValue(-1)
        line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        from_item.add_connection(line_id)
        to_item.add_connection(line_id)

        self.connections.add_connection(from_item, to_item, line)

        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None


    def removeItem(self, item):
        if isinstance(item, FlowShape):
            self.connections.remove_connections_with(item)
        super().removeItem(item)


class FlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Diagramas de Flujo")
        self.setStyleSheet("background-color: gray")

        self.scene = FlowScene()
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(0, 0, 1000, 800)

        toolbar = QToolBar("Formas")
        self.addToolBar(toolbar)

        # Botones de figura
        self.add_shape_action(toolbar, "Inicio/Fin", 'start_end')
        self.add_shape_action(toolbar, "Proceso", 'process')
        self.add_shape_action(toolbar, "Decisión", 'decision')
        self.add_shape_action(toolbar, "Entrada/Salida", 'input_output')
        self.add_shape_action(toolbar, "Conector", 'connector')

        toolbar.addSeparator()

        # Botón para desactivar creación de figuras
        select_action = QAction("Seleccionar / Mover", self)
        select_action.triggered.connect(self.toggle_default_mode)
        toolbar.addAction(select_action)

        # Botón para activar conexión
        connect_action = QAction("Conectar Figuras", self)
        connect_action.triggered.connect(self.toggle_connection_mode)
        toolbar.addAction(connect_action)

        # Nuevo botón para agregar texto
        text_action = QAction("Agregar Texto", self)
        text_action.triggered.connect(self.toggle_text_mode)
        toolbar.addAction(text_action)

        # Botón para poner modo de eliminación de figuras
        delete_action = QAction("Eliminar Figura", self)
        # Agregar la función de eliminación de figuras
        delete_action.triggered.connect(self.delete_shape)
        toolbar.addAction(delete_action)

        layout = QVBoxLayout()
        layout.addWidget(self.view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def delete_shape(self):
        selected_items = self.scene.selectedItems()
        if selected_items:
            for item in selected_items:
                self.scene.removeItem(item)
                if isinstance(item, FlowShape):
                    self.scene.connections.remove_connections_with(item)
                    item.setParentItem(None)
                else:
                    self.scene.removeItem(item)
        else:
            # Mostrar mensaje al usuario si no hay figuras seleccionadas
            QMessageBox.warning(self, "Advertencia", "No hay figuras seleccionadas para eliminar.")


    def add_shape_action(self, toolbar, name, shape_type):
        action = QAction(name, self)
        action.triggered.connect(lambda: self.scene.set_shape_type(shape_type))
        toolbar.addAction(action)

    def toggle_text_mode(self):
        current_mode = self.scene.text_mode
        self.scene.set_text_mode(not current_mode)
        
        # Cambiar cursor cuando está en modo texto
        if self.scene.text_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_connection_mode(self):
        current_mode = self.scene.connection_mode
        self.scene.set_connection_mode(not current_mode)

        # Cambiar el cursor cuando esté en modo conexión
        if self.scene.connection_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_default_mode(self):
        self.scene.set_shape_type(None)
        self.scene.set_connection_mode(False)
        self.scene.set_text_mode(False)
        self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.scene.selected_shape = None
        self.scene.set_shape_type(None)



