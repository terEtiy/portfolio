# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gpzuToolsDialog
                                 A QGIS plugin
 gpzu tools
                             -------------------
        begin                : 2017-06-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by gisproject
        email                : ifomin@gispro.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QRegExp
from qgis.PyQt.QtGui import QRegExpValidator
from .gpzu_tools_dialog_base import Ui_gpzuToolsDialogBase


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpzu_tools_dialog_base.ui'))


class gpzuToolsDialog(QtWidgets.QDialog, Ui_gpzuToolsDialogBase):
#class gpzuToolsDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(gpzuToolsDialog, self).__init__(parent)
        self.setupUi(self)
        self.lineEdit.setText("0")
        regexp = QRegExp('[0-9]*')
        validator = QRegExpValidator(regexp)
        self.lineEdit.setValidator(validator)
        scales = ('2000', '5000', '10000')
        for scale in scales:
            self.comboBox_2.addItem(scale)

    def selectFile(self, mode='open'):
        fileDialog = QtWidgets.QFileDialog()  # Обновлено для PyQt5
        fileDialog.setNameFilter("Geopackage (*.gpkg)")
        fileDialog.selectNameFilter("Geopackage (*.gpkg)")

        if mode == 'save':
            fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)  # Обновлено для PyQt5
        else:
            fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)  # Обновлено для PyQt5

        result = fileDialog.exec_()
        if result == 0:
            filename = None
        else:
            filename = fileDialog.selectedFiles()[0]
            if mode == 'save' and os.path.splitext(filename)[1] != '.gpkg':
                filename += '.gpkg'
        return filename

