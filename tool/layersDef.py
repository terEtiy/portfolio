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


layersDef = \
    {'Рамки карты макета':
         {'schema': 'gpzu',
          'table': 'gpzu_frames',
          'geomField': 'geom',
          'filter': '"scale"=%s and "gpzu_gid"=%s',
          'exp': ('[0-9]+', '[0-9]+')},
     'Точки пересечений с территориальными подзонами':
         {'schema': 'gpzu',
          'table': 'gpzu_tpz_intersection_points',
          'geomField': 'geom',
          'filter': '"gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Схема страниц':
         {'schema': 'gpzu',
          'table': 'gpzu_frames',
          'geomField': 'page_geom',
          'filter': '"scale"=%s and "gpzu_gid"=%s',
          'exp': ('[0-9]+', '[0-9]+')},
     'Координаты поворотных точек':
         {'schema': 'gpzu',
          'table': 'gpzu_point_labels',
          'geomField': 'geom',
          'filter': '"scale"=%s and "gpzu_gid"=%s',
          'exp': ('[0-9]+', '[0-9]+')},
     'Поворотные точки участка':
         {'schema': 'gpzu',
          'table': 'gpzu_points',
          'geomField': 'geom',
          'filter': '"gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Части земельного участка':
      {'schema': 'gpzu',
       'table': 'zu_parts',
       'geomField': 'geom',
       'filter': '"gpzu_gid"=%s',
       'exp': '[0-9]+'},
     'Границы земельного участка':
         {'schema': 'gpzu',
          'table': 'gpzu',
          'geomField': 'geom',
          'filter': '"gid"=%s',
          'exp': '[0-9]+'},
     'Подписи объектов капитального строительства':
         {'schema': 'gpzu',
          'table': 'ikop_point_labels',
          'geomField': 'geom',
          'filter': '"type"=1  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Территория объекта культурного наследия':
         {'schema': 'gpzu',
          'table': 'ikop_point_labels',
          'geomField': 'geom',
          'filter': '"type"=2  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Подписи подзон':
         {'schema': 'gpzu',
          'table': 'ikop_point_labels',
          'geomField': 'geom',
          'filter': '"type"=3  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Подписи индексов режимов подзон':
         {'schema': 'gpzu',
          'table': 'ikop_point_labels',
          'geomField': 'geom',
          'filter': '"type"=4  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Подписи номеров регламентных участков':
         {'schema': 'gpzu',
          'table': 'ikop_point_labels',
          'geomField': 'geom',
          'filter': '"type"=5  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Выноски - подпись части земельного участка':
         {'schema': 'gpzu',
          'table': 'callouts',
          'geomField': 'geom',
          'filter': '"callout_type"=2  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Выноски подзоны':
         {'schema': 'gpzu',
          'table': 'callouts',
          'geomField': 'geom',
          'filter': '"callout_type"=3  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Выноски сит. план':
         {'schema': 'gpzu',
          'table': 'callouts',
          'geomField': 'geom',
          'filter': '"callout_type"=1  AND "gpzu_gid"=%s',
          'exp': '[0-9]+'},
     'Границы земельного участка (маска)':
         {'schema': 'gpzu',
          'table': 'gpzu',
          'geomField': 'geom',
          'filter': '"gid"=%s',
          'exp': '[0-9]+'},
     'Кадастровые участки на ситуационном плане':
         {'schema': '',
          'table': """SELECT 
                        r.gid,
                        r.cadastralnumber,
                        r."state",
                        r.geom
                        FROM 
                            rr.zu_rr r, 
                            gpzu.gpzu g
                        WHERE 
                            g.gid = %s
                            AND r.geom && g.geom
                            AND st_intersects(r.geom, st_buffer(g.geom,2))""",
          'geomField': 'geom',
          'filter': '',
          'exp': '[0-9]+'}
    }