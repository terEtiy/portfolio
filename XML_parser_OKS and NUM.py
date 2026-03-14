# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QTableWidget, QTableWidgetItem, 
                                QComboBox, QCheckBox, QLineEdit, QMessageBox,
                                QHeaderView, QGroupBox, QFileDialog, QTabWidget,
                                QTextEdit, QProgressDialog)
from qgis.PyQt.QtCore import Qt, QVariant, QSettings
from qgis.core import (QgsProject, QgsVectorLayer, QgsField, QgsFeature, 
                      QgsGeometry, QgsPointXY, QgsFields, QgsWkbTypes)
from qgis.PyQt.QtGui import QColor
from xml.dom import minidom
import os
import csv

class UnifiedOKSManagerDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление ОКС: парсинг XML и нумерация объектов")
        self.setMinimumSize(1200, 800)
        
        # Данные для нумерации
        self.current_layer = None
        self.features_data = []
        self.filtered_features = []
        self.custom_order = []
        
        # Данные для парсинга XML
        self.index = 0
        self.index_construction = 0
        self.index_ONS = 0
        self.index_Room = 0
        self.resultArray = []
        self.resultnotCor = []
        
        self.initUI()
        self.load_layers()
        
    def initUI(self):
        # Создаем вкладки для разделения функционала
        self.tabs = QTabWidget()
        
        # Вкладка 1: Парсинг XML
        self.xml_tab = self.create_xml_tab()
        self.tabs.addTab(self.xml_tab, "Парсинг XML ОКС")
        
        # Вкладка 2: Нумерация объектов
        self.numbering_tab = self.create_numbering_tab()
        self.tabs.addTab(self.numbering_tab, "Нумерация объектов")
        
        # Основной лейаут
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def create_xml_tab(self):
        """Создает вкладку для парсинга XML"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки загрузки файлов
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Выбрать XML файлы ОКС")
        self.load_btn.clicked.connect(self.load_xml_files)
        btn_layout.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("Экспорт координат")
        self.export_btn.clicked.connect(self.export_coordinates)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)
        
        self.export_no_coords_btn = QPushButton("Экспорт без координат")
        self.export_no_coords_btn.clicked.connect(self.export_no_coordinates)
        self.export_no_coords_btn.setEnabled(False)
        btn_layout.addWidget(self.export_no_coords_btn)
        
        layout.addLayout(btn_layout)
        
        # Таблица для отображения результатов парсинга
        self.xml_table = QTableWidget()
        self.xml_table.setColumnCount(12)
        self.xml_table.setHorizontalHeaderLabels([
            "Включить", "№", "CadNum", "Address", "Purpose", "CheckResult", 
            "Тип объекта", "Статус", "Площадь", "Дата", "Файл", "Координаты"
        ])
        
        # Настройка ширины столбцов
        header = self.xml_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        header.setSectionResizeMode(7, QHeaderView.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.xml_table)
        
        # Кнопка создания слоя из результатов парсинга
        btn_bottom_layout = QHBoxLayout()
        
        self.create_layer_btn = QPushButton("Создать слой из результатов")
        self.create_layer_btn.clicked.connect(self.create_layer_from_xml)
        self.create_layer_btn.setEnabled(False)
        btn_bottom_layout.addWidget(self.create_layer_btn)
        
        btn_bottom_layout.addStretch()
        
        self.switch_to_numbering_btn = QPushButton("Перейти к нумерации →")
        self.switch_to_numbering_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        btn_bottom_layout.addWidget(self.switch_to_numbering_btn)
        
        layout.addLayout(btn_bottom_layout)
        
        widget.setLayout(layout)
        return widget
        
    def create_numbering_tab(self):
        """Создает вкладку для нумерации объектов"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Выбор слоя
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Выберите точечный слой:"))
        self.layer_combo = QComboBox()
        self.layer_combo.currentTextChanged.connect(self.layer_changed)
        layer_layout.addWidget(self.layer_combo)
        
        self.refresh_btn = QPushButton("Обновить список слоев")
        self.refresh_btn.clicked.connect(self.load_layers)
        layer_layout.addWidget(self.refresh_btn)
        
        self.switch_to_xml_btn = QPushButton("← Вернуться к парсингу")
        self.switch_to_xml_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        layer_layout.addWidget(self.switch_to_xml_btn)
        
        layout.addLayout(layer_layout)
        
        # Режимы нумерации
        mode_group = QGroupBox("Режим нумерации")
        mode_layout = QHBoxLayout()
        
        self.sequential_radio = QCheckBox("Сквозная нумерация")
        self.sequential_radio.setChecked(True)
        self.sequential_radio.toggled.connect(self.update_numbering)
        mode_layout.addWidget(self.sequential_radio)
        
        self.custom_radio = QCheckBox("Нумерация по списку")
        self.custom_radio.toggled.connect(self.toggle_custom_input)
        mode_layout.addWidget(self.custom_radio)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Введите CadNum через запятую: 77:02:0018011:1321, 77:02:0018011:1185, ...")
        self.custom_input.textChanged.connect(self.update_custom_order)
        self.custom_input.setEnabled(False)
        mode_layout.addWidget(self.custom_input)
        
        self.load_list_btn = QPushButton("Загрузить из файла")
        self.load_list_btn.clicked.connect(self.load_custom_list)
        self.load_list_btn.setEnabled(False)
        mode_layout.addWidget(self.load_list_btn)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Статистика
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Всего объектов: 0 | Пронумеровано: 0 | Исключено: 0 | Не найдено в списке: 0")
        stats_layout.addWidget(self.stats_label)
        
        self.apply_btn = QPushButton("Применить нумерацию к слою")
        self.apply_btn.clicked.connect(self.apply_numbering)
        self.apply_btn.setEnabled(False)
        stats_layout.addWidget(self.apply_btn)
        
        layout.addLayout(stats_layout)
        
        # Таблица объектов
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Включить", "№", "CadNum", "Адрес", "Тип", "Статус", "ID", "Геометрия"
        ])
        
        # Настройка поведения столбцов
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.table.setSortingEnabled(True)
        self.table.itemChanged.connect(self.table_item_changed)
        layout.addWidget(self.table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Выделить все")
        self.select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Снять выделение")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)
        
        self.invert_selection_btn = QPushButton("Инвертировать выделение")
        self.invert_selection_btn.clicked.connect(self.invert_selection)
        btn_layout.addWidget(self.invert_selection_btn)
        
        btn_layout.addStretch()
        
        self.export_btn = QPushButton("Экспорт списка")
        self.export_btn.clicked.connect(self.export_list)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    # ==================== XML ПАРСИНГ ====================
    
    def load_xml_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите XML файлы ОКС", "", "XML files (*.xml)"
        )
        
        if files:
            # Показываем прогресс-диалог
            progress = QProgressDialog("Обработка XML файлов...", "Отмена", 0, len(files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            self.process_xml_files(files, progress)
            
            progress.close()
            
            if self.resultArray:
                self.export_btn.setEnabled(True)
                self.export_no_coords_btn.setEnabled(True)
                self.create_layer_btn.setEnabled(True)
                self.populate_xml_table()
    
    def process_xml_files(self, files, progress):
        """Обрабатывает список XML файлов"""
        self.xml_table.setRowCount(0)
        self.resultArray = []
        self.resultnotCor = []
        
        for i, file in enumerate(files):
            progress.setValue(i)
            progress.setLabelText(f"Обработка файла {i+1}/{len(files)}: {os.path.basename(file)}")
            
            if progress.wasCanceled():
                break
                
            try:
                dom = minidom.parse(file)
                self.process_xml_document(dom, os.path.basename(file))
            except Exception as e:
                print(f"Ошибка обработки файла {file}: {str(e)}")
    
    def process_xml_document(self, xml, filename):
        """Обрабатывает один XML документ"""
        # Обработка зданий
        build_records = xml.getElementsByTagName("build_record")
        for record in build_records:
            self.process_building_record(record, xml, filename, "Здание")
        
        # Обработка сооружений
        construction_records = xml.getElementsByTagName("construction_record")
        for record in construction_records:
            self.process_construction_record(record, xml, filename, "Сооружение")
        
        # Обработка ОНС
        ONS_records = xml.getElementsByTagName("object_under_construction_record")
        for record in ONS_records:
            self.process_ONS_record(record, xml, filename, "ОНС")
        
        # Обработка помещений
        Room_records = xml.getElementsByTagName("extract_about_property_room")
        for record in Room_records:
            self.process_room_record(record, xml, filename, "Помещение")
    
    def process_building_record(self, record, xml, filename, obj_type):
        """Обрабатывает запись о здании"""
        cadNum = self.get_text_content(record, "cad_number", "common_data")
        regNum = self.get_text_content(xml, "registration_number", "group_top_requisites")
        date = self.get_text_content(xml, "date_formation", "group_top_requisites")
        address = self.get_text_content(record, "readable_address", "address")
        area = self.get_text_content(record, "area", "params")
        purpose = self.get_text_content(record, "value", "purpose")
        floors = self.get_text_content(record, "floors", "params")
        unfloors = self.get_text_content(record, "underground_floors", "params")
        material = self.get_text_content(record, "material", "params")
        year = self.get_text_content(record, "year_commisioning", "params")
        yearbuild = self.get_text_content(record, "year_built", "params")
        name = self.get_text_content(record, "name", "params")
        status = self.get_text_content(xml, "status", "extract_about_property_build")
        
        # Извлекаем координаты
        coordinates = self.extract_coordinates(record, "build_record")
        centroid = self.calculate_centroid(coordinates) if coordinates else None
        wkt = self.wkt_generate(coordinates) if coordinates else ""
        project = QgsProject.instance()
        task_guid = project.customVariables().get('GPZUTaskGuid')

        # Формируем данные в формате для нумерации
        feature_data = {
            'feature_id': len(self.resultArray),
            'included': True,
            'CadNum': cadNum,
            'Address': address,
            'Purpose': purpose,
            'CheckResult': 2 if 'снят' in str(status).lower() else (1 if centroid is not None else 3),
            'type': obj_type,
            'status': status,
            'fid': len(self.resultArray),
            'wkt_geom': wkt,
            'geometry': centroid,
            'area': area if area else None,
            'date': date,
            'filename': filename,
            'has_coordinates': centroid is not None,
            'TaskGUID': task_guid
        }
        
        if centroid:
            feature_data['x'] = centroid['x']
            feature_data['y'] = centroid['y']
            self.resultArray.append(feature_data)
        else:
            self.resultnotCor.append({
                'cad_number': cadNum,
                'address': address,
                'reason': 'Нет координат'
            })
    
    def process_construction_record(self, record, xml, filename, obj_type):
        """Обрабатывает запись о сооружении"""
        cadNum = self.get_text_content(record, "cad_number", "common_data")
        regNum = self.get_text_content(xml, "registration_number", "group_top_requisites")
        date = self.get_text_content(xml, "date_formation", "group_top_requisites")
        address = self.get_text_content(record, "readable_address", "address")
        area = self.get_text_content(record, "area", "params")
        area_zasrt = self.get_text_content(record, "built_up_area", "params")
        purpose = self.get_text_content(record, "purpose", "params")
        name = self.get_text_content(record, "name", "params")
        status = f"{self.get_text_content(xml, 'status', 'extract_about_property_construction')} {obj_type}"
        
        # Извлекаем координаты
        coordinates = self.extract_coordinates(record, "construction_record")
        centroid = self.calculate_centroid(coordinates) if coordinates else None
        wkt = self.wkt_generate(coordinates) if coordinates else ""
        project = QgsProject.instance()
        task_guid = project.customVariables().get('GPZUTaskGuid')

        # Формируем данные в формате для нумерации
        feature_data = {
            'feature_id': len(self.resultArray),
            'included': True,
            'CadNum': cadNum,
            'Address': address,
            'Purpose': purpose,
            'CheckResult': 2 if 'снят' in str(status).lower() else 1,
            'type': obj_type,
            'status': status,
            'fid': len(self.resultArray),
            'wkt_geom': wkt,
            'geometry': centroid,
            'area': area if area else None,
            'date': date,
            'filename': filename,
            'has_coordinates': centroid is not None,
            'TaskGUID': task_guid
        }
        
        if centroid:
            feature_data['x'] = centroid['x']
            feature_data['y'] = centroid['y']
            self.resultArray.append(feature_data)
        else:
            self.resultnotCor.append({
                'cad_number': cadNum,
                'address': address,
                'reason': 'Нет координат'
            })
    
    def process_ONS_record(self, record, xml, filename, obj_type):
        """Обрабатывает запись об ОНС"""
        cadNum = self.get_text_content(record, "cad_number", "common_data")
        address = self.get_text_content(record, "readable_address", "address")
        purpose = self.get_text_content(record, "value", "purpose")
        status = self.get_text_content(xml, "status", "extract_about_property_under_construction")
        project = QgsProject.instance()
        task_guid = project.customVariables().get('GPZUTaskGuid')

        # ОНС обычно не имеют координат в выписках
        feature_data = {
            'feature_id': len(self.resultArray),
            'included': True,
            'CadNum': cadNum,
            'Address': address,
            'Purpose': purpose,
            'CheckResult': 2 if 'снят' in str(status).lower() else 1,
            'type': obj_type,
            'status': status,
            'fid': len(self.resultArray),
            'wkt_geom': '',
            'geometry': None,
            'area': '',
            'date': '',
            'filename': filename,
            'has_coordinates': False,
            'TaskGUID': task_guid
        }
        
        self.resultArray.append(feature_data)
    
    def process_room_record(self, record, xml, filename, obj_type):
        """Обрабатывает запись о помещении"""
        cadNum = self.get_text_content(record, "cad_number", "common_data")
        address = self.get_text_content(record, "readable_address", "address")
        purpose = self.get_text_content(record, "value", "purpose")
        project = QgsProject.instance()
        task_guid = project.customVariables().get('GPZUTaskGuid')

        feature_data = {
            'feature_id': len(self.resultArray),
            'included': True,
            'CadNum': cadNum,
            'Address': address,
            'Purpose': purpose,
            'CheckResult': 2,
            'type': obj_type,
            'status': 'Помещение',
            'fid': len(self.resultArray),
            'wkt_geom': '',
            'geometry': None,
            'area': '',
            'date': '',
            'filename': filename,
            'has_coordinates': False,
            'TaskGUID': task_guid
        }
        
        self.resultArray.append(feature_data)
    
    def populate_xml_table(self):
        """Заполняет таблицу результатами парсинга XML"""
        self.xml_table.setRowCount(len(self.resultArray))
        
        for row, feature_data in enumerate(self.resultArray):
            # Чекбокс включения
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Checked if feature_data['included'] else Qt.Unchecked)
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.xml_table.setItem(row, 0, checkbox_item)
            
            # Номер
            number_item = QTableWidgetItem(str(row + 1))
            self.xml_table.setItem(row, 1, number_item)
            
            # CadNum
            cad_num_item = QTableWidgetItem(str(feature_data['CadNum']))
            self.xml_table.setItem(row, 2, cad_num_item)
            
            # Address
            address_item = QTableWidgetItem(str(feature_data['Address']))
            self.xml_table.setItem(row, 3, address_item)
            
            # Purpose
            purpose_item = QTableWidgetItem(str(feature_data['Purpose']))
            self.xml_table.setItem(row, 4, purpose_item)
            
            # CheckResult
            status_item = QTableWidgetItem(str(feature_data['CheckResult']))
            self.xml_table.setItem(row, 5, status_item)
            
            # Тип объекта
            type_item = QTableWidgetItem(str(feature_data['type']))
            self.xml_table.setItem(row, 6, type_item)
            
            # Статус
            status_full_item = QTableWidgetItem(str(feature_data['status']))
            self.xml_table.setItem(row, 7, status_full_item)
            
            # Площадь
            area_item = QTableWidgetItem(str(feature_data['area']))
            self.xml_table.setItem(row, 8, area_item)
            
            # Дата
            date_item = QTableWidgetItem(str(feature_data['date']))
            self.xml_table.setItem(row, 9, date_item)
            
            # Файл
            file_item = QTableWidgetItem(str(feature_data['filename']))
            self.xml_table.setItem(row, 10, file_item)
            
            # Координаты
            coords_item = QTableWidgetItem("Есть" if feature_data['has_coordinates'] else "Нет")
            self.xml_table.setItem(row, 11, coords_item)
            
            # Подсветка строк без координат
            if not feature_data['has_coordinates']:
                for col in range(self.xml_table.columnCount()):
                    self.xml_table.item(row, col).setBackground(QColor(255, 230, 230))
    
    def create_layer_from_xml(self):
        """Создает векторный слой из результатов парсинга XML"""
        if not self.resultArray:
            QMessageBox.warning(self, "Ошибка", "Нет данных для создания слоя")
            return
        
        # Фильтруем только объекты с координатами
        features_with_coords = [f for f in self.resultArray if f['has_coordinates']]
        
        if not features_with_coords:
            QMessageBox.warning(self, "Ошибка", "Нет объектов с координатами для создания слоя")
            return
        
        # Создаем слой точек
        fields = QgsFields()
        fields.append(QgsField("fid", QVariant.Int))
        fields.append(QgsField("CadNum", QVariant.String))
        fields.append(QgsField("Address", QVariant.String))
        fields.append(QgsField("Purpose", QVariant.String))
        fields.append(QgsField("CheckResult", QVariant.String))
        fields.append(QgsField("Number", QVariant.Int))
        fields.append(QgsField("wkt_geom", QVariant.String))
        fields.append(QgsField("type", QVariant.String))
        fields.append(QgsField("area", QVariant.String))
        fields.append(QgsField("date", QVariant.String))
        fields.append(QgsField("filename", QVariant.String))
        fields.append(QgsField("TaskGUID", QVariant.String))

        project_crs = QgsProject.instance().crs()
        layer_name = "ОКС из XML"
        
        # Проверяем, не существует ли уже слой с таким именем
        existing_layers = QgsProject.instance().mapLayersByName(layer_name)
        if existing_layers:
            layer_name = f"{layer_name}_{len(existing_layers)}"
        
        layer = QgsVectorLayer(f"Point?crs={project_crs.authid()}", layer_name, "memory")
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()
        
        # Добавляем объекты
        for feature_data in features_with_coords:
            feat = QgsFeature()
            feat.setFields(fields)
            
            feat.setAttribute("fid", feature_data['fid'])
            feat.setAttribute("CadNum", feature_data['CadNum'])
            feat.setAttribute("Address", feature_data['Address'])
            feat.setAttribute("Purpose", feature_data['Purpose'])
            feat.setAttribute("CheckResult", feature_data['CheckResult'])
            feat.setAttribute("Number", 0)  # Начальное значение, будет заполнено при нумерации
            feat.setAttribute("wkt_geom", feature_data['wkt_geom'])
            feat.setAttribute("type", feature_data['type'])
            feat.setAttribute("area", feature_data['area'])
            feat.setAttribute("date", feature_data['date'])
            feat.setAttribute("filename", feature_data['filename'])
            feat.setAttribute("TaskGUID", feature_data['TaskGUID'])

            # Создаем точку (обратите внимание на порядок координат!)
            # Предполагаем, что в feature_data['x'] - восток, ['y'] - север
            point = QgsPointXY(feature_data['y'], feature_data['x'])
            feat.setGeometry(QgsGeometry.fromPointXY(point))
            
            layer.dataProvider().addFeature(feat)
        
        # Добавляем слой в проект
        QgsProject.instance().addMapLayer(layer)
        
        # Обновляем список слоев в комбобоксе
        self.load_layers()
        
        # Выбираем созданный слой
        index = self.layer_combo.findText(layer_name)
        if index >= 0:
            self.layer_combo.setCurrentIndex(index)
        
        # Переключаемся на вкладку нумерации
        self.tabs.setCurrentIndex(1)
        
        QMessageBox.information(self, "Успех", 
                               f"Слой '{layer_name}' создан и добавлен в проект.\n"
                               f"Добавлено объектов: {len(features_with_coords)}\n"
                               f"Объектов без координат: {len(self.resultArray) - len(features_with_coords)}")
    
    # ==================== НУМЕРАЦИЯ ====================
    
    def load_layers(self):
        """Загружает список векторных слоев проекта"""
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        
        point_layers = []
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                # Берем все векторные слои (можно фильтровать только точечные)
                point_layers.append(layer)
        
        for layer in point_layers:
            self.layer_combo.addItem(layer.name(), layer)
    
    def layer_changed(self, layer_name):
        """Обработчик изменения выбранного слоя"""
        if not layer_name:
            return
            
        layer = self.layer_combo.currentData()
        if layer and isinstance(layer, QgsVectorLayer):
            self.current_layer = layer
            self.load_layer_data()
            self.apply_btn.setEnabled(True)
        else:
            self.current_layer = None
            self.apply_btn.setEnabled(False)
    
    def load_layer_data(self):
        """Загружает данные из выбранного слоя"""
        if not self.current_layer:
            return
            
        self.features_data = []
        self.filtered_features = []
        
        # Получаем все поля слоя
        field_names = [field.name() for field in self.current_layer.fields()]
        
        for feature in self.current_layer.getFeatures():
            # Собираем данные, проверяя наличие полей
            feature_data = {
                'feature_id': feature.id(),
                'included': True,
                'CadNum': feature.attribute('CadNum') if 'CadNum' in field_names else '',
                'Address': feature.attribute('Address') if 'Address' in field_names else '',
                'type': feature.attribute('Purpose') if 'Purpose' in field_names else '',
                'status': feature.attribute('CheckResult') if 'CheckResult' in field_names else '',
                'id': feature.attribute('fid') if 'fid' in field_names else '',
                'wkt_geom': feature.attribute('wkt_geom') if 'wkt_geom' in field_names else '',
                'geometry': feature.geometry(),
                'original_feature': feature  # Сохраняем ссылку на оригинальный объект
            }
            
            # Добавляем дополнительные поля, если они есть
            for field in ['area', 'date', 'filename']:
                if field in field_names:
                    feature_data[field] = feature.attribute(field)
            
            self.features_data.append(feature_data)
            self.filtered_features.append(feature_data)
        
        self.populate_table()
        self.update_numbering()
    
    def populate_table(self):
        """Заполняет таблицу данными объектов"""
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        
        self.table.setRowCount(len(self.filtered_features))
        
        for row, feature_data in enumerate(self.filtered_features):
            # Сохраняем feature_id в UserRole для корректной работы при сортировке
            feature_id = feature_data.get('feature_id', row)
            
            # Чекбокс включения
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Checked if feature_data['included'] else Qt.Unchecked)
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setData(Qt.UserRole, feature_id)
            self.table.setItem(row, 0, checkbox_item)
            
            # Номер (будет заполнен позже)
            number_item = QTableWidgetItem("")
            number_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, number_item)
            
            # CadNum
            cad_num_item = QTableWidgetItem(str(feature_data['CadNum']))
            cad_num_item.setFlags(Qt.ItemIsEnabled)
            cad_num_item.setData(Qt.UserRole, feature_id)
            self.table.setItem(row, 2, cad_num_item)
            
            # Адрес
            address_item = QTableWidgetItem(str(feature_data['Address']))
            address_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 3, address_item)
            
            # Тип
            type_item = QTableWidgetItem(str(feature_data['type']))
            type_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 4, type_item)
            
            # Статус
            status_item = QTableWidgetItem(str(feature_data['status']))
            status_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 5, status_item)
            
            # ID
            id_item = QTableWidgetItem(str(feature_data.get('id', '')))
            id_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 6, id_item)
            
            # Геометрия
            wkt_text = str(feature_data.get('wkt_geom', ''))
            wkt_display = wkt_text[:50] + "..." if len(wkt_text) > 50 else wkt_text
            wkt_item = QTableWidgetItem(wkt_display)
            wkt_item.setFlags(Qt.ItemIsEnabled)
            wkt_item.setData(Qt.UserRole, feature_id)
            self.table.setItem(row, 7, wkt_item)
        
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.update_stats()
    
    # Остальные методы для нумерации (table_item_changed, update_numbering, и т.д.)
    # остаются практически такими же, как в оригинальном скрипте,
    # но с использованием feature_id из UserRole
    
    def table_item_changed(self, item):
        """Обработчик изменения элементов таблицы"""
        if item.column() == 0:  # Изменен чекбокс включения
            feature_id = item.data(Qt.UserRole)
            
            # Находим объект по feature_id
            for feature in self.filtered_features:
                if feature.get('feature_id') == feature_id:
                    feature['included'] = (item.checkState() == Qt.Checked)
                    break
            
            self.update_numbering()
    
    def get_original_index(self, sorted_row):
        """Получает исходный индекс элемента с учетом сортировки таблицы"""
        item = self.table.item(sorted_row, 2)  # Берем CadNum столбец
        if not item:
            return None
        
        feature_id = item.data(Qt.UserRole)
        
        # Ищем по feature_id
        for i, feature in enumerate(self.filtered_features):
            if feature.get('feature_id') == feature_id:
                return i
        return None
    
    def toggle_custom_input(self, enabled):
        """Включение/выключение поля для пользовательского списка"""
        self.custom_input.setEnabled(enabled)
        self.load_list_btn.setEnabled(enabled)
        if enabled:
            self.update_custom_order()
        else:
            for feature in self.filtered_features:
                feature['included'] = True
            self.populate_table()
            self.update_numbering()
    
    def update_custom_order(self):
        """Обновление пользовательского порядка из текстового поля"""
        custom_text = self.custom_input.text().strip()
        if custom_text:
            # Разделяем разными разделителями
            import re
            self.custom_order = re.split(r'[,;\n]', custom_text)
            self.custom_order = [num.strip() for num in self.custom_order if num.strip()]
            
            for feature in self.filtered_features:
                feature['included'] = (feature['CadNum'] in self.custom_order)
            
            self.populate_table()
            self.update_numbering()
        else:
            for feature in self.filtered_features:
                feature['included'] = True
            self.populate_table()
            self.update_numbering()
    
    def load_custom_list(self):
        """Загрузка пользовательского списка из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл со списком CadNum", "", 
            "Text files (*.txt);;CSV files (*.csv);;All files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    cad_nums = []
                    
                    if filename.endswith('.csv'):
                        # Читаем CSV
                        reader = csv.reader(f)
                        for row in reader:
                            if row:
                                cad_nums.append(row[0].strip())
                    else:
                        # TXT файл
                        cad_nums = [line.strip() for line in content.split('\n') if line.strip()]
                    
                    self.custom_input.setText(', '.join(cad_nums))
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def update_numbering(self):
        """Обновление нумерации в соответствии с выбранным режимом"""
        if not self.filtered_features:
            return
        
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        
        included_features = [f for f in self.filtered_features if f['included']]
        
        if self.custom_radio.isChecked() and self.custom_order:
            current_number = 1
            features_dict = {feature['CadNum']: feature for feature in included_features}
            
            for cad_num in self.custom_order:
                if cad_num in features_dict:
                    features_dict[cad_num]['current_number'] = current_number
                    current_number += 1
                else:
                    current_number += 1
        else:
            for i, feature in enumerate(included_features, 1):
                feature['current_number'] = i
        
        for row in range(self.table.rowCount()):
            original_index = self.get_original_index(row)
            if original_index is not None:
                feature_data = self.filtered_features[original_index]
                
                number_item = self.table.item(row, 1)
                if not number_item:
                    number_item = QTableWidgetItem()
                    self.table.setItem(row, 1, number_item)
                
                if feature_data['included'] and 'current_number' in feature_data:
                    number_item.setText(str(feature_data['current_number']))
                    number_item.setBackground(QColor(200, 255, 200))
                else:
                    number_item.setText("")
                    number_item.setBackground(QColor(255, 200, 200))
                
                checkbox_item = self.table.item(row, 0)
                if checkbox_item:
                    if feature_data['included']:
                        checkbox_item.setBackground(QColor(200, 255, 200))
                    else:
                        checkbox_item.setBackground(QColor(255, 200, 200))
        
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.update_stats()
    
    def update_stats(self):
        """Обновление статистики"""
        total = len(self.filtered_features)
        included = len([f for f in self.filtered_features if f['included']])
        excluded = total - included
        
        not_found_count = 0
        if self.custom_radio.isChecked() and self.custom_order:
            features_cad_nums = {f['CadNum'] for f in self.filtered_features}
            for cad_num in self.custom_order:
                if cad_num not in features_cad_nums:
                    not_found_count += 1
        
        self.stats_label.setText(
            f"Всего объектов: {total} | Пронумеровано: {included} | "
            f"Исключено: {excluded} | Не найдено в списке: {not_found_count}"
        )
    
    def select_all(self):
        """Выделить все объекты"""
        for feature in self.filtered_features:
            feature['included'] = True
        
        self.populate_table()
        self.update_numbering()
    
    def deselect_all(self):
        """Снять выделение со всех объектов"""
        for feature in self.filtered_features:
            feature['included'] = False
        
        self.populate_table()
        self.update_numbering()
    
    def invert_selection(self):
        """Инвертировать выделение"""
        for feature in self.filtered_features:
            feature['included'] = not feature['included']
        
        self.populate_table()
        self.update_numbering()
    
    def apply_numbering(self):
        """Применяет нумерацию к векторному слою"""
        if not self.current_layer:
            QMessageBox.warning(self, "Ошибка", "Слой не выбран")
            return
        
        # Проверяем наличие поля 'Number', создаем если нет
        fields = self.current_layer.fields()
        if fields.indexFromName('Number') == -1:
            self.current_layer.dataProvider().addAttributes([QgsField('Number', QVariant.Int)])
            self.current_layer.updateFields()
        
        # Применяем нумерацию
        self.current_layer.startEditing()
        
        for feature_data in self.features_data:
            feature = self.current_layer.getFeature(feature_data['feature_id'])
            if feature_data['included'] and 'current_number' in feature_data:
                feature['Number'] = feature_data['current_number']
            else:
                # Устанавливаем NULL для исключенных объектов
                feature.setAttribute('Number', QVariant())
            self.current_layer.updateFeature(feature)
        
        if self.current_layer.commitChanges():
            QMessageBox.information(self, "Успех", "Нумерация успешно применена к слою")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось применить нумерацию")
            self.current_layer.rollBack()
    
    def export_list(self):
        """Экспорт списка объектов с нумерацией"""
        if not self.filtered_features:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт списка", "", "CSV files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow([
                        "№", "CadNum", "Address", "Purpose", "CheckResult", 
                        "fid", "included", "type", "area", "date"
                    ])
                    
                    for feature in self.filtered_features:
                        number = feature.get('current_number', '')
                        included = "Да" if feature['included'] else "Нет"
                        writer.writerow([
                            number,
                            feature['CadNum'],
                            feature['Address'],
                            feature.get('type', ''),
                            feature.get('status', ''),
                            feature.get('id', ''),
                            included,
                            feature.get('type', ''),
                            feature.get('area', ''),
                            feature.get('date', '')
                        ])
                
                QMessageBox.information(self, "Успех", f"Список экспортирован в {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать список: {str(e)}")
    
    # ==================== XML ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def get_text_content(self, record, tag_name, parent_tag_name=None):
        """Извлекает текстовое содержимое из XML элемента"""
        try:
            if parent_tag_name:
                parent = record.getElementsByTagName(parent_tag_name)[0]
                element = parent.getElementsByTagName(tag_name)[0]
            else:
                element = record.getElementsByTagName(tag_name)[0]
            return element.firstChild.nodeValue if element.firstChild else ""
        except:
            return ""
    
    def extract_coordinates(self, record, record_type):
        """Извлекает координаты из XML записи"""
        try:
            contours = record.getElementsByTagName("contours")[0]
            contour = contours.getElementsByTagName("contour")[0]
            entity_spatial = contour.getElementsByTagName("entity_spatial")[0]
            
            # Проверка системы координат (можно ослабить)
            try:
                sk_id = entity_spatial.getElementsByTagName("sk_id")[0].firstChild.nodeValue
                # Принимаем любую систему координат, преобразование будет в QGIS
                # if sk_id not in ["ПМСК Москвы", "МСК Москвы"]:
                #     return None
            except:
                pass  # Пропускаем проверку, если нет информации о СК
            
            spatial_elements = entity_spatial.getElementsByTagName("spatials_elements")[0]
            spatial_element = spatial_elements.getElementsByTagName("spatial_element")[0]
            ordinates = spatial_element.getElementsByTagName("ordinates")[0]
            
            coordinates = []
            for ordinate in ordinates.getElementsByTagName("ordinate"):
                x = float(ordinate.getElementsByTagName("x")[0].firstChild.nodeValue)
                y = float(ordinate.getElementsByTagName("y")[0].firstChild.nodeValue)
                coordinates.append({'x': x, 'y': y})
            
            return coordinates
        except Exception as e:
            print(f"Ошибка извлечения координат: {str(e)}")
            return None
    
    def calculate_centroid(self, coordinates):
        """Вычисляет центроид полигона"""
        if not coordinates:
            return None
            
        sum_x = 0
        sum_y = 0
        count = 0
        
        for point in coordinates:
            sum_x += point['x']
            sum_y += point['y']
            count += 1
        
        if count == 0:
            return None
            
        return {'x': sum_x / count, 'y': sum_y / count}
    
    def wkt_generate(self, coordinates):
        """Генерирует WKT строку полигона"""
        if not coordinates:
            return ""
            
        wkt = "POLYGON (("
        points = []
        
        for point in coordinates:
            points.append(f"{point['x']} {point['y']}")
        
        if points[0] != points[-1]:
            points.append(points[0])
            
        wkt += ", ".join(points) + "))"
        return wkt
    
    def export_coordinates(self):
        """Экспорт координат в CSV"""
        if not self.resultArray:
            return
            
        features_with_coords = [f for f in self.resultArray if f['has_coordinates']]
        
        if not features_with_coords:
            QMessageBox.warning(self, "Ошибка", "Нет объектов с координатами для экспорта")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить координаты", "", "CSV files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow([
                        "cad_number", "x", "y", "address", "type", 
                        "status", "wktGeom", "purpose", "area", "date"
                    ])
                    
                    for item in features_with_coords:
                        writer.writerow([
                            item['CadNum'],
                            item.get('x', ''),
                            item.get('y', ''),
                            item['Address'],
                            item['type'],
                            item['CheckResult'],
                            item.get('wkt_geom', ''),
                            item.get('Purpose', ''),
                            item.get('area', ''),
                            item.get('date', '')
                        ])
                
                QMessageBox.information(self, "Успех", f"Координаты экспортированы в {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать координаты: {str(e)}")
    
    def export_no_coordinates(self):
        """Экспорт объектов без координат"""
        if not self.resultnotCor:
            QMessageBox.information(self, "Информация", "Нет объектов без координат")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные без координат", "", "CSV files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["cad_number", "address", "reason"])
                    
                    for item in self.resultnotCor:
                        writer.writerow([
                            item['cad_number'],
                            item['address'],
                            item.get('reason', 'Нет координат')
                        ])
                
                QMessageBox.information(self, "Успех", f"Данные экспортированы в {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать данные: {str(e)}")


# Для использования в QGIS
dialog = UnifiedOKSManagerDialog()
dialog.show()