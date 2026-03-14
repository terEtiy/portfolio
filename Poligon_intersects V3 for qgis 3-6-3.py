# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry, QgsProject, QgsVectorLayer, QgsFeature, QgsWkbTypes
import time

sttime = None

# Получение выбранного полигона
selected_feature = iface.activeLayer().selectedFeatures()[0]
selected_geometry = selected_feature.geometry()

group_name = 'Intersecting Layers'
group_name2 = 'podzon'
clipped_group_name = 'Clipped Layers'
root = QgsProject.instance().layerTreeRoot()
group = root.addGroup(group_name)
group2 = root.addGroup(group_name2)
clipped_group = root.addGroup(clipped_group_name)

def getGeometryTypeAsString(layer):
    if layer.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint]:
        return "Point"
    elif layer.wkbType() in [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString]:
        return "LineString"
    elif layer.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon]:
        return "Polygon"

# Получение списка всех слоев в проекте
layers = QgsProject.instance().mapLayers().values()

intersecting_layers = []
clipped_count = 0

for layer in layers:
    if sttime is None:
        sttime = time.time()
        
    layer_added = False  # Инициализация флага
    if layer.name() in ['map_3','Точки пересечений с территориальными подзонами','Ранее учтенные земельные участки']:
        continue
    
    if layer.type() == QgsVectorLayer.VectorLayer:
        features = layer.getFeatures()

        for feature in features:
            feature_geometry = feature.geometry()

            if not feature_geometry:
                continue

            if not feature_geometry.intersects(selected_geometry):
                continue
            
            intersection = feature.geometry().intersection(selected_geometry)
            if intersection.isEmpty():
                continue
            
            # Добавляем слой в соответствующую группу
            if not layer_added:
                if layer.name() in ['Территории_преимущественно_компактной_застройки','Прочие виды использования']:
                    intersecting_layers.append(layer)
                    print('group2', layer.name())
                    eltime = time.time() - sttime
                    print(eltime)
                    sttime = None
                    group2.addLayer(layer)
                else:
                    intersecting_layers.append(layer)
                    group.addLayer(layer)
                    print('group2',layer.name())
                    eltime = time.time() - sttime
                    print(eltime)
                    sttime = None
                layer_added = True
                
            if layer.name() in ['Прочие виды использования','Функциональное назначение не установлено']:
                continue
            else:
                # Создаем обрезанный слой для каждого пересечения
                if layer.isValid():
                    clipped_count += 1
                    clipped_area = intersection.area()
                    clipped_layer_name = f"{layer.name()}_clipped_{clipped_count}_area_{clipped_area:.2f}"
                    gt = getGeometryTypeAsString(layer) or "Unknown"
                    clipped_layer = QgsVectorLayer(f"{gt}?crs={layer.crs().authid()}", clipped_layer_name, "memory")
                    dp = clipped_layer.dataProvider()
                    dp.addAttributes(layer.fields())
                    clipped_layer.updateFields()

                    new_feature = QgsFeature()
                    new_feature.setGeometry(intersection)
                    new_feature.setAttributes(feature.attributes())
                    dp.addFeatures([new_feature])

                    QgsProject.instance().addMapLayer(clipped_layer, False)
                    clipped_group.addLayer(clipped_layer)
        
print('/////////////////////////////////////////////////////////////')