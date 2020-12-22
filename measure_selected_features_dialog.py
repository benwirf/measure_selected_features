"""
/****************************************************************************************
Copyright:  (C) Ben Wirf
Date:       April 2020
Email:      ben.wirf@gmail.com
****************************************************************************************/
"""

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QDockWidget, QWidget, QGridLayout, QLabel, QLineEdit

class MeasureSelectedFeaturesDialog(QDockWidget):
    
    was_closed = pyqtSignal()
    
    def __init__(self):
        QDockWidget.__init__(self)
        self.setWindowTitle('Measure selected features')
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QGridLayout(self)
        self.widget.setLayout(self.layout)
        self.lbl_1 = QLabel('Geographic\n(ellipsoidal)', self)
        self.le_geo = QLineEdit(self)
        self.le_geo.setReadOnly(True)
        self.le_geo.setMinimumSize(QSize(350, 10))
        self.lbl_2 = QLabel('Projected\n(planar)', self)
        self.le_proj = QLineEdit(self)
        self.le_proj.setReadOnly(True)
        self.le_proj.setMinimumSize(QSize(350, 10))
        self.lbl_3 = QLabel('Converted', self)
        self.le_converted_km = QLineEdit(self)
        self.le_converted_km.setReadOnly(True)
        self.le_converted_km.setMinimumSize(QSize(200, 10))
        self.le_converted_ha = QLineEdit(self)
        self.le_converted_ha.setReadOnly(True)
        self.le_converted_ha.setMinimumSize(QSize(200, 10))
        self.layout.addWidget(self.lbl_1, 0, 0, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.le_geo, 0, 1, 1, 1, Qt.AlignJustify)
        self.layout.addWidget(self.lbl_2, 0, 2, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.le_proj, 0, 3, 1, 1, Qt.AlignJustify)
        self.layout.addWidget(self.lbl_3, 0, 4, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.le_converted_km, 0, 5, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.le_converted_ha, 0, 6, 1, 1, Qt.AlignCenter)


    def closeEvent(self, event):
        self.was_closed.emit()

