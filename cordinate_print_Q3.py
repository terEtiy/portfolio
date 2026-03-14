# -*- coding: utf-8 -*-
# Импортируем необходимые библиотеки
from qgis.core import QgsProject, QgsWkbTypes

# Получаем активный слой в QGIS
layer = iface.activeLayer()

# Получаем объект проекта QGIS
project = QgsProject.instance()

# Получаем ID активного слоя
layer_id = layer.id()

# Получаем реестр выбранных объектов на активном слое
selection = layer.selectedFeatures()

# Проверяем, есть ли выбранные объекты
if len(selection) > 0:
    # Получаем выбранный объект (полигон)
    selected_feature = selection[0]
    # Получаем геометрию полигона
    geometry = selected_feature.geometry()
    # Проверяем тип геометрии
    if geometry.isMultipart():
        # Обработка мультиполигона
        for part in geometry.asMultiPolygon():
            for ring in part:
                for coordinate in ring:
                    print("1 {},{}".format(coordinate.y(), coordinate.x()))
    else:
        # Получаем координаты полигона
        coordinates = geometry.asPolygon()[0]
        # Выводим координаты в консоль
        print("1 {},{}".format(coordinates[0].y(), coordinates[0].x()))
        for i, coordinate in enumerate(coordinates):
            if i > 0:
                print("{} {},{}".format(i+1, coordinate.y(), coordinate.x()))
else:
    # Если объект не выбран, выводим сообщение об ошибке
    print("No feature selected")