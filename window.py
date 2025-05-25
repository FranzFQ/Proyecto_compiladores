import sys
import math
import uuid
from collections import deque
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QGraphicsPolygonItem, QToolBar, QVBoxLayout, QWidget, 
    QInputDialog, QLineEdit, QMessageBox, QHBoxLayout, QLabel, QSizePolicy, 
    QPushButton, QTextEdit
)
from PyQt6.QtGui import (
    QPolygonF, QPen, QColor, QAction, QPainter, QCursor, QFont, QBrush, QFontMetrics
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QRect, QProcess

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

    def create_connection(self, from_item, to_item, scene):
        try:
            # Verificar que los ítems existen y están en la escena
            if not from_item or not to_item or from_item == to_item:
                return None

            # Calcular puntos de inicio y fin
            from_center = from_item.center()
            to_center = to_item.center()
            
            # Verificar que los puntos son válidos
            if not from_center or not to_center:
                return None
                
            start_pos = from_item.edge_point(to_center)
            end_pos = to_item.edge_point(from_center)
            
            # Crear la línea principal
            line = QGraphicsLineItem()
            pen = QPen(QColor("#555555"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            line.setPen(pen)
            line.setLine(QLineF(start_pos, end_pos))
            
            # Crear flecha solo si la línea tiene longitud suficiente
            if QLineF(start_pos, end_pos).length() > 5:
                arrow_size = 10
                angle = math.atan2(end_pos.y() - start_pos.y(), end_pos.x() - start_pos.x())
                
                # Ajustar el punto final para que la flecha no se superponga
                adjusted_end = end_pos - QPointF(math.cos(angle) * 2, math.sin(angle) * 2)
                
                arrow_p1 = adjusted_end - QPointF(
                    math.cos(angle - math.pi/6) * arrow_size,
                    math.sin(angle - math.pi/6) * arrow_size
                )
                arrow_p2 = adjusted_end - QPointF(
                    math.cos(angle + math.pi/6) * arrow_size,
                    math.sin(angle + math.pi/6) * arrow_size
                )
                
                arrow_head = QPolygonF()
                arrow_head.append(adjusted_end)
                arrow_head.append(arrow_p1)
                arrow_head.append(arrow_p2)
                
                arrow = QGraphicsPolygonItem(arrow_head)
                arrow.setBrush(QColor("#555555"))
                arrow.setPen(QPen(Qt.GlobalColor.transparent))
                
                scene.addItem(arrow)
                self.add_connection(from_item, to_item, (line, arrow))
            else:
                self.add_connection(from_item, to_item, (line, None))
            
            scene.addItem(line)
            return line
            
        except Exception as e:
            print(f"Error al crear conexión: {str(e)}")
            return None

    def remove_connections_with(self, item_to_remove):
        current = self.head
        prev = None
        while current:
            if current.from_item == item_to_remove or current.to_item == item_to_remove:
                # Eliminar los elementos gráficos de la escena
                if isinstance(current.line_item, tuple):
                    for item in current.line_item:
                        if item and item.scene():
                            item.scene().removeItem(item)
                elif current.line_item and current.line_item.scene():
                    current.line_item.scene().removeItem(current.line_item)

                # Eliminar el nodo de la lista
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
            try:
                if current.from_item == item or current.to_item == item:
                    if current.from_item.scene() and current.to_item.scene():
                        # Calcular nuevos puntos
                        from_center = current.from_item.center()
                        to_center = current.to_item.center()
                        
                        start_pos = current.from_item.edge_point(to_center)
                        end_pos = current.to_item.edge_point(from_center)
                        
                        # Actualizar línea
                        if isinstance(current.line_item, tuple) and current.line_item[0]:
                            current.line_item[0].setLine(QLineF(start_pos, end_pos))
                            
                            # Actualizar flecha si existe
                            if current.line_item[1] and QLineF(start_pos, end_pos).length() > 5:
                                arrow_size = 10
                                angle = math.atan2(end_pos.y() - start_pos.y(), 
                                                end_pos.x() - start_pos.x())
                                
                                adjusted_end = end_pos - QPointF(math.cos(angle) * 2, math.sin(angle) * 2)
                                
                                arrow_p1 = adjusted_end - QPointF(
                                    math.cos(angle - math.pi/6) * arrow_size,
                                    math.sin(angle - math.pi/6) * arrow_size
                                )
                                arrow_p2 = adjusted_end - QPointF(
                                    math.cos(angle + math.pi/6) * arrow_size,
                                    math.sin(angle + math.pi/6) * arrow_size
                                )
                                
                                arrow_head = QPolygonF()
                                arrow_head.append(adjusted_end)
                                arrow_head.append(arrow_p1)
                                arrow_head.append(arrow_p2)
                                
                                current.line_item[1].setPolygon(arrow_head)
            except Exception as e:
                print(f"Error al actualizar conexión: {str(e)}")
                
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
    def __init__(self, shape_type, parent=None):
        super().__init__(parent)
        self.shape_type = shape_type
        self.id = str(uuid.uuid4())
        self._text = ""
        self._highlight_color = None
        self._is_start_connector = False
        self.padding = 10
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                     QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                     QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Tamaño mínimo inicial
        self.min_width = 100
        self.min_height = 60
        
        # Fuente para el texto
        self.font = QFont()
        self.font.setPointSize(10)

    def boundingRect(self):
        rect = QRectF(0, 0, self.min_width, self.min_height)
        if self.text:
            text_size = self.calculate_text_rect()
            new_width = max(self.min_width, text_size.width() + 2 * self.padding)
            new_height = max(self.min_height, text_size.height() + 2 * self.padding)
            rect = QRectF(0, 0, new_width, new_height)
        return rect.normalized()

    def paint(self, painter: QPainter, option, widget):
        pen = QPen(Qt.GlobalColor.black, 2)
        if self.isSelected():
            pen = QPen(Qt.GlobalColor.blue, 3)
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
        elif self.shape_type == 'function_call': brush_color = QColor('pink')

        painter.setBrush(QColor(brush_color))

        current_rect = self.boundingRect()

        if self.shape_type == 'start_end':
            painter.drawEllipse(current_rect)
        elif self.shape_type == 'process':
            painter.drawRect(current_rect)
        elif self.shape_type == 'decision':
            points = [
                QPointF(current_rect.width() / 2, 0),
                QPointF(current_rect.width(), current_rect.height() / 2),
                QPointF(current_rect.width() / 2, current_rect.height()),
                QPointF(0, current_rect.height() / 2)
            ]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'input_output':
            slant = current_rect.width() * 0.2
            points = [
                QPointF(slant, 0),
                QPointF(current_rect.width(), 0),
                QPointF(current_rect.width() - slant, current_rect.height()),
                QPointF(0, current_rect.height())
            ]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == 'connector':
            diameter = min(current_rect.width(), current_rect.height()) - self.padding
            # Usando QRectF para el círculo
            ellipse_rect = QRectF(
                current_rect.center().x() - diameter / 2,
                current_rect.center().y() - diameter / 2,
                diameter,
                diameter
            )
            painter.drawEllipse(ellipse_rect)
        elif self.shape_type == 'function_call':
            painter.drawRect(current_rect)
            painter.drawLine(
                int(current_rect.left() + self.padding/2), 
                int(current_rect.top()), 
                int(current_rect.left() + self.padding/2), 
                int(current_rect.bottom())
            )
            painter.drawLine(
                int(current_rect.right() - self.padding/2), 
                int(current_rect.top()), 
                int(current_rect.right() - self.padding/2), 
                int(current_rect.bottom())
            )

        if self.text:
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(self.font)
            text_rect = current_rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)
            
    def calculate_text_rect(self):
        font_metrics = QFontMetrics(self.font)
        max_text_width = self.min_width - 2 * self.padding
        text_bounding_rect = font_metrics.boundingRect(
            QRect(0, 0, max_text_width, 0),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.text
        )
        return text_bounding_rect.size()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.update()

    def set_min_size(self, width, height):
        self.min_width = width
        self.min_height = height
        self.update()

    def set_as_start_connector(self, is_start):
        self._is_start_connector = is_start
        self.update()

    def highlight(self, color):
        self._highlight_color = color
        self.update()

    def center(self):
        return self.scenePos() + QPointF(self.boundingRect().width() / 2,
                                        self.boundingRect().height() / 2)
    
    def edge_point(self, target_center):
        """Calcula el punto en el borde más cercano al punto objetivo"""
        center_pos = self.center()
        rect = self.boundingRect()
        rect.moveTo(self.scenePos())
        
        # Vector desde el centro al objetivo
        direction = target_center - center_pos
        if direction.x() == 0 and direction.y() == 0:
            return center_pos  # Si es el mismo punto
        
        # Normalizar el vector
        length = (direction.x()**2 + direction.y()**2)**0.5
        if length == 0:
            return center_pos
        
        direction = direction / length
        
        # Manejar formas especiales primero
        if self.shape_type in ['start_end', 'connector']:  # Círculos
            radius = min(rect.width(), rect.height()) / 2
            return center_pos + direction * radius
        
        # Para formas rectangulares (proceso, decisión, etc.)
        half_width = rect.width() / 2
        half_height = rect.height() / 2
        
        # Manejar casos donde la dirección es puramente horizontal o vertical
        if direction.x() == 0:  # Movimiento vertical puro
            return center_pos + QPointF(0, half_height if direction.y() > 0 else -half_height)
        
        if direction.y() == 0:  # Movimiento horizontal puro
            return center_pos + QPointF(half_width if direction.x() > 0 else -half_width, 0)
        
        # Calcular intersección con el rectángulo para dirección diagonal
        tx = (half_width if direction.x() > 0 else -half_width) / direction.x()
        ty = (half_height if direction.y() > 0 else -half_height) / direction.y()
        
        t = min(tx, ty)
        return center_pos + direction * t
        
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
        self.temp_line = None
        self.connections = ConnectionList()
        self.start_node = None

    def set_shape_type(self, shape_type):
        self.selected_shape = shape_type
        if shape_type is not None:
            self.set_connection_mode(False)
            self.set_text_mode(False)

    def set_connection_mode(self, enabled):
        self.connection_mode = enabled
        if enabled:
            self.set_shape_type(None)
        else:
            if self.first_item:
                self.first_item.set_as_start_connector(False)
                self.first_item = None
            if self.temp_line:
                if self.temp_line.scene():
                    self.removeItem(self.temp_line)
                self.temp_line = None

    def set_text_mode(self, enabled):
        self.text_mode = enabled
        if enabled:
            self.set_shape_type(None)
            self.set_connection_mode(False)

    def mousePressEvent(self, event):
        item_at_click = self.itemAt(event.scenePos(), self.views()[0].transform())

        if self.selected_shape:
            # Crear nueva forma
            shape = FlowShape(self.selected_shape)
            shape.setPos(event.scenePos())
            self.addItem(shape)
            if shape.shape_type == 'start_end' and not self.start_node:
                self.set_start_node(shape)
            return

        elif self.connection_mode:
            if isinstance(item_at_click, FlowShape):
                if self.first_item is None:
                    # Validar si es un punto de salida válido (para decisiones)
                    if item_at_click.shape_type == 'decision':
                        click_pos = item_at_click.mapFromScene(event.scenePos())
                        rect = item_at_click.boundingRect()
                        
                        # Solo permitir comenzar conexiones desde derecha o abajo
                        if not (click_pos.x() >= rect.right() - 10 or click_pos.y() >= rect.bottom() - 10):
                            QMessageBox.warning(self.views()[0], "Error", 
                                            "En decisiones, las conexiones salientes deben comenzar desde la derecha o abajo")
                            return
                    
                    self.first_item = item_at_click
                    self.first_item.set_as_start_connector(True)
                else:
                    # Validar si es un punto de entrada válido (para decisiones)
                    if item_at_click.shape_type == 'decision':
                        click_pos = item_at_click.mapFromScene(event.scenePos())
                        rect = item_at_click.boundingRect()
                        
                        # Solo permitir conexiones entrantes por izquierda o arriba
                        if not (click_pos.x() <= rect.left() + 10 or click_pos.y() <= rect.top() + 10):
                            QMessageBox.warning(self.views()[0], "Error",
                                            "En decisiones, las conexiones entrantes deben llegar por arriba o izquierda")
                            self.first_item.set_as_start_connector(False)
                            self.first_item = None
                            return
                    
                    # Crear la conexión
                    self.connections.create_connection(self.first_item, item_at_click, self)
                    self.first_item.set_as_start_connector(False)
                    self.first_item = None
            return

        elif self.text_mode:
            if isinstance(item_at_click, FlowShape):
                if item_at_click.shape_type == 'process':
                    text, ok = QInputDialog.getMultiLineText(
                        self.views()[0], "Editar Texto",
                        "Ingrese el texto:", item_at_click.text)
                else:
                    text, ok = QInputDialog.getText(
                        self.views()[0], "Editar Texto",
                        "Ingrese el texto:", QLineEdit.EchoMode.Normal, item_at_click.text)
                
                if ok:
                    item_at_click.text = text
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.connection_mode and self.first_item:
            if not self.temp_line:
                self.temp_line = QGraphicsLineItem()
                self.temp_line.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
                self.addItem(self.temp_line)
            
            # Cambiar esta línea:
            # start_pos = self.first_item.get_connection_point(event.scenePos(), is_input=False)
            # Por esta:
            start_pos = self.first_item.edge_point(event.scenePos())
            
            self.temp_line.setLine(QLineF(start_pos, event.scenePos()))
        else:
            super().mouseMoveEvent(event)

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
        self.setStyleSheet("background-color: #CEE9F5")

        self.scene = FlowScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setFixedSize(1000, 800)

        # Crear barra de herramientas
        toolbar = QToolBar("Formas")
        self.addToolBar(toolbar)

        # Añadir formas
        shapes = [
            ("Inicio/Fin", 'start_end'),
            ("Proceso", 'process'),
            ("Decisión", 'decision'),
            ("Entrada/Salida", 'input_output'),
            ("Conector", 'connector'),
            ("Llamada a Función", 'function_call')
        ]

        for name, shape_type in shapes:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, st=shape_type: self.scene.set_shape_type(st))
            toolbar.addAction(action)

        toolbar.addSeparator()

        # Añadir herramientas
        self.select_action = QAction("Seleccionar/Mover", self)
        self.select_action.triggered.connect(self.toggle_default_mode)
        toolbar.addAction(self.select_action)

        self.connect_action = QAction("Conectar", self)
        self.connect_action.triggered.connect(self.toggle_connection_mode)
        toolbar.addAction(self.connect_action)

        self.text_action = QAction("Texto", self)
        self.text_action.triggered.connect(self.toggle_text_mode)
        toolbar.addAction(self.text_action)

        self.delete_action = QAction("Eliminar", self)
        self.delete_action.triggered.connect(self.delete_shape)
        toolbar.addAction(self.delete_action)

        # Configurar layout principal
        main_layout = QHBoxLayout()
        right_panel = QVBoxLayout()
        
        # Área de compilación
        self.compilation_output = QTextEdit()
        self.compilation_output.setReadOnly(True)
        right_panel.addWidget(QLabel("Salida de Compilación:"))
        right_panel.addWidget(self.compilation_output)

        # Botón de compilación
        compile_btn = QPushButton("Compilar Diagrama")
        compile_btn.clicked.connect(self.compile_flowchart)
        right_panel.addWidget(compile_btn)

        # Agregar la terminal WSL
        self.wsl_terminal = WslTerminalWidget()
        right_panel.addWidget(self.wsl_terminal)

        main_layout.addWidget(self.view, 3)
        main_layout.addLayout(right_panel, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def toggle_default_mode(self):
        self.scene.set_shape_type(None)
        self.scene.set_connection_mode(False)
        self.scene.set_text_mode(False)
        self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_connection_mode(self):
        self.scene.set_connection_mode(not self.scene.connection_mode)
        if self.scene.connection_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_text_mode(self):
        self.scene.set_text_mode(not self.scene.text_mode)
        if self.scene.text_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def delete_shape(self):
        selected_items = self.scene.selectedItems()
        if selected_items:
            reply = QMessageBox.question(self, "Confirmar",
                                    f"¿Eliminar {len(selected_items)} figura(s)?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for item in selected_items:
                    # Eliminar todas las conexiones asociadas a este ítem
                    self.scene.connections.remove_connections_with(item)
                    # Eliminar el ítem de la escena
                    self.scene.removeItem(item)
                    
                    # Si era el nodo de inicio, limpiar la referencia
                    if hasattr(self.scene, 'start_node') and self.scene.start_node == item:
                        self.scene.start_node = None

    def compile_flowchart(self):
        if not self.scene.start_node:
            QMessageBox.warning(self, "Error", "No se ha definido un nodo de inicio")
            return
        
        # Aquí iría la lógica de compilación
        self.compilation_output.setText("Diagrama compilado correctamente")

class WslTerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Área de salida
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: black; color: green; font-family: 'Consolas', 'DejaVu Sans Mono', monospace;")
        layout.addWidget(self.output_area)

        # Botones para ensamblador
        asm_buttons_layout = QHBoxLayout()
        
        self.compile_button = QPushButton("Compilar (NASM)")
        self.compile_button.setStyleSheet("background-color: #333; color: white;")
        self.compile_button.clicked.connect(self.compile_asm)
        asm_buttons_layout.addWidget(self.compile_button)
        
        self.link_button = QPushButton("Enlazar (LD)")
        self.link_button.setStyleSheet("background-color: #333; color: white;")
        self.link_button.clicked.connect(self.link_asm)
        asm_buttons_layout.addWidget(self.link_button)
        
        self.run_button = QPushButton("Ejecutar programa")
        self.run_button.setStyleSheet("background-color: #333; color: white;")
        self.run_button.clicked.connect(self.run_program)
        asm_buttons_layout.addWidget(self.run_button)

        # Botón para limpiar la salida
        self.clear_button = QPushButton("Limpiar salida")
        self.clear_button.setStyleSheet("background-color: #333; color: white;")
        self.clear_button.clicked.connect(lambda: self.output_area.clear())
        asm_buttons_layout.addWidget(self.clear_button)

        
        layout.addLayout(asm_buttons_layout)

        # Línea de entrada para comandos tradicionales
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Ingresa lo solicitado...")
        self.input_line.setStyleSheet("background-color: white; color: gray;")
        layout.addWidget(self.input_line)

        # Proceso WSL
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.handle_finished)
        # Cambiar color
        self.output_area.setStyleSheet("background-color: black; color: green; font-family: 'Consolas', 'DejaVu Sans Mono', monospace;")

        self.input_line.returnPressed.connect(self.send_command)

        try:
            self.process.start("wsl.exe")
            self.output_area.append("--- Iniciando Terminal WSL/Ubuntu ---")
            self.output_area.append("Usa los botones para compilar y ejecutar código ensamblador")
        except Exception as e:
            self.output_area.append(f"ERROR: No se pudo iniciar WSL. Asegúrate de que 'wsl.exe' esté en tu PATH y WSL esté instalado. {e}")
            self.input_line.setEnabled(False)
            for btn in [self.compile_button, self.link_button, self.run_button]:
                btn.setEnabled(False)

    def compile_asm(self):
        self.output_area.append("> Compilando programa.asm con NASM...")
        command = "nasm -f elf32 programa.asm -o programa.o"
        self.process.write((command + '\n').encode('utf-8'))

    def link_asm(self):
        self.output_area.append("> Enlazando programa.o con LD...")
        command = "ld -m elf_i386 -o programa programa.o"
        self.process.write((command + '\n').encode('utf-8'))

    def run_program(self):
        self.output_area.append("> Ejecutando programa...")
        command = "./programa"
        self.process.write((command + '\n').encode('utf-8'))

    def read_stdout(self):
        data_bytes = self.process.readAllStandardOutput().data()
        data_str = data_bytes.decode('utf-8', errors='ignore')
        self.output_area.append(data_str.strip())
        self.output_area.verticalScrollBar().setValue(self.output_area.verticalScrollBar().maximum())

    def read_stderr(self):
        data_bytes = self.process.readAllStandardError().data()
        data_str = data_bytes.decode('utf-8', errors='ignore')
        self.output_area.append(f"<span style='color:red;'>ERROR: {data_str.strip()}</span>")
        self.output_area.verticalScrollBar().setValue(self.output_area.verticalScrollBar().maximum())

    def send_command(self):
        command = self.input_line.text()
        if command:
            self.output_area.append(f"<span style='color:lightblue;'>$ {command}</span>")
            self.process.write((command + '\n').encode('utf-8'))
            self.input_line.clear()

    def handle_finished(self, exitCode, exitStatus):
        self.output_area.append(f"--- Terminal WSL terminada con código {exitCode} y estado {exitStatus} ---")
        self.input_line.setEnabled(False)
        for btn in [self.compile_button, self.link_button, self.run_button]:
            btn.setEnabled(False)