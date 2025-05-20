import sys

from PyQt6.QtWidgets import ( # type: ignore
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QToolBar, QVBoxLayout, QWidget, QInputDialog, QLineEdit,
    QMessageBox, QHBoxLayout, QLabel, QSizePolicy, QPushButton
)
from PyQt6.QtGui import ( # type: ignore
    QPolygonF, QPen, QColor, QAction, QPainter, QCursor
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF # type: ignore
import uuid
from collections import deque

from parser import Parser


class ConnectionNode:
    def __init__(self, from_item, to_item, line_item):
        self.from_item = from_item
        self.to_item = to_item
        self.line_item = line_item
        self.next = None

    def __str__(self):
        return f"{self.from_item.text} -> {self.to_item.text}"


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
            from_text = current.from_item.text if current.from_item.text else current.from_item.shape_type
            to_text = current.to_item.text if current.to_item.text else current.to_item.shape_type
            print(f"'{from_text}' ({current.from_item.id}) → '{to_text}' ({current.to_item.id})")
            current = current.next

    def remove_connections_with(self, item_to_remove):
        current = self.head
        prev = None
        while current:
            if current.from_item == item_to_remove or current.to_item == item_to_remove:
                if current.line_item.scene():
                    current.line_item.scene().removeItem(current.line_item)
                
                if prev:
                    prev.next = current.next
                else: 
                    self.head = current.next
                
                removed_node = current
                current = current.next
                del removed_node 
                continue 

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

    def get_connections_from(self, from_item): 
        connections = []
        current = self.head
        while current:
            if current.from_item == from_item:
                connections.append(current.to_item)
            current = current.next
        return connections


class FlowShape(QGraphicsItem):
    def __init__(self, shape_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = shape_type
        self.id = str(uuid.uuid4())
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._is_start_connector = False
        self._highlight_color = None
        self.text = ""

    def boundingRect(self):
        return QRectF(0, 0, 100, 60)

    def paint(self, painter: QPainter, option, widget):
        pen = QPen(Qt.GlobalColor.black, 2)
        if self.scene() and hasattr(self.scene(), 'start_node') and self.scene().start_node == self:
            pen = QPen(QColor("gold"), 3, Qt.PenStyle.SolidLine)
        elif self._is_start_connector: 
            pen = QPen(Qt.GlobalColor.green, 3, Qt.PenStyle.DashLine)
        elif self._highlight_color: 
            pen = QPen(self._highlight_color, 3)

        painter.setPen(pen)
        
        brush_color = QColor('lightgray') 
        if self.shape_type == 'start_end': brush_color = QColor('lightgreen')
        elif self.shape_type == 'process': brush_color = QColor('lightblue')
        elif self.shape_type == 'decision': brush_color = QColor('orange')
        elif self.shape_type == 'input_output': brush_color = QColor('plum')
        elif self.shape_type == 'connector': brush_color = QColor('darkgray')
        
        painter.setBrush(QColor(brush_color))

        if self.shape_type == 'start_end':
            painter.drawEllipse(self.boundingRect())
        elif self.shape_type == 'process':
            painter.drawRect(self.boundingRect())
        elif self.shape_type == 'decision':
            points = [QPointF(50, 0), QPointF(100, 30), QPointF(50, 60), QPointF(0, 30)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'input_output':
            points = [QPointF(20, 0), QPointF(100, 0), QPointF(80, 60), QPointF(0, 60)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'connector':
            painter.drawEllipse(35, 15, 30, 30)

        if self.text:
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            text_rect = self.boundingRect().adjusted(5, 5, -5, -5)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)

    def set_as_start_connector(self, is_start): 
        if self._is_start_connector != is_start:
            self._is_start_connector = is_start
            self.update()

    def highlight(self, color): 
        if self._highlight_color != color:
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
        self.text_mode = False
        
        self.first_item = None 
        self._temp_line = None 
        
        self.connections = ConnectionList()
        self.start_node = None 

    def set_shape_type(self, shape_type): 
        is_activating = shape_type is not None
        self.selected_shape = shape_type 

        if is_activating:
            self.set_connection_mode(False) 
            self.set_text_mode(False)       

    def set_connection_mode(self, enabled):
        self.connection_mode = enabled
        if enabled:
            self.set_shape_type(None)   
            self.set_text_mode(False)   
        else: 
            if self.first_item: 
                self.first_item.set_as_start_connector(False)
                self.first_item = None
            if self._temp_line: 
                if self._temp_line.scene(): 
                    self.removeItem(self._temp_line)
                self._temp_line = None

    def set_text_mode(self, enabled):
        self.text_mode = enabled
        if enabled:
            self.set_shape_type(None)       
            self.set_connection_mode(False) 

    def mousePressEvent(self, event):
        item_at_click = self.itemAt(event.scenePos(), self.views()[0].transform())
        
        if self.selected_shape: 
            shape = FlowShape(self.selected_shape)
            shape.setPos(event.scenePos())
            self.addItem(shape)
            if shape.shape_type == 'start_end' and self.start_node is None:
                self.set_start_node(shape) 
            return 
            
        elif self.connection_mode:
            if isinstance(item_at_click, FlowShape):
                if self.first_item is None: 
                    self.first_item = item_at_click
                    self.first_item.set_as_start_connector(True)
                else: 
                    second_item = item_at_click
                    if second_item != self.first_item:
                        self.create_connection(self.first_item, second_item)
                    
                    self.first_item.set_as_start_connector(False)
                    self.first_item = None
                    if self._temp_line: 
                        if self._temp_line.scene():
                           self.removeItem(self._temp_line)
                        self._temp_line = None
            else: 
                if self.first_item: 
                    self.first_item.set_as_start_connector(False)
                    self.first_item = None
                if self._temp_line: 
                    if self._temp_line.scene():
                        self.removeItem(self._temp_line)
                    self._temp_line = None
            return 
                
        elif self.text_mode: 
            if isinstance(item_at_click, FlowShape):
                text, ok = QInputDialog.getText(
                    self.views()[0], 
                    "Agregar texto", 
                    f"Ingrese el texto para la figura:", 
                    QLineEdit.EchoMode.Normal,
                    item_at_click.text
                )
                if ok: 
                    item_at_click.text = text
                    item_at_click.update() 
            return 

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.connection_mode and self.first_item: 
            if not self._temp_line: 
                self._temp_line = QGraphicsLineItem()
                self._temp_line.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
                self.addItem(self._temp_line)
            start_pos = self.first_item.center()
            end_pos = event.scenePos()
            self._temp_line.setLine(QLineF(start_pos, end_pos))
        else:
            super().mouseMoveEvent(event) 

    def create_connection(self, from_item, to_item):
        line = QGraphicsLineItem()
        line.setPen(QPen(Qt.GlobalColor.black, 2))
        self.addItem(line)
        start_pos = from_item.center()
        end_pos = to_item.center()
        line.setLine(QLineF(start_pos, end_pos))
        line.setZValue(-1) 
        line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.connections.add_connection(from_item, to_item, line)

    def removeItem(self, item): 
        if isinstance(item, FlowShape):
            if item == self.start_node:
                self.set_start_node(None)
            self.connections.remove_connections_with(item)
        
        if item.scene(): 
            super().removeItem(item)

    def set_start_node(self, node): 
        if self.start_node and self.start_node != node:
            self.start_node.update() 
        self.start_node = node
        if self.start_node:
            self.start_node.update() 

class FlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Diagramas de Flujo")
        self.setStyleSheet("background-color: gray") 

        self.scene = FlowScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing) 
        self.scene.setSceneRect(0, 0, 1000, 800) 
        self.view.setMaximumSize(1000, 800) 
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) 
        
        toolbar = QToolBar("Formas") 
        self.addToolBar(toolbar)

        self.add_shape_action(toolbar, "Inicio/Fin", 'start_end')
        self.add_shape_action(toolbar, "Proceso", 'process')
        self.add_shape_action(toolbar, "Decisión", 'decision')
        self.add_shape_action(toolbar, "Entrada/Salida", 'input_output')
        self.add_shape_action(toolbar, "Conector", 'connector')
        toolbar.addSeparator()

        self.select_action = QAction("Seleccionar / Mover", self)
        self.select_action.triggered.connect(self.toggle_default_mode)
        toolbar.addAction(self.select_action)

        self.connect_action = QAction("Conectar Figuras", self)
        self.connect_action.triggered.connect(self.toggle_connection_mode)
        toolbar.addAction(self.connect_action)

        self.text_action = QAction("Agregar Texto", self)
        self.text_action.triggered.connect(self.toggle_text_mode)
        toolbar.addAction(self.text_action)
        
        self.delete_action = QAction("Eliminar Figura", self) 
        self.delete_action.triggered.connect(self.delete_shape) # Nombre de método original
        toolbar.addAction(self.delete_action)

        main_layout = QHBoxLayout()

        layout = QHBoxLayout() 
        layout.addWidget(self.view)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft) 

        layout1 = QVBoxLayout()
        self.compilation_output_label = QLabel("Presione 'Compilar' para ver el flujo.")
        self.compilation_output_label.setStyleSheet("background-color: white; border: 1px solid black; padding: 5px;")
        self.compilation_output_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.compilation_output_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.compilation_output_label.setWordWrap(True)

        button_compile = QPushButton("Compilar") 
        button_compile.setStyleSheet("background-color: white") 
        button_compile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
        button_compile.clicked.connect(self.compile_flowchart) 

        layout1.addWidget(self.compilation_output_label)
        layout1.addWidget(button_compile)
        
        right_widget_container = QWidget()
        right_widget_container.setLayout(layout1)

        main_layout.addLayout(layout) 
        main_layout.addWidget(right_widget_container) 

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def add_shape_action(self, toolbar, name, shape_type):
        action = QAction(name, self)
        action.triggered.connect(lambda: self.scene.set_shape_type(shape_type))
        toolbar.addAction(action)

    def toggle_default_mode(self):
        self.scene.set_shape_type(None) 
        self.scene.set_connection_mode(False) 
        self.scene.set_text_mode(False) 
        self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_connection_mode(self):
        current_mode = self.scene.connection_mode
        self.scene.set_connection_mode(not current_mode) 
        
        if self.scene.connection_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_text_mode(self):
        current_mode = self.scene.text_mode
        self.scene.set_text_mode(not current_mode)

        if self.scene.text_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
    def delete_shape(self):
        selected_items = self.scene.selectedItems()
        if selected_items:
            reply = QMessageBox.question(self, "Confirmar Eliminación",
                                         f"¿Eliminar {len(selected_items)} figura(s) seleccionada(s)?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

            for item in list(selected_items): 
                if isinstance(item, FlowShape):
                    self.scene.connections.remove_connections_with(item) 
                    self.scene.removeItem(item) 
                else: 
                    self.scene.removeItem(item)
        else:
            QMessageBox.warning(self, "Advertencia", "No hay figuras seleccionadas para eliminar.")


    def analisis_connections(self, initial_node):
        final_flow_steps = []
        visited_nodes_ids = set()
        processing_queue = deque()
        if self.scene.start_node and initial_node == self.scene.start_node:
            processing_queue.append(self.scene.start_node)
        else:
            processing_queue.append(initial_node)
        
        while processing_queue:
            current_node_for_bfs = processing_queue.popleft()
            if current_node_for_bfs.id in visited_nodes_ids:
                continue
            visited_nodes_ids.add(current_node_for_bfs.id)
            final_flow_steps.append(current_node_for_bfs)
            
            conn_node = self.scene.connections.head
            while conn_node:
                if conn_node.from_item == current_node_for_bfs:
                    next_node_in_flow = conn_node.to_item
                    if next_node_in_flow.id not in visited_nodes_ids:
                        processing_queue.append(next_node_in_flow)
                conn_node = conn_node.next
        
        if not final_flow_steps:
             self.compilation_output_label.setText("El nodo de inicio no tiene conexiones salientes o no se pudo procesar el flujo.")
             return

        return final_flow_steps
    
    def compile_flowchart(self): 
        try:
            if not self.scene.start_node:
                self.compilation_output_label.setText("Error: No se ha definido un nodo de inicio.\n"
                                                    "Añada una figura 'Inicio/Fin'.")
                QMessageBox.warning(self, "Error de Compilación", "No se ha definido un nodo de inicio.")
                return
            final_flow_steps = []
            #Diccionario el cual contiene las funciones
            #Ejamplo de como se guardan: {"Nombre de la funcion": [Nodo1, nodo2, nodo3]}
            diccionary_functions = {}
            
            for item in self.scene.items():
                if isinstance(item, QGraphicsLineItem):
                    pass
                elif isinstance(item, FlowShape):
                    for function in diccionary_functions:
                        if item.text.strip() == function: 
                            QMessageBox.warning(self, "Error de sintaxis", "Se detectaron dos funciones con el mismo nombre")
                            break

                    if item.shape_type == "start_end" and item.text == "inicio":
                            final_flow_steps = self.analisis_connections(item)
                            diccionary_functions[item.text.strip()] = final_flow_steps

                    elif item.shape_type == "start_end":
                            final_flow_steps = self.analisis_connections(item)
                            diccionary_functions[item.text.strip()] = final_flow_steps

            output_text = "Orden de Ejecución Detectado:\n"
            for i, function in enumerate(diccionary_functions):
                keys = list(diccionary_functions.keys())
                output_text += f"\nNodos de la funcion: {keys[i]}\n"
                for j, node in enumerate(diccionary_functions[function]):
                    node_text = f"Nodo: {node.text.strip() if node.text.strip() else node.shape_type}"
                    output_text += f"{j+1}. {node_text} (Tipo: {node.shape_type} (dir: {node}) (id: {id(node)}))\n"

            self.compilation_output_label.setText(output_text)

            diccionary_functions['conn'] = self.scene.connections

            parser = Parser(diccionary_functions)
            codigo_c = parser.generate_code()

            print(codigo_c)
        except Exception as e:
            self.compilation_output_label.setText(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error de Compilación", str(e))

        