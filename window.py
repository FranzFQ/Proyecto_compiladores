import sys
from analizador import tokenize
from main_parser import Parseador
import subprocess
import uuid
from collections import deque
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QToolBar, QVBoxLayout, QWidget, QInputDialog, QLineEdit,
    QMessageBox, QHBoxLayout, QLabel, QSizePolicy, QPushButton, QTextEdit, QGraphicsPolygonItem
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
        # Validar conexiones para objetos de decisión
        if from_item.shape_type == 'decision' and to_item.shape_type == 'decision':
            QMessageBox.warning(None, "Error", "No se puede conectar dos decisiones directamente")
            return None

        # Obtener puntos de conexión específicos
        start_pos = from_item.get_connection_point(to_item.center(), is_input=False)
        end_pos = to_item.get_connection_point(from_item.center(), is_input=True)

        # Crear la línea
        line = QGraphicsLineItem(QLineF(start_pos, end_pos))
        line.setPen(QPen(Qt.GlobalColor.black, 2))
        scene.addItem(line)

        # Crear flecha
        arrow_size = 10
        angle = math.atan2(end_pos.y() - start_pos.y(), end_pos.x() - start_pos.x())
        
        arrow_p1 = end_pos - QPointF(math.cos(angle - math.pi/6) * arrow_size,
                                    math.sin(angle - math.pi/6) * arrow_size)
        arrow_p2 = end_pos - QPointF(math.cos(angle + math.pi/6) * arrow_size,
                                    math.sin(angle + math.pi/6) * arrow_size)
        
        arrow = QGraphicsPolygonItem(QPolygonF([end_pos, arrow_p1, arrow_p2]))
        arrow.setBrush(Qt.GlobalColor.black)
        scene.addItem(arrow)

        self.add_connection(from_item, to_item, (line, arrow))
        return line

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
                # Remove both line and arrow from scene
                if isinstance(current.line_item, tuple):  # Si es una tupla (línea, flecha)
                    for item in current.line_item:
                        if item.scene():
                            item.scene().removeItem(item)
                else:
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
                if current.from_item.scene() and current.to_item.scene():
                    # Usar puntos de conexión específicos
                    start_pos = current.from_item.get_connection_point(
                        current.to_item.center(), is_input=False)
                    end_pos = current.to_item.get_connection_point(
                        current.from_item.center(), is_input=True)
                    
                    current.line_item[0].setLine(QLineF(start_pos, end_pos))
                    
                    # Actualizar flecha
                    arrow_size = 10
                    angle = math.atan2(end_pos.y() - start_pos.y(), 
                                    end_pos.x() - start_pos.x())
                    
                    arrow_p1 = end_pos - QPointF(
                        math.cos(angle - math.pi/6) * arrow_size,
                        math.sin(angle - math.pi/6) * arrow_size)
                    arrow_p2 = end_pos - QPointF(
                        math.cos(angle + math.pi/6) * arrow_size,
                        math.sin(angle + math.pi/6) * arrow_size)
                    
                    current.line_item[1].setPolygon(QPolygonF([end_pos, arrow_p1, arrow_p2]))
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
    
    def edge_point(self, target_center, is_input=True):
        """Calcula el punto en el borde más cercano al punto objetivo, considerando puntos de conexión específicos"""
        if self.shape_type != 'decision':
            return self._calculate_general_edge_point(target_center)
        
        connection_points = self.get_connection_points(is_input)
        
        # Encontrar el punto más cercano al objetivo
        closest_point = None
        min_distance = float('inf')
        
        for point in connection_points:
            # Convertir a coordenadas de escena
            scene_point = self.mapToScene(point)
            distance = QLineF(scene_point, target_center).length()
            
            if distance < min_distance:
                min_distance = distance
                closest_point = scene_point
        
        return closest_point if closest_point else self.center()

    def _calculate_general_edge_point(self, target_center):
        """Método original para calcular puntos de borde para formas no-decisión"""
        center_pos = self.center()
        rect = self.boundingRect()
        rect.moveTo(self.scenePos())
        
        direction = target_center - center_pos
        if direction.x() == 0 and direction.y() == 0:
            return center_pos
        
        length = (direction.x()**2 + direction.y()**2)**0.5
        if length == 0:
            return center_pos
        
        direction = direction / length
        
        if self.shape_type in ['start_end', 'connector']:
            radius = min(rect.width(), rect.height()) / 2
            return center_pos + direction * radius
        
        half_width = rect.width() / 2
        half_height = rect.height() / 2
        
        if direction.x() == 0:
            return center_pos + QPointF(0, half_height if direction.y() > 0 else -half_height)
        
        if direction.y() == 0:
            return center_pos + QPointF(half_width if direction.x() > 0 else -half_width, 0)
        
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
    
    def get_connection_point(self, target_pos, is_input):
        """Obtiene el punto de conexión específico para decisiones"""
        if self.shape_type != 'decision':
            return self.center()
        
        rect = self.boundingRect()
        center = rect.center()
        local_pos = self.mapFromScene(target_pos)
        
        # Para decisiones
        if is_input:
            # Conexiones entrantes (arriba o izquierda)
            if abs(local_pos.x() - rect.left()) < abs(local_pos.y() - rect.top()):
                return self.mapToScene(QPointF(rect.left(), center.y()))  # Izquierda
            else:
                return self.mapToScene(QPointF(center.x(), rect.top()))   # Arriba
        else:
            # Conexiones salientes (derecha o abajo)
            if abs(local_pos.x() - rect.right()) < abs(local_pos.y() - rect.bottom()):
                return self.mapToScene(QPointF(rect.right(), center.y())) # Derecha
            else:
                return self.mapToScene(QPointF(center.x(), rect.bottom())) # Abajo


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

        if self.connection_mode:
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
                    self.first_item.highlight(QColor("green"))
                
                else:
                    # Validar si es un punto de entrada válido (para decisiones)
                    if item_at_click.shape_type == 'decision':
                        click_pos = item_at_click.mapFromScene(event.scenePos())
                        rect = item_at_click.boundingRect()
                        
                        # Solo permitir conexiones entrantes por izquierda o arriba
                        if not (click_pos.x() <= rect.left() + 10 or click_pos.y() <= rect.top() + 10):
                            QMessageBox.warning(self.views()[0], "Error",
                                            "En decisiones, las conexiones entrantes deben llegar por arriba o izquierda")
                            self.first_item.highlight(None)
                            self.first_item = None
                            return
                    
                    # Crear la conexión
                    self.connections.create_connection(self.first_item, item_at_click, self)
                    self.first_item.highlight(None)
                    self.first_item = None
                    
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


    


class FlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Diagramas de Flujo")
        self.setStyleSheet("background-color: #CEE9F5")

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

        button_compile = QPushButton("Generar código")
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
                
                # Aquí se guardará el código ensamblador en un archivo
                with open("programa.asm", "w") as archivo:
                    archivo.write(codigo_asm)


                # Ahora el codigo se ejecutará en la otra terminal de WSL al presionar los botones
                # subprocess.run(["nasm", "-f", "elf32", "programa.asm", "-o", "programa.o"])
                # subprocess.run(["ld", "-m", "elf_i386", "-o", "programa", "programa.o"])
                # subprocess.run(["./programa"])
            except Exception as e:
                print(f"Error al generar el código ensamblador: {e}")

        except Exception as e:
            self.compilation_output_label.setText(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error de Compilación", str(e))

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