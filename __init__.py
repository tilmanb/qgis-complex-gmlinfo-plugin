# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ComplexGmlInfo
                                 A QGIS plugin
 Display feature info of complex feature types.
                             -------------------
        begin                : 2015-09-16
        copyright            : (C) 2015 by Juergen Weichand
        email                : juergen@weichand.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ComplexGmlInfo class from file ComplexGmlInfo.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gmlinfo import ComplexGmlInfo
    return ComplexGmlInfo(iface)
