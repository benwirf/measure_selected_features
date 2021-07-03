"""
/****************************************************************************************
 *   Copyright:  (C) Ben Wirf
 *   Date:       April 2020 (updated June 2021)
 *   Email:      ben.wirf@gmail.com
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (QDockWidget, QWidget, QGridLayout, QLabel,
                            QLineEdit, QRadioButton, QComboBox)

class MeasureSelectedFeaturesDialog(QDockWidget):
    
    was_closed = pyqtSignal()
    
    def __init__(self):
        QDockWidget.__init__(self)
        self.setWindowTitle('Measure selected features')
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QGridLayout(self)
        self.widget.setLayout(self.layout)
        #####31-05-21
        self.rad_1 = QRadioButton('Ellipsoidal', self)
        self.rad_2 = QRadioButton('Planimetric', self)
        #####31-05-21
        self.lbl_1 = QLabel('Total selected features', self)
        self.le_total = QLineEdit(self)
        self.le_total.setReadOnly(True)
        self.le_total.setMinimumSize(QSize(450, 25))
        #####24-06-21
        self.cb_units = QComboBox(self)
        self.cb_units.setMinimumSize(QSize(250, 25))
        self.layout.addWidget(self.rad_1, 0, 0, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.rad_2, 0, 1, 1, 1, Qt.AlignCenter)
        self.layout.addWidget(self.lbl_1, 0, 2, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.le_total, 0, 3, 1, 1, Qt.AlignJustify)
        self.layout.addWidget(self.cb_units, 0, 4, 1, 1, Qt.AlignJustify)


    def closeEvent(self, event):
        self.was_closed.emit()

