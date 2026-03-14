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

from qgis.core import (QgsField, QgsExpression, QgsExpressionContext, 
                       QgsExpressionContextUtils, QgsDistanceArea, QgsProject, 
                       QgsFeature, QgsVectorLayer, Qgis)
from qgis.utils import iface
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import QgsProcessingException

class FieldsMapper(QgisAlgorithm):

    def init(self):
        super().init()
        self.mapping = None
        self.geomTypes = {
            "Point": Qgis.WKBPoint, 
            "LineString": Qgis.WKBLineString,
            "Polygon": Qgis.WKBPolygon, 
            "MultiPoint": Qgis.WKBMultiPoint,
            "MultiLineString": Qgis.WKBMultiLineString,
            "MultiPolygon": Qgis.WKBMultiPolygon
        }

    def exec_(self, srcLayer, mapping):
        crs = srcLayer.crs().toWkt()
        geomTypeId = srcLayer.dataProvider().geometryType()
        geomType = [k for k, v in self.geomTypes.items() if v == geomTypeId][0]
        mLayer = QgsVectorLayer('{0}?crs={1}'.format(geomType, crs), 'tmp', 'memory')

        fields = []
        expressions = []

        da = QgsDistanceArea()
        da.setSourceCrs(srcLayer.crs())
        da.setEllipsoidalMode(iface.mapCanvas().mapSettings().hasCrsTransformEnabled())
        da.setEllipsoid(QgsProject.instance().ellipsoid())

        exp_context = QgsExpressionContext()
        exp_context.appendScope(QgsExpressionContextUtils.globalScope())
        exp_context.appendScope(QgsExpressionContextUtils.projectScope())
        exp_context.appendScope(QgsExpressionContextUtils.layerScope(srcLayer))

        for field_def in mapping:
            fields.append(QgsField(name=field_def['name'],
                                   type=field_def['type'],
                                   len=field_def['length'],
                                   prec=field_def['precision']))

            expression = QgsExpression(field_def['expression'])
            expression.setGeomCalculator(da)
            expression.setDistanceUnits(QgsProject.instance().distanceUnits())
            expression.setAreaUnits(QgsProject.instance().areaUnits())

            if expression.hasParserError():
                raise GeoAlgorithmExecutionException(
                    self.tr('Parser error in expression "{}": {}')
                    .format(field_def['expression'], expression.parserErrorString()))

            expression.prepare(exp_context)
            if expression.hasParserError():
                raise GeoAlgorithmExecutionException(
                    self.tr('Parser error in expression "{}": {}')
                    .format(field_def['expression'], expression.parserErrorString()))

            expressions.append(expression)

        mLayer.startEditing()
        mLayer.dataProvider().addAttributes(fields)

        error = ''    
        calculationSuccess = True
        outFeats = []
        for current, inFeat in enumerate(srcLayer.getFeatures()):
            outFeat = QgsFeature()
            geometry = inFeat.geometry()
            if geometry:
                outFeat.setGeometry(geometry)

            attrs = []
            for i, field_def in enumerate(mapping):
                expression = expressions[i]
                exp_context.setFeature(inFeat)
                exp_context.lastScope().setVariable("row_number", current + 1)
                value = expression.evaluate(exp_context)
                if expression.hasEvalError():
                    calculationSuccess = False
                    error = expression.evalErrorString()
                    break
                attrs.append(value)

            outFeat.setAttributes(attrs)
            outFeats.append(outFeat)

        mLayer.dataProvider().addFeatures(outFeats)
        mLayer.commitChanges()

        if not calculationSuccess:
            raise GeoAlgorithmExecutionException(
                self.tr('An error occurred while evaluating the calculation string:\n') + error)

        return mLayer
