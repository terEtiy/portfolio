# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gpzuTools
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

from PyQt5.QtCore import QSettings, QTranslator, Qt, QCoreApplication
from datetime import datetime
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QAction, QWidget, QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsVectorFileWriter, QgsAuthManager,\
    QgsAuthMethodConfig, QgsExpressionContextUtils, QgsProject, QgsRectangle,\
    QgsFeatureRequest, QgsExpression, QgsMessageLog, QgsApplication
from qgis.core import Qgis, QgsGeometry
import subprocess
import re
import time
# Initialize Qt resources from file resources.py
# This would typically be updated to:
# from .resources import *
# Import the code for the dialog
from .gpzu_tools_dialog import gpzuToolsDialog
import os.path
from .fields_mapper import FieldsMapper
from .layersDef import layersDef

class gpzuTools:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'gpzuTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&gpzu tools')
        self.toolbar = self.iface.addToolBar(u'gpzuTools')
        self.toolbar.setObjectName(u'gpzuTools')

        self.exportTables = ('gpzu.gpzu_frames', 'gpzu.gpzu', 'lgr.pnt', 'ctp.pnt', 'lgr.lin',
                             'ctp.lin', 'lgr.pol', 'ctp.pol', 'gpzu.gpzu_points', 'gpzu.gpzu_point_labels',
                             'ctp.pnt_2017', 'ctp.lin_2017', 'ctp.pol_2017')

        self.importTables = ('lgr.pnt', 'ctp.pnt', 'lgr.lin', 'ctp.lin', 'lgr.pol', 'ctp.pol',
                             'ctp.pnt_2017', 'ctp.lin_2017', 'ctp.pol_2017')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QApplication.translate('gpzuTools', message)

    def log(self, message, title, level=0):
        QgsMessageLog.logMessage(self.tr(message), title, level)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = gpzuToolsDialog()
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        for conn in self.getConnections():
            self.dlg.comboBox.addItem(conn)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_upload = ':/plugins/gpzuTools/upload.svg'
        icon_download = ':/plugins/gpzuTools/download.svg'
        icon_setup = ':/plugins/gpzuTools/setup.svg'
        icon_gispro = ':/plugins/gpzuTools/icon.png'
        self.add_action(
            icon_download,
            text=self.tr(u'Загрузить участок карты'),
            callback=self.gpzuExport,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_upload,
            text=self.tr(u'Импорт пакета геоданных'),
            callback=self.gpzuImport,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_setup,
            text=self.tr(u'Настроить чертеж'),
            callback=self.gpzuUpdateFilters,
            parent=self.iface.mainWindow())


