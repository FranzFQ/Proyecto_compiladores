import sys
from analizador import tokenize
from main_parser import Parseador
import subprocess
import uuid
from collections import deque

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QToolBar, QVBoxLayout, QWidget, QInputDialog, QLineEdit,
    QMessageBox, QHBoxLayout, QLabel, QSizePolicy, QPushButton, QTextEdit
)
from PyQt6.QtGui import (
    QPolygonF, QPen, QColor, QAction, QPainter, QCursor, QTextOption, QFontMetrics, QFont
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QProcess, QRect


# Assuming 'parser.py' exists and has a class Parser
try:
    from parser import Parser
except ImportError:
    class Parser:
        def __init__(self, data):
            self.data = data
        def generate_code(self):
            return "¡Hola desde el generador de código de ejemplo! (parser.py no encontrado o sin implementar)"
    print("Advertencia: No se encontró el módulo 'parser.py' o la clase 'Parser'. Usando un parser de ejemplo.")


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
            from_text = current.from_item.text if current.from_item.text else current.from_item.shape_type
            to_text = current.to_item.text if current.to_item.text else current.to_item.shape_type
            print(f"'{from_text}' ({current.from_item.id}) → '{to_text}' ({current.to_item.id})")
            current = current.next

    def remove_connections_with(self, item_to_remove):
        current = self.head
        prev = None
        while current:
            # Check if either the 'from' or 'to' item is the one being removed
            if current.from_item == item_to_remove or current.to_item == item_to_remove:
                # Remove the line item from the scene if it's still there
                if current.line_item.scene():
                    current.line_item.scene().removeItem(current.line_item)

                # Adjust the linked list pointers
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next

                # Move to the next node, as the current one is being deleted
                removed_node = current
                current = current.next
                del removed_node # Explicitly delete the node object
                continue # Skip prev update for this iteration

            prev = current
            current = current.next

    def update_connections_for_item(self, item):
        current = self.head
        while current:
            # Only update if the item is part of the connection
            if current.from_item == item or current.to_item == item:
                # Ensure items are still in the scene before trying to get their center
                if current.from_item.scene() and current.to_item.scene():
                    start_pos = current.from_item.center()
                    end_pos = current.to_item.center()
                    current.line_item.setLine(QLineF(start_pos, end_pos))
                else:
                    # If one of the connected items is no longer in the scene,
                    # the connection itself should likely be removed.
                    # This scenario should be handled by remove_connections_with
                    # when an item is explicitly deleted.
                    pass
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
        self._text = ""
        self.padding = 10
        self.set_min_size(100, 60)

        self.font = QFont()
        self.font.setPointSize(10)


    def set_min_size(self, width, height):
        self.min_width = width
        self.min_height = height

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        if self._text != new_text:
            self._text = new_text
            self.prepareGeometryChange()
            self.update()

    def calculate_text_rect(self):
        font_metrics = QFontMetrics(self.font)
        max_text_width = self.min_width - 2 * self.padding
        if max_text_width <= 0:
            max_text_width = 1

        text_bounding_rect = font_metrics.boundingRect(
            QRect(0, 0, max_text_width, 0),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.text
        )
        return text_bounding_rect.size()


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
            # Convertir a enteros explícitamente
            x = int(current_rect.center().x() - diameter / 2)
            y = int(current_rect.center().y() - diameter / 2)
            w = int(diameter)
            h = int(diameter)
            painter.drawEllipse(x, y, w, h)
            
        elif self.shape_type == 'function_call':
            painter.drawRect(current_rect)
            painter.drawLine(int(current_rect.left() + self.padding/2), int(current_rect.top()), int(current_rect.left() + self.padding/2), int(current_rect.bottom()))
            painter.drawLine(int(current_rect.right() - self.padding/2), int(current_rect.top()), int(current_rect.right() - self.padding/2), int(current_rect.bottom()))


        if self.text:
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(self.font)
            text_rect = current_rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
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
        self.temp_line = None

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
                    if self.temp_line:
                        if self.temp_line.scene():
                            self.removeItem(self.temp_line)
                            self.temp_line = None
            else:
                if self.first_item:
                    self.first_item.set_as_start_connector(False)
                    self.first_item = None
                if self.temp_line:
                    if self.temp_line.scene():
                        self.removeItem(self.temp_line)
                    self.temp_line = None
            return

        elif self.text_mode:
            if isinstance(item_at_click, FlowShape):
                if item_at_click.shape_type == 'process':
                    text, ok = QInputDialog.getMultiLineText(
                        self.views()[0],
                        "Agregar/Editar Texto de Proceso",
                        "Ingrese el texto para el proceso (acepta saltos de línea):",
                        item_at_click.text
                    )
                    if ok:
                        item_at_click.text = text
                else:
                    # Corrección aquí: Usar QLineEdit.EchoMode.Normal
                    text, ok = QInputDialog.getText(
                        self.views()[0],
                        "Agregar/Editar Texto",
                        f"Ingrese el texto para la figura '{item_at_click.shape_type}':",
                        QLineEdit.EchoMode.Normal,  # Cambiado de QLineEdit.Normal
                        item_at_click.text
                    )
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
            start_pos = self.first_item.center()
            end_pos = event.scenePos()
            self.temp_line.setLine(QLineF(start_pos, end_pos))
        else:
            super().mouseMoveEvent(event)

    def create_connection(self, from_item, to_item):
        # Ensure a connection is not made to itself
        if from_item == to_item:
            QMessageBox.warning(self.views()[0], "Error de Conexión", "No se puede conectar una figura consigo misma.")
            return

        # Check for existing connections between these two specific items
        # To prevent duplicate lines, you might need to iterate through existing connections.
        # For simplicity, this example allows multiple lines between the same two items.
        # If you need to prevent duplicates, you'd add a loop here:
        # for node in self.connections.get_connections_from(from_item):
        #     if node == to_item:
        #         QMessageBox.information(self.views()[0], "Conexión Existente", "Esta conexión ya existe.")
        #         return

        line = QGraphicsLineItem()
        line.setPen(QPen(Qt.GlobalColor.black, 2))
        self.addItem(line)
        start_pos = from_item.center()
        end_pos = to_item.center()
        line.setLine(QLineF(start_pos, end_pos))
        line.setZValue(-1) # Draw lines behind shapes
        line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False) # Lines are not directly selectable
        self.connections.add_connection(from_item, to_item, line)

    def removeItem(self, item):
        # This method is called by the scene itself, often from delete_shape or when an item is deleted manually.
        # Ensure connections are removed first to avoid dangling pointers or lines.
        if isinstance(item, FlowShape):
            # If the item being removed was the start node, clear the start node reference
            if item == self.start_node:
                self.set_start_node(None)
            self.connections.remove_connections_with(item)

        # Call the superclass method to actually remove the item from the scene
        super().removeItem(item)

    def set_start_node(self, node):
        if self.start_node and self.start_node != node:
            self.start_node.update() # Refresh old start node to remove gold highlight
        self.start_node = node
        if self.start_node:
            self.start_node.update() # Refresh new start node to apply gold highlight


    def analisis_connections(self, initial_node):
        final_flow_steps = []
        visited_nodes_ids = set()
        processing_queue = deque()
        if self.start_node and initial_node == self.start_node:
            processing_queue.append(self.start_node)
        else:
            # If initial_node is not explicitly the start_node, but we're analyzing a function,
            # we should still start from that initial_node.
            processing_queue.append(initial_node)

        while processing_queue:
            current_node_for_bfs = processing_queue.popleft()
            if current_node_for_bfs.id in visited_nodes_ids:
                continue
            visited_nodes_ids.add(current_node_for_bfs.id)
            final_flow_steps.append(current_node_for_bfs)

            outgoing_connections = self.connections.get_connections_from(current_node_for_bfs)
            for next_node_in_flow in outgoing_connections:
                if next_node_in_flow.id not in visited_nodes_ids:
                    processing_queue.append(next_node_in_flow)

        if not final_flow_steps:
             # This message should probably be handled by the caller (compile_flowchart)
             # as this function is for analysis, not direct UI update.
             return None

        return final_flow_steps

    def compile_flowchart(self):
        if not self.start_node:
            self.compilation_output_label.setText("Error: No se ha definido un nodo de inicio.\n"
                                                 "Añada una figura 'Inicio/Fin'.")
            QMessageBox.warning(self, "Error de Compilación", "No se ha definido un nodo de inicio.")
            return

        diccionary_functions = {}
        all_start_end_nodes = [item for item in self.scene.items() if isinstance(item, FlowShape) and item.shape_type == "start_end"]

        function_names = set()
        for item in all_start_end_nodes:
            if item.text.strip():
                if item.text.strip() in function_names:
                    QMessageBox.warning(self, "Error de sintaxis", f"Se detectaron dos funciones con el mismo nombre: '{item.text.strip()}'")
                    self.compilation_output_label.setText(f"Error de sintaxis: Función duplicada '{item.text.strip()}'")
                    return
                function_names.add(item.text.strip())

        main_start_node_found = False
        for item in all_start_end_nodes:
            if item.text.strip().lower() == "inicio":
                main_start_node_found = True
                flow_for_func = self.analisis_connections(item)
                if flow_for_func is not None:
                    diccionary_functions[item.text.strip()] = flow_for_func
                else:
                    self.compilation_output_label.setText("El nodo 'inicio' no tiene conexiones salientes o no se pudo procesar su flujo.")
                    return
                break

        if not main_start_node_found:
            self.compilation_output_label.setText("Advertencia: No se encontró un nodo 'Inicio'. Se compilarán otras funciones si existen.")
            pass

        for item in all_start_end_nodes:
            if item.text.strip() and item.text.strip().lower() != "inicio":
                flow_for_func = self.analisis_connections(item)
                if flow_for_func is not None:
                    diccionary_functions[item.text.strip()] = flow_for_func


        output_text = "Orden de Ejecución Detectado:\n"
        if not diccionary_functions:
            output_text += "No se detectaron funciones o el nodo 'inicio' no tiene texto 'inicio' y no hay otras funciones definidas.\n"
        else:
            for function_name in diccionary_functions:
                output_text += f"\nNodos de la funcion: '{function_name}'\n"
                for j, node in enumerate(diccionary_functions[function_name]):
                    node_text = f"Nodo: {node.text.strip() if node.text.strip() else node.shape_type}"
                    output_text += f"{j+1}. {node_text} (Tipo: {node.shape_type})\n"

        self.compilation_output_label.setText(output_text)

        parser_data = {'connections': self.scene.connections}
        parser_data['functions_flow'] = diccionary_functions

        parser = Parser(parser_data)
        codigo_c = parser.generate_code()

        print("\n--- Código C Generado ---")
        print(codigo_c)


class WslTerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: black; color: green; font-family: 'Consolas', 'DejaVu Sans Mono', monospace;")
        layout.addWidget(self.output_area)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Escribe un comando y presiona Enter (ej: ls -la, pwd, echo 'Hola WSL')")
        self.input_line.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.input_line)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.handle_finished)

        self.input_line.returnPressed.connect(self.send_command)

        try:
            self.process.start("wsl.exe")
            self.output_area.append("--- Iniciando Terminal WSL/Ubuntu ---")
        except Exception as e:
            self.output_area.append(f"ERROR: No se pudo iniciar WSL. Asegúrate de que 'wsl.exe' esté en tu PATH y WSL esté instalado. {e}")
            self.input_line.setEnabled(False)

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


class FlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Diagramas de Flujo")
        self.setStyleSheet("background-color: gray")

        self.scene = FlowScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setFixedSize(1000, 800) # Setting a fixed size for the view

        toolbar = QToolBar("Formas")
        self.addToolBar(toolbar)

        self.add_shape_action(toolbar, "Inicio/Fin", 'start_end')
        self.add_shape_action(toolbar, "Proceso", 'process')
        self.add_shape_action(toolbar, "Decisión", 'decision')
        self.add_shape_action(toolbar, "Entrada/Salida", 'input_output')
        self.add_shape_action(toolbar, "Conector", 'connector')
        self.add_shape_action(toolbar, "Llamada a Función", 'function_call')
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
        self.delete_action.triggered.connect(self.delete_shape)
        toolbar.addAction(self.delete_action)

        toolbar.addSeparator()

        main_layout = QHBoxLayout()

        flowchart_layout = QVBoxLayout()
        flowchart_layout.addWidget(self.view)
        main_layout.addLayout(flowchart_layout, 3)

        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(0,0,0,0)

        compilation_section_widget = QWidget()
        compilation_layout = QVBoxLayout(compilation_section_widget)
        compilation_layout.setContentsMargins(5,5,5,5)
        self.compilation_output_label = QLabel("Presione 'Compilar' para ver el flujo.")
        self.compilation_output_label.setStyleSheet("background-color: white; border: 1px solid black; padding: 5px;")
        self.compilation_output_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.compilation_output_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.compilation_output_label.setWordWrap(True)
        compilation_layout.addWidget(self.compilation_output_label)

        button_compile = QPushButton("Compilar")
        button_compile.setStyleSheet("background-color: white")
        button_compile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button_compile.clicked.connect(self.compile_flowchart)
        compilation_layout.addWidget(button_compile)
        right_panel_layout.addWidget(compilation_section_widget, 1)

        self.wsl_terminal_widget = WslTerminalWidget()
        right_panel_layout.addWidget(self.wsl_terminal_widget, 2)

        main_layout.addLayout(right_panel_layout, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setMinimumSize(self.sizeHint())


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

            for item in list(selected_items): # Iterate over a copy to avoid modification during iteration
                if isinstance(item, FlowShape):
                    # removeItem handles connection cleanup, so no need to call connections.remove_connections_with here
                    self.scene.removeItem(item)
                # If it's not a FlowShape (e.g., a line if lines were selectable), remove it too.
                # However, lines are not selectable here, so this primarily targets FlowShapes.
                elif isinstance(item, QGraphicsLineItem):
                    self.scene.removeItem(item) # This should not typically happen if lines are not selectable
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

            outgoing_connections = self.scene.connections.get_connections_from(current_node_for_bfs)
            for next_node_in_flow in outgoing_connections:
                if next_node_in_flow.id not in visited_nodes_ids:
                    processing_queue.append(next_node_in_flow)

        if not final_flow_steps:
             self.compilation_output_label.setText("El nodo de inicio no tiene conexiones salientes o no se pudo procesar el flujo.")
             return None

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


            diccionary_functions['conn'] = self.scene.connections

            parser = Parser(diccionary_functions)
            codigo_c = parser.generate_code()
            print(codigo_c)
            token = tokenize(codigo_c)
            self.compilation_output_label.setText(codigo_c)

            print("Iniciando análisis sintáctico...")
            parseador = Parseador(token)
            arbol_ast = parseador.parsear()

            try:            
                codigo_asm = arbol_ast.generar_codigo()
                
                with open("programa.asm", "w") as archivo:
                    archivo.write(codigo_asm)

                subprocess.run(["nasm", "-f", "elf32", "programa.asm", "-o", "programa.o"])
                subprocess.run(["ld", "-m", "elf_i386", "-o", "programa", "programa.o"])
                subprocess.run(["./programa"])
            except Exception as e:
                print(f"Error al generar el código ensamblador: {e}")

        except Exception as e:
            self.compilation_output_label.setText(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error de Compilación", str(e))
