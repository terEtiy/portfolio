# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QFileDialog, QTabWidget, QTextEdit, QMessageBox)
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, 
                      QgsPointXY, QgsField, QgsFields, QgsSpatialIndex)
from qgis.PyQt.QtGui import QColor
import xml.etree.ElementTree as ET
import os

class LandParcelProcessorDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработчик XML файлов земельных участков")
        self.setMinimumSize(1000, 700)
        
        self.parcel_data = {}
        self.parcel_location_geom = None
        self.parcel_obj_parts_dict = {}
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Обработка XML файлов земельных участков")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Выбрать XML файл земельного участка")
        self.load_btn.clicked.connect(self.load_xml_file)
        self.load_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; }")
        btn_layout.addWidget(self.load_btn)
        
        self.export_main_btn = QPushButton("Экспорт основного контура")
        self.export_main_btn.clicked.connect(self.export_main_parcel)
        self.export_main_btn.setEnabled(False)
        btn_layout.addWidget(self.export_main_btn)
        
        self.export_parts_btn = QPushButton("Экспорт частей участка")
        self.export_parts_btn.clicked.connect(self.export_parts)
        self.export_parts_btn.setEnabled(False)
        btn_layout.addWidget(self.export_parts_btn)
        
        layout.addLayout(btn_layout)
        
        # Информация о файле
        self.file_info_label = QLabel("Файл не выбран")
        self.file_info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.file_info_label)
        
        # Вкладки для разных типов данных
        self.tabs = QTabWidget()
        
        # Вкладка основной информации
        self.main_info_tab = QTableWidget()
        self.main_info_tab.setColumnCount(2)
        self.main_info_tab.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.main_info_tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.main_info_tab, "Основная информация")
        
        # Вкладка основного контура
        self.main_contour_tab = QTableWidget()
        self.main_contour_tab.setColumnCount(6)
        self.main_contour_tab.setHorizontalHeaderLabels([
            "Кадастровый номер", "Кадастровый квартал", "Категория земель", 
            "Площадь", "Погрешность", "Номер ЕГРН"
        ])
        self.main_contour_tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.main_contour_tab, "Основной контур")
        
        # Вкладка частей участка
        self.parts_tab = QTableWidget()
        self.parts_tab.setColumnCount(8)
        self.parts_tab.setHorizontalHeaderLabels([
            "Номер части", "Площадь", "Погрешность площади", "Примечание",
            "Вид обременения", "Код обременения", "Действует с", "Срок действия"
        ])
        self.parts_tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.parts_tab, "Части участка")
        
        # Вкладка ограничений
        self.restrictions_tab = QTableWidget()
        self.restrictions_tab.setColumnCount(6)
        self.restrictions_tab.setHorizontalHeaderLabels([
            "Номер части", "Вид обременения", "Код обременения", 
            "Действует с", "Срок действия", "Содержание ограничения"
        ])
        self.restrictions_tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.restrictions_tab, "Ограничения и обременения")
        
        # Вкладка сырых данных
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.tabs.addTab(self.raw_data_text, "Сырые данные XML")
        
        layout.addWidget(self.tabs)
        
        # Кнопки добавления слоев
        layer_btn_layout = QHBoxLayout()
        
        self.add_main_layer_btn = QPushButton("Добавить основной контур в проект")
        self.add_main_layer_btn.clicked.connect(self.add_main_layer_to_project)
        self.add_main_layer_btn.setEnabled(False)
        self.add_main_layer_btn.setStyleSheet("QPushButton { padding: 8px; background-color: #e1f5fe; }")
        layer_btn_layout.addWidget(self.add_main_layer_btn)
        
        self.add_parts_layer_btn = QPushButton("Добавить части участка в проект")
        self.add_parts_layer_btn.clicked.connect(self.add_parts_layer_to_project)
        self.add_parts_layer_btn.setEnabled(False)
        self.add_parts_layer_btn.setStyleSheet("QPushButton { padding: 8px; background-color: #e8f5e8; }")
        layer_btn_layout.addWidget(self.add_parts_layer_btn)
        
        self.add_all_layers_btn = QPushButton("Добавить все слои в проект")
        self.add_all_layers_btn.clicked.connect(self.add_all_layers_to_project)
        self.add_all_layers_btn.setEnabled(False)
        self.add_all_layers_btn.setStyleSheet("QPushButton { padding: 8px; background-color: #fff3e0; font-weight: bold; }")
        layer_btn_layout.addWidget(self.add_all_layers_btn)
        
        layout.addLayout(layer_btn_layout)
        
        # Статус бар
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e8; border: 1px solid #4caf50;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_xml_file(self):
        """Выбор XML файла земельного участка"""
        xml_file, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите XML файл земельного участка", 
            "", 
            "XML files (*.xml);;All files (*.*)"
        )
        
        if not xml_file:
            self.status_label.setText("Файл не выбран")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffebee; border: 1px solid #f44336;")
            return
        
        try:
            self.file_info_label.setText(f"Загружен файл: {os.path.basename(xml_file)}")
            self.status_label.setText("Обработка XML файла...")
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0; border: 1px solid #ff9800;")
            
            # Парсинг XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Построение геометрий
            self.parcel_data, self.parcel_location_geom, self.parcel_obj_parts_dict = self.xml_land_record_root_to_geoms(root)
            
            # Отображение данных в таблицах
            self.display_data_in_tables(xml_file)
            
            # Активация кнопок
            self.export_main_btn.setEnabled(True)
            self.export_parts_btn.setEnabled(True)
            self.add_main_layer_btn.setEnabled(True)
            self.add_parts_layer_btn.setEnabled(True if self.parcel_obj_parts_dict else False)
            self.add_all_layers_btn.setEnabled(True)
            
            self.status_label.setText("Обработка завершена успешно")
            self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e8; border: 1px solid #4caf50;")
            
        except Exception as e:
            error_msg = f"Ошибка при обработке XML файла:\n{str(e)}"
            self.status_label.setText("Ошибка обработки файла")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffebee; border: 1px solid #f44336;")
            QMessageBox.critical(self, "Ошибка", error_msg)
    
    def xml_land_record_root_to_geoms(self, r):
        """Парсим XML преобразуя его в геометрии"""
        # Сведения о земельном участке
        parcel_data = {
            "Кадастровый номер": None,
            "Номер кадастрового квартала": None,
            "Дата присвоения кадастрового номера": None,
            "Категория земель": None,
            "Код категории земель": None,
            "Общая площадь": None,
            "Погрешность общей площади": None,
            "Номер ЕГРН": None,
            "Дата ЕГРН": None
        }
        
        # Геометрия контура ЗУ (мультигеометрия)
        parcel_location = []
        # Геометрии и инфа частей ЗУ (список мультигеометрий)
        parcel_obj_parts = []
        # Ограничения частей ЗУ
        restrictions_parts = []

        def root_to_parts(root, parents_chain=None):
            for child in root:
                if child.tag.startswith('{'):
                    child.tag = child.tag.split('}', 1)[-1]
                curr_chain = parents_chain + [child.tag] if parents_chain else [child.tag]

                # Ограничения частей ЗУ
                if child.tag == "restriction_encumbrance" and parents_chain == ["land_record", "restrictions_encumbrances"]:
                    restrictions_parts.append({})
                elif child.tag == "part_number" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance"]:
                    restrictions_parts[-1]["n"] = child.text
                elif child.tag == "value" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance", "encumbrance_type"]:
                    restrictions_parts[-1]["Вид обременения"] = child.text
                elif child.tag == "code" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance", "encumbrance_type"]:
                    restrictions_parts[-1]["Код вида обременения"] = child.text
                elif child.tag == "starting_date" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance"]:
                    restrictions_parts[-1]["Действует с"] = child.text
                elif child.tag == "validity" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance"]:
                    restrictions_parts[-1]["Срок действия"] = child.text
                elif child.tag == "content_restrict_encumbrances" and parents_chain == ["land_record", "restrictions_encumbrances", "restriction_encumbrance"]:
                    restrictions_parts[-1]["Содержание ограничения"] = child.text

                # Сведения о земельном участке
                elif child.tag == "registration_date" and parents_chain == ["land_record", "record_info"]:
                    parcel_data["Дата присвоения кадастрового номера"] = child.text
                elif child.tag == "cad_number" and parents_chain == ["land_record", "object", "common_data"]:
                    parcel_data["Кадастровый номер"] = child.text
                elif child.tag == "quarter_cad_number" and parents_chain == ["land_record", "object", "common_data"]:
                    parcel_data["Номер кадастрового квартала"] = child.text
                elif child.tag == "value" and parents_chain == ["land_record", "params", "category", "type"]:
                    parcel_data["Категория земель"] = child.text
                elif child.tag == "code" and parents_chain == ["land_record", "params", "category", "type"]:
                    parcel_data["Код категории земель"] = child.text
                elif child.tag == "value" and parents_chain == ["land_record", "params", "area"]:
                    parcel_data["Общая площадь"] = child.text
                elif child.tag == "inaccuracy" and parents_chain == ["land_record", "params", "area"]:
                    parcel_data["Погрешность общей площади"] = child.text
                elif child.tag == "registration_number" and parents_chain == ["details_statement", "group_top_requisites"]:
                    parcel_data["Номер ЕГРН"] = child.text
                elif child.tag == "date_formation" and parents_chain == ["details_statement", "group_top_requisites"]:
                    parcel_data["Дата ЕГРН"] = child.text

                # Части земельных участков
                elif child.tag == "object_part" and parents_chain == ["land_record", "object_parts"]:
                    parcel_obj_parts.append({"geom": []})
                elif child.tag == "part_number" and parents_chain == ["land_record", "object_parts", "object_part"]:
                    parcel_obj_parts[-1]["n"] = child.text
                elif child.tag == "area" and parents_chain == ["land_record", "object_parts", "object_part"]:
                    parcel_obj_parts[-1]["Площадь"] = None
                    parcel_obj_parts[-1]["Погрешность площади"] = None
                    parcel_obj_parts[-1]["Тип площади"] = None
                    parcel_obj_parts[-1]["Код типа площади"] = None
                elif child.tag == "value" and parents_chain == ["land_record", "object_parts", "object_part", "area"]:
                    parcel_obj_parts[-1]["Площадь"] = child.text
                elif child.tag == "inaccuracy" and parents_chain == ["land_record", "object_parts", "object_part", "area"]:
                    parcel_obj_parts[-1]["Погрешность площади"] = child.text
                elif child.tag == "footnote" and parents_chain == ["land_record", "object_parts", "object_part"]:
                    parcel_obj_parts[-1]["Примечание"] = child.text
                elif child.tag == "contour" and parents_chain == ["land_record", "object_parts", "object_part", "contours"]:
                    parcel_obj_parts[-1]["geom"].append([])
                elif child.tag == "spatial_element" and parents_chain == ["land_record", "object_parts", "object_part", "contours", "contour", "entity_spatial", "spatials_elements"]:
                    parcel_obj_parts[-1]["geom"][-1].append([])
                elif child.tag == "ordinate" and parents_chain == ["land_record", "object_parts", "object_part", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates"]:
                    parcel_obj_parts[-1]["geom"][-1][-1].append({})
                elif child.tag == "x" and parents_chain == ["land_record", "object_parts", "object_part", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_obj_parts[-1]["geom"][-1][-1][-1]["x"] = float(child.text.replace(",", "."))
                elif child.tag == "y" and parents_chain == ["land_record", "object_parts", "object_part", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_obj_parts[-1]["geom"][-1][-1][-1]["y"] = float(child.text.replace(",", "."))
                elif child.tag == "ord_nmb" and parents_chain == ["land_record", "object_parts", "object_part", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_obj_parts[-1]["geom"][-1][-1][-1]["n"] = int(child.text)

                # Контур земельного участка
                elif child.tag == "contour" and parents_chain == ["land_record", "contours_location", "contours"]:
                    parcel_location.append([])
                elif child.tag == "spatial_element" and parents_chain == ["land_record", "contours_location", "contours", "contour", "entity_spatial", "spatials_elements"]:
                    parcel_location[-1].append([])
                elif child.tag == "ordinate" and parents_chain == ["land_record", "contours_location", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates"]:
                    parcel_location[-1][-1].append({})
                elif child.tag == "x" and parents_chain == ["land_record", "contours_location", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_location[-1][-1][-1]["x"] = float(child.text.replace(",", "."))
                elif child.tag == "y" and parents_chain == ["land_record", "contours_location", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_location[-1][-1][-1]["y"] = float(child.text.replace(",", "."))
                elif child.tag == "ord_nmb" and parents_chain == ["land_record", "contours_location", "contours", "contour", "entity_spatial", "spatials_elements", "spatial_element", "ordinates", "ordinate"]:
                    parcel_location[-1][-1][-1]["n"] = int(child.text)

                root_to_parts(child, curr_chain)

        root_to_parts(r)

        parcel_location_geom = self.parts_to_multi_polygon(parcel_location)
        parcel_obj_parts_dict = {}
        
        for obj_part in parcel_obj_parts:
            number = obj_part.pop("n")
            obj_part["geom"] = self.parts_to_multi_polygon(obj_part["geom"])

            if number not in parcel_obj_parts_dict:
                parcel_obj_parts_dict[number] = []

            parcel_obj_parts_dict[number].append(obj_part)

        # Заполняем ограничения частей
        for part_restr in restrictions_parts:
            if "n" in part_restr:
                number = part_restr.pop("n")
            else:
                number = ""

            if number not in parcel_obj_parts_dict:
                parcel_obj_parts_dict[number] = []

            select_obj_part = None
            for obj_part in parcel_obj_parts_dict[number]:
                if "Обременения" not in obj_part:
                    select_obj_part = obj_part
                    break

            if select_obj_part is None:
                select_obj_part = {}
                parcel_obj_parts_dict[number].append(select_obj_part)

            select_obj_part["Обременения"] = part_restr
            if "geom" not in select_obj_part:
                if number == "":
                    select_obj_part["geom"] = QgsGeometry(parcel_location_geom)
                    select_obj_part["Площадь"] = parcel_data.get("Общая площадь")
                    select_obj_part["Погрешность площади"] = parcel_data.get("Погрешность общей площади")
                else:
                    select_obj_part["geom"] = QgsGeometry()

        return parcel_data, parcel_location_geom, parcel_obj_parts_dict

    def parts_to_multi_polygon(self, parts_list):
        """Преобразует список частей в мультиполигон"""
        multipolygon_parts = []

        # Соберём все ринги
        rings = []
        for part in parts_list:
            for contour in part:
                coord_set = set()
                ring_list = []
                for p in contour:
                    if p["n"] not in coord_set:
                        # Меняем координаты местами для корректного отображения в QGIS
                        ring_list.append((p["n"], f'{p["y"]} {p["x"]}'))
                    coord_set.add(p["n"])
                
                if ring_list:
                    # Сортируем по номерам точек
                    ring_list.sort(key=lambda p: p[0])
                    ring_list = [p[1] for p in ring_list]
                    # Замыкаем контур
                    ring_list.append(ring_list[0])
                    rings.append("(" + ", ".join(ring_list) + ")")

        # Создаем полигоны из рингов
        polygons = [QgsGeometry.fromWkt(f"Polygon({ring})") for ring in rings]

        # Определяем отношения между полигонами
        ring_relations = {i: (set(), set(), rings[i]) for i, p in enumerate(polygons)}

        # Создаем пространственный индекс для быстрого расчета
        idx = QgsSpatialIndex()
        for i, p in enumerate(polygons):
            idx.addFeature(i, p.boundingBox())

        for i1, p1 in enumerate(polygons):
            intersections = idx.intersects(p1.boundingBox())

            for i2 in intersections:
                if i2 == i1:
                    continue

                p2 = polygons[i2]

                if p1.contains(p2):
                    ring_relations[i1][0].add(i2)
                    ring_relations[i2][1].add(i1)

        # Формируем мультиполигон
        rings_with_levels = [(i, len(ring_relations[i][1])) for i, r in enumerate(rings)]
        rings_with_levels.sort(key=lambda r: r[1])

        processed_rings = set()
        for i1, level1 in rings_with_levels:
            if i1 in processed_rings:
                continue

            r1 = ring_relations[i1][2]
            rings_contains = ring_relations[i1][0]

            # Внешние кольца имеют четный уровень
            if (level1 % 2) != 0:
                continue

            part_rings = [r1]
            processed_rings.add(i1)

            for i2 in rings_contains:
                level2 = len(ring_relations[i2][1])

                if (level2 - 1) != level1:
                    continue

                r2 = ring_relations[i2][2]
                part_rings.append(r2)
                processed_rings.add(i2)

            if part_rings:
                wkt_polygon = "Polygon(" + ",".join(part_rings) + ")"
                polygon_geom = QgsGeometry.fromWkt(wkt_polygon)
                multipolygon_parts.append(polygon_geom)

        multipolygon_geom = QgsGeometry.collectGeometry(multipolygon_parts)
        return multipolygon_geom

    def display_data_in_tables(self, xml_file):
        """Отображает данные в таблицах интерфейса"""
        
        # Основная информация
        self.main_info_tab.setRowCount(len(self.parcel_data))
        for i, (key, value) in enumerate(self.parcel_data.items()):
            self.main_info_tab.insertRow(i)
            self.main_info_tab.setItem(i, 0, QTableWidgetItem(str(key)))
            self.main_info_tab.setItem(i, 1, QTableWidgetItem(str(value) if value else ""))
        
        # Основной контур
        self.main_contour_tab.setRowCount(1)
        self.main_contour_tab.insertRow(0)
        self.main_contour_tab.setItem(0, 0, QTableWidgetItem(self.parcel_data.get("Кадастровый номер", "")))
        self.main_contour_tab.setItem(0, 1, QTableWidgetItem(self.parcel_data.get("Номер кадастрового квартала", "")))
        self.main_contour_tab.setItem(0, 2, QTableWidgetItem(self.parcel_data.get("Категория земель", "")))
        self.main_contour_tab.setItem(0, 3, QTableWidgetItem(self.parcel_data.get("Общая площадь", "")))
        self.main_contour_tab.setItem(0, 4, QTableWidgetItem(self.parcel_data.get("Погрешность общей площади", "")))
        self.main_contour_tab.setItem(0, 5, QTableWidgetItem(self.parcel_data.get("Номер ЕГРН", "")))
        
        # Части участка
        parts_count = sum(len(parts) for parts in self.parcel_obj_parts_dict.values())
        self.parts_tab.setRowCount(parts_count)
        row = 0
        for part_number, parts_list in self.parcel_obj_parts_dict.items():
            for part_data in parts_list:
                self.parts_tab.insertRow(row)
                self.parts_tab.setItem(row, 0, QTableWidgetItem(str(part_number)))
                self.parts_tab.setItem(row, 1, QTableWidgetItem(part_data.get("Площадь", "")))
                self.parts_tab.setItem(row, 2, QTableWidgetItem(part_data.get("Погрешность площади", "")))
                self.parts_tab.setItem(row, 3, QTableWidgetItem(part_data.get("Примечание", "")))
                
                # Данные обременений
                if "Обременения" in part_data:
                    encumbrance = part_data["Обременения"]
                    self.parts_tab.setItem(row, 4, QTableWidgetItem(encumbrance.get("Вид обременения", "")))
                    self.parts_tab.setItem(row, 5, QTableWidgetItem(encumbrance.get("Код вида обременения", "")))
                    self.parts_tab.setItem(row, 6, QTableWidgetItem(encumbrance.get("Действует с", "")))
                    self.parts_tab.setItem(row, 7, QTableWidgetItem(encumbrance.get("Срок действия", "")))
                
                row += 1
        
        # Ограничения
        restrictions_count = sum(1 for parts_list in self.parcel_obj_parts_dict.values() 
                               for part_data in parts_list if "Обременения" in part_data)
        self.restrictions_tab.setRowCount(restrictions_count)
        row = 0
        for part_number, parts_list in self.parcel_obj_parts_dict.items():
            for part_data in parts_list:
                if "Обременения" in part_data:
                    encumbrance = part_data["Обременения"]
                    self.restrictions_tab.insertRow(row)
                    self.restrictions_tab.setItem(row, 0, QTableWidgetItem(str(part_number)))
                    self.restrictions_tab.setItem(row, 1, QTableWidgetItem(encumbrance.get("Вид обременения", "")))
                    self.restrictions_tab.setItem(row, 2, QTableWidgetItem(encumbrance.get("Код вида обременения", "")))
                    self.restrictions_tab.setItem(row, 3, QTableWidgetItem(encumbrance.get("Действует с", "")))
                    self.restrictions_tab.setItem(row, 4, QTableWidgetItem(encumbrance.get("Срок действия", "")))
                    self.restrictions_tab.setItem(row, 5, QTableWidgetItem(encumbrance.get("Содержание ограничения", "")))
                    row += 1
    
    def export_main_parcel(self):
        """Экспорт основного контура участка"""
        if not self.parcel_data:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные основного контура", "", "CSV files (*.csv)"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Параметр;Значение\n")
                for key, value in self.parcel_data.items():
                    f.write(f"{key};{value if value else ''}\n")
    
    def export_parts(self):
        """Экспорт данных о частях участка"""
        if not self.parcel_obj_parts_dict:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные частей участка", "", "CSV files (*.csv)"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Номер части;Площадь;Погрешность;Примечание;Вид обременения;Код обременения;Действует с;Срок действия\n")
                for part_number, parts_list in self.parcel_obj_parts_dict.items():
                    for part_data in parts_list:
                        encumbrance = part_data.get("Обременения", {})
                        f.write(f"{part_number};{part_data.get('Площадь', '')};{part_data.get('Погрешность площади', '')};"
                               f"{part_data.get('Примечание', '')};{encumbrance.get('Вид обременения', '')};"
                               f"{encumbrance.get('Код вида обременения', '')};{encumbrance.get('Действует с', '')};"
                               f"{encumbrance.get('Срок действия', '')}\n")
    
    def add_main_layer_to_project(self):
        """Добавляет слой основного контура в проект QGIS"""
        if not self.parcel_location_geom or self.parcel_location_geom.isEmpty():
            QMessageBox.warning(self, "Предупреждение", "Нет данных основного контура для добавления в проект")
            return
        
        # Создаем слой для основного контура участка
        main_layer = QgsVectorLayer("MultiPolygon?crs=" + QgsProject.instance().crs().authid(), "Земельный участок", "memory")
        main_provider = main_layer.dataProvider()
        
        # Добавляем поля атрибутов
        main_provider.addAttributes([
            QgsField("Кадастровый номер", QVariant.String),
            QgsField("Номер кадастрового квартала", QVariant.String),
            QgsField("Категория земель", QVariant.String),
            QgsField("Площадь", QVariant.String),
            QgsField("Номер ЕГРН", QVariant.String)
        ])
        main_layer.updateFields()
        
        # Создаем объект для основного участка
        feature = QgsFeature()
        feature.setGeometry(self.parcel_location_geom)
        feature.setAttributes([
            self.parcel_data.get("Кадастровый номер", ""),
            self.parcel_data.get("Номер кадастрового квартала", ""),
            self.parcel_data.get("Категория земель", ""),
            self.parcel_data.get("Общая площадь", ""),
            self.parcel_data.get("Номер ЕГРН", "")
        ])
        
        main_provider.addFeature(feature)
        main_layer.updateExtents()
        
        # Добавляем слой в проект
        QgsProject.instance().addMapLayer(main_layer)
        QMessageBox.information(self, "Успех", "Слой основного контура добавлен в проект")
    
    def add_parts_layer_to_project(self):
        """Добавляет слой частей участка в проект QGIS"""
        if not self.parcel_obj_parts_dict:
            QMessageBox.warning(self, "Предупреждение", "Нет данных частей участка для добавления в проект")
            return
        
        # Создаем слой для частей участка
        parts_layer = QgsVectorLayer("MultiPolygon?crs=" + QgsProject.instance().crs().authid(), "Части участка", "memory")
        parts_provider = parts_layer.dataProvider()
        
        parts_provider.addAttributes([
            QgsField("Номер части", QVariant.String),
            QgsField("Площадь", QVariant.String),
            QgsField("Примечание", QVariant.String)
        ])
        parts_layer.updateFields()
        
        features_added = 0
        for part_number, parts_list in self.parcel_obj_parts_dict.items():
            for part_data in parts_list:
                if "geom" in part_data and part_data["geom"] and not part_data["geom"].isEmpty():
                    feature = QgsFeature()
                    feature.setGeometry(part_data["geom"])
                    feature.setAttributes([
                        str(part_number),
                        part_data.get("Площадь", ""),
                        part_data.get("Примечание", "")
                    ])
                    parts_provider.addFeature(feature)
                    features_added += 1
        
        if features_added > 0:
            parts_layer.updateExtents()
            QgsProject.instance().addMapLayer(parts_layer)
            QMessageBox.information(self, "Успех", f"Слой частей участка добавлен в проект ({features_added} объектов)")
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет геометрий частей участка для отображения")
    
    def add_all_layers_to_project(self):
        """Добавляет все доступные слои в проект"""
        self.add_main_layer_to_project()
        self.add_parts_layer_to_project()

# Для использования в QGIS
dialog = LandParcelProcessorDialog()
dialog.show()