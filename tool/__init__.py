# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gpzuTools
                                 A QGIS plugin
 ...
"""

from qgis.core import QgsMessageLog, Qgis  # Добавляем необходимые импорты

def classFactory(iface):
    """Load gpzuTools class from file gpzuTools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    QgsMessageLog.logMessage("Initializing gpzuTools...", "gpzuTools", Qgis.Info)  # Логируем начало инициализации
    try:
        from .gpzu_tools import gpzuTools
        QgsMessageLog.logMessage("gpzuTools loaded successfully.", "gpzuTools", Qgis.Info)  # Успешная загрузка
        return gpzuTools(iface)
    except Exception as e:
        QgsMessageLog.logMessage("Error loading gpzuTools: " + str(e), "gpzuTools", Qgis.Critical)  # Логирование ошибки
        raise
