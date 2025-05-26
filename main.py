from window import FlowMainWindow
import sys
from PyQt6.QtWidgets import QApplication
import os
# os.environ["QT_QPA_PLATFORM"] = "xcb"
app = QApplication(sys.argv)
window = FlowMainWindow()
window.resize(1200, 800)
window.show()
sys.exit(app.exec())

