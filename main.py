from window import FlowMainWindow
import sys
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
window = FlowMainWindow()
window.resize(1200, 800)
window.show()
sys.exit(app.exec())