#    def unload(self):
#        """Removes the plugin menu item and icon from QGIS GUI."""
#        for action in self.actions:
#            self.iface.removePluginMenu(
#                self.tr(u'&gpzu tools'),
#                action)
#            self.iface.removeToolBarIcon(action)
#        # remove the toolbar
#        del self.toolbar


    def writeToFile(self, layer, filename, layerName):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = layerName
        options.fileEncoding = 'utf-8'
        if os.path.exists(filename):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        return QgsVectorFileWriter.writeAsVectorFormat(layer, filename, options)


    def getPGLayer(self, uri, schema, sql, fltr, layerName):
        sql = re.sub("\s+|\n|\r|\s+$", ' ', sql)
        uri.setDataSource(schema, sql, "geom", fltr, "gid")
        return QgsVectorLayer(uri.uri(False), layerName, "postgres")

    def loadFromDB(self, table, gpzu_gid, scale, uri):
        sql = ''
        fltr = ''
        schema = ''
        if 'gpzu' in table:
            schema, sql = table.split('.')
            if sql == 'gpzu':
                fltr = "gid = {0}".format(gpzu_gid)
            else:
                fltr = "gpzu_gid = {0}".format(gpzu_gid)

        elif 'pnt' in table or 'lin' in table or 'pol' in table:
            sql = """(WITH knife AS (
                        SELECT st_union(geom) AS geom
                        FROM
                          gpzu.gpzu_frames
                        WHERE
                          gpzu_gid = {gid}
                          AND
                          scale = {scale}
                    )

                    SELECT
                        l.*
                    FROM
                        {table} l,
                        knife
                    WHERE
                        l.geom && knife.geom)""".format(gid=gpzu_gid, table=table, scale=scale)

        return self.getPGLayer(uri, schema, sql, fltr, table)


    def getDBCredentials(self, conn):
        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections/" + conn)
        PGDatabase = settings.value("database", "")
        PGHost = settings.value("host", "")
        PGUsername = settings.value("username", "")
        PGPassword = settings.value("password", "")
        PGPort = settings.value("port", "")
        PGService = settings.value("service", "")
        authcfg = settings.value("authcfg", "")

        #load user and password from authdb for QSqlDatabase
        if len(authcfg) > 0:
            config = QgsAuthMethodConfig()
            authm = QgsAuthManager.instance()
            method = authm.configAuthMethodKey(authcfg)
            if method == 'Basic':
                authm.loadAuthenticationConfig(authcfg, config, True)
                PGUsername = config.config('username')
                PGPassword = config.config('password')

            else:
                self.pushMessage('Error',
                                 "Метод аутентификации {} не поддерживается".format(method),
                                 QgsMessageBar.CRITICAL)
                self.log("Метод аутентификации {} не поддерживается".format(method), 'gpzu_tools error', 1)
                raise Exception("Not supported auth method: {}".format(method))
        settings.endGroup()
        return {'database': PGDatabase, 'host': PGHost, 'username': PGUsername, 'password': PGPassword,
                'port': PGPort, 'service': PGService, 'authcfg': authcfg}


    def getConnections(self):
        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections")
        currentConnections = settings.childGroups()
        settings.endGroup()
        return currentConnections

    def setPGUri(self, conn):
        uri = QgsDataSourceUri()
        uri.setConnection(conn['host'], conn['port'], conn['database'], conn['username'], conn['password'],
                          QgsDataSourceUri.SSLdisable, conn["authcfg"])
        return uri


    def getGpkgLayer(self, filename, table):
        uri = u"{0}|layername={1}".format(filename, table)
        return QgsVectorLayer(uri, table, "ogr")


    def setDBConn(self, conn):
        db = QSqlDatabase.addDatabase("QPSQL")
        db.setHostName(conn['host'])
        db.setDatabaseName(conn['database'])
        db.setUserName(conn['username'])
        db.setPassword(conn['password'])
        return db


    def addFeatures(self, dstLayer, features):
        dstLayer.startEditing()
        (res, f) = dstLayer.dataProvider().addFeatures(features)
        if res:
            dstLayer.commitChanges()
        elif not res and len(features) > 1:
            dstLayer.rollBack()
            half = int(len(features)/2)
            self.addFeatures(dstLayer, features[0:half])
            self.addFeatures(dstLayer, features[half:])
        else:
            self.log('Не удалось добавить запись в таблицу {table}\n'
                     'Атрибуты:{attrs}\n'
                     'Геометрия:{geom}'
                     .format(table=dstLayer.name(),
                             attrs=features[0].attributes(),
                             geom=features[0].geometry().exportToWkt()),
                     'gpzu_tools error', 1)
            dstLayer.rollBack()


    def loadToDB(self, srcLayer, uri, table):
        schema, table = table.split('.')
        fltr = ''
        dstLayer = self.getPGLayer(uri, schema, table, fltr, "{0}.{1}".format(schema, table))
        caps = dstLayer.dataProvider().capabilities()
        srcFields = [field.name() for field in srcLayer.dataProvider().fields()]
        mapping = []
        for field in dstLayer.dataProvider().fields():
            layerDef = {'name': field.name(), 'type': field.type(),
                        'length': field.length(), 'precision': field.precision(),
                        'expression': field.name()}
            if field.name() not in srcFields:
                layerDef['expression'] = 'Null'
            mapping.append(layerDef)
        try:
            mLayer = FieldsMapper().exec_(srcLayer, mapping)
        except:
            return
        mLayer.setName('{}.{}'.format(schema, table))
        features = [feature for feature in mLayer.getFeatures()]
        self.addFeatures(dstLayer, features)


    def pushMessage(self, title, message, messageLevel=Qgis.Info):
        self.iface.messageBar().clearWidgets()
        self.iface.messageBar().pushMessage(self.tr(title), self.tr(message),
                                            level=messageLevel)


    def initProgressBar(self, max):
        self.iface.messageBar().clearWidgets()
        progressMessageBar = self.iface.messageBar()
        progress = QProgressBar()
        progress.setMaximum(max)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.pushWidget(progress)
        return progress

    def prepareDBTable(self, db, table, extent):
        query = QSqlQuery(db)
        sql = """DELETE FROM
                    {table} p
                    WHERE
                      p.geom &&
                      st_makeenvelope(
                        {xmin},
                        {ymin},
                        {xmax},
                        {ymax},
                        900999);""".format(table=table, xmin=extent.xMinimum(), ymin=extent.yMinimum(),
                                           xmax=extent.xMaximum(), ymax=extent.yMaximum())
        #self.log(sql, 'gpzu_tools', 3)

        return query.exec_(sql)


    def prepareExp(self, template, exp):
        specialChars = ('\\', '.', '^', '$', '*', '+', '?', '{', '[', ']', '|', '(', ')')
        template = re.sub("\s+|\n|\r|\s+$", ' ', template).lower()
        for char in specialChars:
            template = template.replace(char, '\\' + char)
        template = template % exp
        template = template.replace(' ', '')
        return template



    def findLayer(self, layerName):
        layerList = QgsProject.instance().mapLayersByName(self.tr(layerName))
        if layerList:
            return layerList[0]
        else:
            layerList = []
            layerDef = layersDef[layerName]
            if layerDef['schema'] != '':
                filterExp = self.prepareExp(layerDef['filter'], layerDef['exp'])
                tableExp = layerDef['table']
            else:
                filterExp = layerDef['filter']
                tableExp = self.prepareExp(layerDef['table'], layerDef['exp'])
            for layer in QgsProject.instance().mapLayers().values():
                ds = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
                schema = ds.schema().lower()
                geomField = ds.geometryColumn().lower()
                filter = re.sub("\s+|\n|\r|\s+$", ' ', ds.sql())
                filter = filter.lower().replace(' ','')
                table = re.sub("\s+|\n|\r|\s+$", ' ', ds.table())
                table = table.lower().replace(' ', '').replace('((((', '').replace('))))', '')
                if layerDef['schema'] == schema and layerDef['geomField'] == geomField \
                    and re.match(filterExp, filter) and re.match(tableExp, table):
                    layerList.append(layer)
            if layerList:
                return layerList[0]
            else:
                self.pushMessage('Warning', "Слой '{}' не найден".format(layerName), QgsMessageBar.WARNING)
                self.log('Слой "{layer}" не найден\n'
                         'Схема: {schema}\n'
                         'Таблица: {table}\n'
                         'Поле геометрии: {geom}\n'
                         'Фильтр: {filter}'
                         .format(layer=layerName,
                                 schema=layerDef['schema'],
                                 table=tableExp,
                                 geom=layerDef['geomField'],
                                 filter=filterExp),
                         'gpzu_tools error', 1)

    def exportRaster(self, extent, outputFile):
        #gdalPath = QgsApplication.prefixPath() + '/bin'
        #gdal_translate = gdalPath + '/gdal_translate'
        # Обновите путь к gdal_translate в соответствии с версией QGIS 3
        gdal_translate = 'C:/PROGRA~1/QGIS3~1.18/bin/gdal_translate.exe'
        inputFile = '\\\\GISSRV3\\!Mosaic\\mosaic.vrt'
        translate = r'{gdal} -projwin {xMin} {yMax} {xMax} {yMin} {src} {dst} -of GPKG -co APPEND_SUBDATASET=YES ' \
                    r'-co RASTER_TABLE=ofp -a_srs "+proj=tmerc +lat_0=55.66666666667 +lon_0=37.5 +k=1 +x_0=12 ' \
                    r'+y_0=14 +ellps=bessel +towgs84=316.151,78.924,589.65,-1.57273,2.69209,2.34693,8.4507 ' \
                    r'+units=m +no_defs"'.format(gdal=gdal_translate,
                                                 xMin=extent.xMinimum(),
                                                 yMax=extent.yMaximum(),
                                                 xMax=extent.xMaximum(),
                                                 yMin=extent.yMinimum(),
                                                 src=inputFile,
                                                 dst=outputFile)
        self.log('Выполняется {cmd}'.format(cmd=translate), 'gpzu_tools')
        res = subprocess.call(translate)
        if res != 0:
            self.log('Возникла ошибка при выполнении {cmd}'.format(translate), 'gpzu_tools', 1)

    def gpzuExport(self):
        """export data from postgres to geopackage"""
        self.dlg.setWindowTitle(self.tr("Загрузить участок карты"))
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            conn = self.getDBCredentials(self.dlg.comboBox.currentText())
            pguri = self.setPGUri(conn)
            filename = self.dlg.selectFile(mode='save')
            if filename == None: return
            gid = self.dlg.lineEdit.text()
            scale = self.dlg.comboBox_2.currentText()

            progress = self.initProgressBar(len(self.exportTables))
            extent = None
            for table in self.exportTables:
                layer = self.loadFromDB(table, gid, scale, pguri)
                if table == "gpzu.gpzu_frames":
                    try:
                        next(layer.getFeatures())
                    except StopIteration:
                        self.log('Слой "{layer}" не содержит объектов'.format(layer=layer.name()), 'gpzu_tools error', 1)
                        raise ValueError('Object with gid {0} not found in db'.format(gid))

                    extent = layer.extent()

                self.writeToFile(layer, filename, layer.name())
                progress.setValue(self.exportTables.index(table) + 1)
                layer = None  # Recommended way to delete layer in QGIS 3

            if extent is not None:
                if self.dlg.checkBox.isChecked():
                    try:
                        self.exportRaster(extent, filename)
                    except:
                        self.log('Не удалось вырезать растр', 'gpzu_tools error', 1)
            else:
                self.log('Отсутствует экстент участка', 'gpzu_tools error', 1)

            self.pushMessage("INFO", "Участок карты загружен успешно")
            self.log("Участок карты загружен успешно", 'gpzu_tools')


    def gpzuImport(self):
        """import data from geopackage to postgres"""
        self.dlg.setWindowTitle(self.tr("Импорт пакета геоданных"))
        # show the dialog
        self.dlg.label.hide()
        self.dlg.checkBox.hide()
        self.dlg.lineEdit.hide()
        self.dlg.show()
        result = self.dlg.exec_()
        self.dlg.label.show()
        self.dlg.lineEdit.show()
        self.dlg.checkBox.show()
        if result:
            filename = self.dlg.selectFile()
            if filename == None: return
            scale = self.dlg.comboBox_2.currentText()
            conn = self.getDBCredentials(self.dlg.comboBox.currentText())
            pguri = self.setPGUri(conn)
            db = self.setDBConn(conn)
            ok = db.open()
            if not ok:
                self.pushMessage("Error", "Не удалось подключиться к базе данных", QgsMessageBar.CRITICAL)
                self.log("Не удалось подключиться к базе данных".format(), 'gpzu_tools error', 1)
                raise Exception("Database error: {0}".format(db.lastError().text()))

            progress = self.initProgressBar(len(self.importTables))
            frame = next(self.getGpkgLayer(filename, "gpzu.gpzu_frames").getFeatures())
            extent = frame.geometry().boundingBox()
            self.log('Рамка участка: {}'.format(extent.toString()), 'gpzu_tools')
            for table in self.importTables:
                layer = self.getGpkgLayer(filename, table)
                try:
                    next(layer.getFeatures())
                except StopIteration:
                    continue
                if layer.featureCount() <= 0:
                    self.log("Слой {} не содержит данных".format(table), 'gpzu_tools', 2)
                else:
                    self.log("Загрузка слоя {}".format(table), 'gpzu_tools', 0)
                    if not self.prepareDBTable(db, table, extent):
                        continue
                    self.loadToDB(layer, pguri, table)
                    progress.setValue(self.importTables.index(table))
            db.close()
            layer = None  # Recommended way to delete layer in QGIS 3
            self.pushMessage("Info", 'Загрузка данных в базу успешно завершена')
            self.log('Загрузка данных в базу успешно завершена', 'gpzu_tools')


    def updateFilter(self, layerName, values):
        if type(values) == tuple:
            values = tuple(map(str, values))
        else:
            values = str(values)
        try:
            filter = layersDef[layerName]['filter'] % values
        except:
            self.log('Ошибка при применении фильтра:\n'
                     'Слой: {layer}\n'
                     'Маска: {mask}\n'
                     'Значения: {val}'
                     .format(layer=layerName, mask=layersDef[layerName]['filter'], val=values),
                     'gpzu_tools error', 1)
            return 1
        layer = self.findLayer(layerName)
        if layer:
            layer.setSubsetString(filter)

    def updateSql(self, layerName, values):
        if type(values) == tuple:
            values = tuple(map(str, values))
        else:
            values = str(values)
        table = '(' + layersDef[layerName]['table'] % values + ')'
        layer = self.findLayer(layerName)
        if layer:
            ds = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
            ds.setDataSource(ds.schema(), table, ds.geometryColumn(), ds.sql(), ds.keyColumn())
            layer.setDataSource(ds.uri(False), layer.name(), layer.dataProvider().name(), QgsVectorLayer.LayerOptions())

    def getFeaturesSubset(self, layer, expressionString):
        request = QgsFeatureRequest(QgsExpression(expressionString))
        features = [f for f in layer.getFeatures(request)]
        return features

    def gpzuUpdateFilters(self):
        self.dlg.setWindowTitle(self.tr("Настройка чертежа"))
        self.dlg.label_2.hide()
        self.dlg.comboBox.hide()
        self.dlg.checkBox.hide()
        self.dlg.show()
        result = self.dlg.exec_()
        self.dlg.label_2.show()
        self.dlg.comboBox.show()
        self.dlg.checkBox.show()
        if result:
            scale = self.dlg.comboBox_2.currentText()
            gid = self.dlg.lineEdit.text()
            layers = {"Рамки карты макета": (scale, gid),
                     "Схема страниц": (scale, gid),
                     "Координаты поворотных точек": (scale, gid),
                     "Поворотные точки участка": gid,
                     "Границы земельного участка": gid,
                     "Границы земельного участка (маска)": gid,
                     "Части земельного участка": gid,
                     "Точки пересечений с территориальными подзонами": gid,
                     "Подписи объектов капитального строительства": gid,
                     "Территория объекта культурного наследия": gid,
                     "Подписи подзон": gid,
                     "Подписи индексов режимов подзон": gid,
                     "Подписи номеров регламентных участков": gid,
                     "Выноски - подпись части земельного участка": gid,
                     "Выноски подзоны": gid,
                     "Выноски сит. план": gid}
            for layer, values in layers.items():
                self.updateFilter(layer, values)

            #sqlLayers = {"Кадастровые участки на ситуационном плане": gid}
            #for layer, values in sqlLayers.items():
            #    self.updateSql(layer, values)


            # Получить текущую дату и время
            current_datetime = datetime.now()

            # Преобразовать дату и время в нужный формат
            current_datetime_str = current_datetime.strftime('%d-%m-%Y')
            
            project = QgsProject.instance()

            # Проверить, существуют ли переменные до установки значений
            print("Переменные до установки:")
            print("gpzu_id:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_id'))
            print("gpzu_date:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_date'))
            print("gpzu_scale:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_scale'))

            scale = self.dlg.comboBox_2.currentText()
            gid = self.dlg.lineEdit.text()
            
            variable_name1 = 'gpzu_date'
            variable_name2 = 'gpzu_id'
            variable_name3 = 'gpzu_scale'
            
            # Установить новое значение переменной проекта
            QgsExpressionContextUtils.setProjectVariable(project,variable_name2, gid)
            QgsExpressionContextUtils.setProjectVariable(project,variable_name1, current_datetime_str)
            QgsExpressionContextUtils.setProjectVariable(project,variable_name3, scale)

            # Проверить, были ли успешно установлены переменные
            print("Переменные после установки:")
            print("gpzu_id:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_id'))
            print("gpzu_date:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_date'))
            print("gpzu_scale:", QgsExpressionContextUtils.projectScope(project).hasVariable('gpzu_scale'))

            layer = QgsProject.instance().mapLayersByName("Схема страниц")[0]
            if layer:
                features = layer.getFeatures()
                feature = next(features)
                QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(),'page_count', feature.attribute('pages') * 4)

                if feature.attribute('pages') > 1:
                    extent = QgsGeometry().boundingBox()
                    for feature in features:
                        extent.combineExtentWith(feature.geometry().boundingBox())

                    QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'schema_list_xmin', extent.xMinimum())
                    QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'schema_list_ymin', extent.yMinimum())
                    QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'schema_list_xmax', extent.xMaximum())
                    QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'schema_list_ymax', extent.yMaximum())

            layer = self.findLayer("Границы земельного участка")
            if layer:
                if layer.featureCount() == 0:
                    doc_num = ''
                    self.log('отсутствуют объекты в слое "Границы земельного участка"\n', 'gpzu_tools', 2)
                else:
                    feature = next(layer.getFeatures())
                    doc_num = feature.attribute('doc_num')
                QgsExpressionContextUtils.setProjectVariable('doc_num', doc_num)

            self.pushMessage('Info', 'Чертёж настроен')
            self.log('Чертёж настроен', 'gpzu_tools')
