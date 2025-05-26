import sys
from analizador import tokenize
from main_parser import Parseador
import subprocess
import math
import uuid
from collections import deque
from PyQt6.QtWidgets import (
     QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsLineItem, QGraphicsPolygonItem, QToolBar, QVBoxLayout, QWidget, 
    QInputDialog, QLineEdit, QMessageBox, QHBoxLayout, QLabel, QSizePolicy, 
    QPushButton, QTextEdit, QGraphicsSimpleTextItem # Importar QGraphicsSimpleTextItem
)
from PyQt6.QtGui import (
    QIcon, QPolygonF, QPen, QColor, QAction, QPainter, QCursor, QFont, QBrush, QFontMetrics
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QRect, QProcess

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
    def __init__(self, from_item, to_item, line_item, label=None, label_item=None):
        self.from_item = from_item
        self.to_item = to_item
        self.line_item = line_item
        self.label = label
        self.label_item = label_item
        self.next = None

class ConnectionList:
    def __init__(self):
        self.head = None

    def add_connection(self, from_item, to_item, line_item, label=None, label_item=None):
        new_node = ConnectionNode(from_item, to_item, line_item, label, label_item)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node

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
                
                if current.label_item and current.label_item.scene():
                     current.label_item.scene().removeItem(current.label_item)

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
                        
                        # Usar get_connection_point en lugar de edge_point
                        start_pos = current.from_item.get_connection_point(to_center)
                        end_pos = current.to_item.get_connection_point(from_center)
                        
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

                        # Actualizar posición de la etiqueta
                        if current.label_item:
                            mid_point = QLineF(start_pos, end_pos).center()
                            offset = QPointF(0, -15) # Offset encima de la línea
                            current.label_item.setPos(mid_point + offset)

            except Exception as e:
                print(f"Error al actualizar conexión: {str(e)}")
                
            current = current.next
            
    def get_connections_from(self, from_item):
        connections = []
        current = self.head
        while current:
            if current.from_item == from_item:
                connections.append((current.to_item, current.label))
            current = current.next
        return connections

    def get_all_connections(self):
        connections_list = []
        current = self.head
        while current:
            connections_list.append(current)
            current = current.next
        return connections_list

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
    
    def get_connection_point(self, target_point: QPointF) -> QPointF:
        """
        Calcula el punto en el borde de la forma más cercano al target_point,
        respetando las restricciones de conexión de los nodos de decisión.
        """
        item_center = self.center()
        line_to_target = QLineF(item_center, target_point)

        if self.shape_type == 'decision':
            w = self.boundingRect().width()
            h = self.boundingRect().height()
            local_points = [
                QPointF(w / 2, 0),
                QPointF(w, h / 2),
                QPointF(w / 2, h),
                QPointF(0, h / 2)
            ]
            scene_points = [self.mapToScene(p) for p in local_points]

            segments = [
                QLineF(scene_points[0], scene_points[1]),
                QLineF(scene_points[1], scene_points[2]),
                QLineF(scene_points[2], scene_points[3]),
                QLineF(scene_points[3], scene_points[0])
            ]

            possible_intersections = []
            for segment in segments:
                intersect_type, intersect_point_result = segment.intersects(line_to_target)
                if intersect_type == QLineF.IntersectionType.BoundedIntersection and intersect_point_result:
                     possible_intersections.append(intersect_point_result)

            if possible_intersections:
                 closest_point = min(possible_intersections, key=lambda p: QLineF(p, target_point).length())
                 return closest_point
            
            return item_center

        elif self.shape_type in ['start_end', 'connector']:  # Círculos
            radius = min(self.boundingRect().width(), self.boundingRect().height()) / 2
            direction = target_point - item_center
            length = math.sqrt(direction.x()**2 + direction.y()**2)
            if length == 0:
                return item_center
            return item_center + direction / length * radius
        
        else: # Para otras formas (rectángulo, paralelogramo, etc.)
            rect = self.sceneBoundingRect()
            
            # Crea las cuatro líneas que forman el borde del rectángulo
            top_line = QLineF(rect.topLeft(), rect.topRight())
            bottom_line = QLineF(rect.bottomLeft(), rect.bottomRight())
            left_line = QLineF(rect.topLeft(), rect.bottomLeft())
            right_line = QLineF(rect.topRight(), rect.bottomRight())

            rectangle_segments = [top_line, bottom_line, left_line, right_line]
            
            possible_intersections = []
            for segment in rectangle_segments:
                intersect_type, intersect_point_result = segment.intersects(line_to_target)
                if intersect_type == QLineF.IntersectionType.BoundedIntersection and intersect_point_result:
                    possible_intersections.append(intersect_point_result)
            
            if possible_intersections:
                closest_point = min(possible_intersections, key=lambda p: QLineF(p, target_point).length())
                return closest_point

            return item_center # En caso de que no haya intersección (ej. target_point está dentro de la forma)
            
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
        self.delete_mode = False 

        self.first_item = None
        self._temp_line = None
        self.connections = ConnectionList()
        self.start_node = None

    def set_delete_mode(self, enabled):
            self.delete_mode = enabled
            if enabled:
                self.set_shape_type(None)
                self.set_connection_mode(False)
                self.set_text_mode(False)


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

        if self.delete_mode and isinstance(item_at_click, FlowShape):
            reply = QMessageBox.question(
                self.views()[0], 
                "Confirmar eliminación",
                f"¿Eliminar esta figura ({item_at_click.shape_type})?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.removeItem(item_at_click)
            return
        
        if self.selected_shape:
            shape = FlowShape(self.selected_shape)
            shape.setPos(event.scenePos() - shape.boundingRect().center())
            self.addItem(shape)
            if shape.shape_type == 'start_end' and self.start_node is None:
                self.set_start_node(shape)
            return

        elif self.connection_mode:
            if isinstance(item_at_click, FlowShape):
                if self.first_item is None:
                    self.first_item = item_at_click
                    self.first_item.set_as_start_connector(True)
                    if not self._temp_line:
                        self._temp_line = QGraphicsLineItem()
                        self._temp_line.setPen(QPen(Qt.GlobalColor.darkGray, 2, Qt.PenStyle.DashLine))
                        self.addItem(self._temp_line)

                else:
                    second_item = item_at_click
                    if second_item != self.first_item:
                        valid_connection = True
                        connection_label = None

                        if self.first_item.shape_type == 'decision':
                            conn_point_on_decision = self.first_item.get_connection_point(second_item.center())
                            decision_center = self.first_item.center()
                            relative_point = conn_point_on_decision - decision_center
                            
                            # Condición para la salida 'Yes' o 'No' (inferior o derecha)
                            # Esto es una simplificación, podrías necesitar una lógica más robusta
                            # para determinar qué lado del rombo es "inferior" o "derecho"
                            # con respecto al punto de conexión.
                            # Por ahora, si la conexión no sale por la parte "superior" o "izquierda"
                            # del rombo, la consideramos válida para la decisión.
                            # Esto puede requerir un ajuste más preciso.
                            
                            # Para un rombo, las salidas "válidas" son típicamente por abajo o a la derecha
                            # Una conexión inválida para una decisión sería si intenta salir por la esquina
                            # superior o izquierda si se supone que es una salida "Yes" o "No"
                            # Esta lógica es compleja para un rombo. Podrías necesitar un enfoque diferente.
                            
                            # Por simplicidad, mantendré una lógica similar a la que tenías,
                            # pero ten en cuenta que el rombo tiene 4 lados.
                            # Para decisiones, lo más común es que "Yes" salga por un lado y "No" por otro.
                            
                            # Si quieres ser muy estricto con las esquinas del rombo, puedes usar esto:
                            # Los puntos del rombo son (w/2, 0), (w, h/2), (w/2, h), (0, h/2)
                            # Si relative_point está en el cuadrante superior-izquierdo del rombo (respecto a su centro),
                            # podría ser una salida "inválida" si se espera que salgan por abajo/derecha.
                            
                            # Para una decisión, a menudo se espera que haya una salida "verdadero" y una "falso".
                            # Si quieres controlar las direcciones, lo ideal sería que el `get_connection_point`
                            # ya diera pistas sobre la dirección.

                            # Deshabilitando la validación estricta de coordenadas para decisiones
                            # porque es compleja y puede generar falsos positivos/negativos
                            # basándose solo en las coordenadas relativas del punto de conexión.
                            # La validación de "Yes"/"No" de las etiquetas ya es un buen control.
                            
                            # if relative_point.x() < -1e-6 and relative_point.y() < -1e-6: 
                            #     valid_connection = False
                            #     QMessageBox.warning(self.views()[0], "Error de Conexión",
                            #                         "Las decisiones solo pueden salir por la derecha o por abajo.")

                        # if valid_connection and second_item.shape_type == 'decision':
                        #     conn_point_on_decision = second_item.get_connection_point(self.first_item.center())
                        #     decision_center = second_item.center()
                        #     relative_point = conn_point_on_decision - decision_center
                            
                        #     if relative_point.x() > 1e-6 and relative_point.y() > 1e-6: 
                        #         valid_connection = False
                        #         QMessageBox.warning(self.views()[0], "Error de Conexión",
                        #                             "Las decisiones solo pueden entrar por arriba o por la izquierda.")

                        if valid_connection:
                            if self.first_item.shape_type == 'decision':
                                label_text, ok = QInputDialog.getItem(
                                    self.views()[0],
                                    "Etiqueta de Decisión",
                                    "Seleccione la etiqueta para la conexión:",
                                    ["Yes", "No"],
                                    0, False
                                )
                                if ok and label_text:
                                    connection_label = label_text
                                else:
                                    valid_connection = False

                            if valid_connection:
                                self.create_connection(self.first_item, second_item, connection_label)

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
                if item_at_click.shape_type == 'process':
                    text, ok = QInputDialog.getMultiLineText(
                        self.views()[0], "Editar Texto",
                        "Ingrese el texto:", item_at_click.text)
                else:
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
            
            start_pos = self.first_item.get_connection_point(event.scenePos())
            
            self._temp_line.setLine(QLineF(start_pos, event.scenePos()))
        else:
            super().mouseMoveEvent(event)

    def create_connection(self, from_item, to_item, label=None):
        line = QGraphicsLineItem()
        line.setPen(QPen(QColor("#555555"), 2))
        self.addItem(line)

        start_pos = from_item.get_connection_point(to_item.center())
        end_pos = to_item.get_connection_point(from_item.center())
        line.setLine(QLineF(start_pos, end_pos))

        line.setZValue(-1)
        line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        arrow_size = 10
        angle = math.atan2(end_pos.y() - start_pos.y(), end_pos.x() - start_pos.x())
        
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
        self.addItem(arrow)
        arrow.setZValue(0)

        label_item = None
        if label:
            label_item = QGraphicsSimpleTextItem(label)
            label_item.setFont(QFont("Arial", 8))
            label_item.setBrush(QBrush(Qt.GlobalColor.black))
            self.addItem(label_item)
            label_item.setZValue(1)

            mid_point = QLineF(start_pos, end_pos).center()
            offset = QPointF(0, -15)
            label_item.setPos(mid_point + offset)

        self.connections.add_connection(from_item, to_item, (line, arrow), label, label_item)
    
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

# El resto del código de FlowMainWindow iría aquí.
# Solo asegúrate de que FlowMainWindow y FlowScene se importen correctamente.

class FlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Diagramas de Flujo")
        self.setStyleSheet("background-color: #0077B6")

        # Configuración inicial de la escena y vista
        self.scene = FlowScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Configurar barra de herramientas (tu código existente)
        toolbar = self.setup_toolbar()

        # Configurar paneles principales
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Panel izquierdo (editor)
        left_panel = QVBoxLayout()
        left_panel.addWidget(self.view)
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(left_panel)

        # Panel derecho (compilación)
        right_panel = self.setup_right_panel()

        # Asignar proporciones
        main_layout.addWidget(left_panel_widget, 2)  # 2/3
        main_layout.addWidget(right_panel, 1)        # 1/3

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def setup_right_panel(self):
        """Configura el panel derecho con compilación y terminal"""
        panel = QVBoxLayout()
        panel.setSpacing(5)

        # Área de compilación
        self.compilation_output = QTextEdit()
        self.compilation_output.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        self.compilation_output.setReadOnly(True)

        # Botón de compilación
        compile_btn = QPushButton("Compilar Diagrama")
        compile_btn.clicked.connect(self.compile_flowchart)

        # Terminal WSL
        self.wsl_terminal = WslTerminalWidget()

        # Añadir widgets al panel derecho
        panel.addWidget(QLabel("Salida de Compilación:"))
        panel.addWidget(self.compilation_output)
        panel.addWidget(compile_btn)
        panel.addWidget(self.wsl_terminal)

        # Configurar proporciones internas
        panel.setStretch(1, 1)  # compilation_output
        panel.setStretch(3, 2)  # wsl_terminal

        panel_widget = QWidget()
        panel_widget.setLayout(panel)
        return panel_widget
    
    
    def setup_toolbar(self):
            """Configura la barra de herramientas (tu código existente)"""

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

            # Configurar acciones con íconos y estado checkable
            self.select_action = QAction("Seleccionar", self)
            self.select_action.setCheckable(True)
            self.select_action.setChecked(True)  # Modo por defecto
            self.select_action.setIcon(QIcon.fromTheme("cursor-arrow"))
            self.select_action.triggered.connect(self.set_default_mode)
            
            self.connect_action = QAction("Conectar", self)
            self.connect_action.setCheckable(True)
            self.connect_action.setIcon(QIcon.fromTheme("draw-connector"))
            self.connect_action.triggered.connect(self.set_connection_mode)
            
            self.text_action = QAction("Texto", self)
            self.text_action.setCheckable(True)
            self.text_action.setIcon(QIcon.fromTheme("accessories-text-editor"))
            self.text_action.triggered.connect(self.set_text_mode)
            
            self.delete_action = QAction("Eliminar", self)
            self.delete_action.setCheckable(True)
            self.delete_action.setIcon(QIcon.fromTheme("edit-delete"))
            self.delete_action.triggered.connect(self.set_delete_mode)

            # Agregar acciones a la barra de herramientas
            toolbar.addAction(self.select_action)
            toolbar.addAction(self.connect_action)
            toolbar.addAction(self.text_action)
            toolbar.addAction(self.delete_action)





            # ... (resto de tu configuración de toolbar)
            return toolbar


    def set_default_mode(self):
        """Activa el modo selección/movimiento"""
        self._reset_modes()
        self.select_action.setChecked(True)
        self.scene.set_shape_type(None)
        self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def set_connection_mode(self):
        """Activa el modo conexión"""
        self._reset_modes()
        self.connect_action.setChecked(True)
        self.scene.set_connection_mode(True)
        self.view.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def set_text_mode(self):
        """Activa el modo texto"""
        self._reset_modes()
        self.text_action.setChecked(True)
        self.scene.set_text_mode(True)
        self.view.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

    def set_delete_mode(self):
        """Activa el modo eliminación"""
        self._reset_modes()
        self.delete_action.setChecked(True)
        self.scene.set_delete_mode(True)
        self.view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _reset_modes(self):
        """Desactiva todos los modos y desmarca los botones"""
        self.select_action.setChecked(False)
        self.connect_action.setChecked(False)
        self.text_action.setChecked(False)
        self.delete_action.setChecked(False)
        self.scene.set_connection_mode(False)
        self.scene.set_text_mode(False)
        self.scene.set_delete_mode(False)




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

    def toggle_delete_mode(self):
        self.scene.delete_mode = not self.scene.delete_mode
        if self.scene.delete_mode:
            self.view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.delete_action.setChecked(True)  # Mostrar como activado
            # Desactivar otros modos y sus acciones
            self.select_action.setChecked(False)
            self.connect_action.setChecked(False)
            self.text_action.setChecked(False)
        else:
            self.view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.delete_action.setChecked(False)


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
                next_node_in_flow = next_node_in_flow[0]  # Obtener el nodo de la conexión
                if next_node_in_flow.id not in visited_nodes_ids:
                    processing_queue.append(next_node_in_flow)
        if not final_flow_steps:
             self.compilation_output.setText("El nodo de inicio no tiene conexiones salientes o no se pudo procesar el flujo.")
             return None
        return final_flow_steps

    def compile_flowchart(self): 
        # Ejemplo para aceder a los nodos de decisión y sus conexiones
        # for i in self.scene.items():
        #     if isinstance(i, FlowShape):
        #         if i.shape_type == "decision":
        #             print(f"El nodo de decisión {i.text} tiene {len(self.scene.connections.get_connections_from(i))} conexiones salientes.")
        #             yes = None
        #             no = None
        #             # Verificar conexiones salientes del nodo de decisión
        #             # i es el node de decisión actual
        #             for conn in self.scene.connections.get_connections_from(i):
        #                 if conn[1] == "Yes":
        #                     yes = conn[0]
        #                     # Imprimir información de la conexión Yes (Es el nodo al cual apunta la conexión si)
        #                     print(f"Conexión 'Yes' encontrada: {yes.text} (ID: {yes.id})")
        #                 elif conn[1] == "No":
        #                     no = conn[0]
        #                     # Imprimir información de la conexión No (Es el nodo al cual apunta la conexión no)
        #                     print(f"Conexión 'No' encontrada: {no.text} (ID: {no.id})")
        try:
            if not self.scene.start_node:
                self.compilation_output.setText("Error: No se ha definido un nodo de inicio.\n"
                                                    "Añada una figura 'Inicio/Fin'.")
                QMessageBox.warning(self, "Error de Compilación", "No se ha definido un nodo de inicio.")
                return
            final_flow_steps = []
            #Diccionario el cual contiene las funciones
            #Ejamplo de como se guardan: {"Nombre de la funcion": [Nodo1, nodo2, nodo3]}
            diccionary_functions = {}
            print("hola")
            
            for item in self.scene.items():
                if isinstance(item, QGraphicsLineItem):
                    pass
                elif isinstance(item, QGraphicsPolygonItem):
                    pass

                elif isinstance(item, FlowShape):
                    for function in diccionary_functions:
                        if item.text.strip() == function: 
                            QMessageBox.warning(self, "Error de sintaxis", "Se detectaron dos funciones con el mismo nombre")
                            break

                    if item.shape_type == "start_end" and item.text.strip() == "inicio":
                            final_flow_steps = self.analisis_connections(item)
                            diccionary_functions[item.text.strip()] = final_flow_steps

                    elif item.shape_type == "start_end":
                            final_flow_steps = self.analisis_connections(item)
                            diccionary_functions[item.text.strip()] = final_flow_steps

            output_text = "Orden de Ejecución Detectado:\n"
            for i, function in enumerate(diccionary_functions):
                keys = list(diccionary_functions.keys())
                print(f"Función: {function} (ID: {id(function)})")
                output_text += f"\nNodos de la funcion: {keys[i]}\n"
                for j, node in enumerate(diccionary_functions[function]):
                    node_text = f"Nodo: {node.text.strip() if node.text.strip() else node.shape_type}"
                    output_text += f"{j+1}. {node_text} (Tipo: {node.shape_type} (dir: {node.text.strip()}) (id: {id(node.id)}))\n"

            diccionary_functions['conn'] = self.scene.connections

            parser = Parser(diccionary_functions)
            codigo_c = parser.generate_code()

            print(codigo_c)
            token = tokenize(codigo_c)
            self.compilation_output.setText(codigo_c)

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
            self.compilation_output.setText(f"Error: {str(e)}")
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