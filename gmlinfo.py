# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ComplexGmlInfo
                                 A QGIS plugin
 Display feature info of complex feature types.
                              -------------------
        begin                : 2015-09-16
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Juergen Weichand
        email                : juergen@weichand.de
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QTreeWidgetItem, QColor
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from gmlinfo_dialog import ComplexGmlInfoDialog
import os.path

from extlib.pygml import pygml, util
from collections import OrderedDict
import logging


class ComplexGmlInfo:
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
            'ComplexGmlInfo_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = ComplexGmlInfoDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Complex GML Info')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ComplexGmlInfo')
        self.toolbar.setObjectName(u'ComplexGmlInfo')

        logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logfile = util.getTempfile('gmlinfo.log')
        logging.basicConfig(filename=logfile, level=logging.ERROR, format=logformat)

        self.cache = {}

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
        return QCoreApplication.translate('ComplexGmlInfo', message)


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
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ComplexGmlInfo/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Complex GML Info'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.add_action(
            None,
            text='About',
            callback=self.about,
            add_to_toolbar=None,
            parent=None)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Complex GML Info'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def about(self):
        infoString = "<table><tr><td colspan=\"2\"><b>Complex GML Info 0.3</b></td></tr><tr><td colspan=\"2\"></td></tr><tr><td>Author:</td><td>J&uuml;rgen Weichand</td></tr><tr><td>Mail:</td><td><a href=\"mailto:juergen@weichand.de\">juergen@weichand.de</a></td></tr><tr><td>Website:</td><td><a href=\"http://www.weichand.de\">http://www.weichand.de</a></td></tr></table>"
        QMessageBox.information(self.iface.mainWindow(), "About GML Loader", infoString)


    def run(self):
        self.dlg.treeWidget.setHeaderHidden(True)
        self.displaySelectedFeatures()


    def displaySelectedFeatures(self):

        layer = self.iface.activeLayer()

        # layer must be activated
        if not layer:
            QMessageBox.critical(self.dlg, 'Error', u'Please activate GML layer!')
            return

        # layer must be GML
        if layer.storageType() != 'GML':
            QMessageBox.critical(self.dlg, 'Error', u'Please activate GML layer!')
            return

        filename = layer.dataProvider().dataSourceUri().split('|')[0]

        if not filename in self.cache:
            logging.debug('%s not cached yet!' % filename)
            self.cache[filename] = pygml.Dataset(filename)

        gml = self.cache[filename]

        # >= 1 feature must be selected
        if not layer.selectedFeatures():
            QMessageBox.critical(self.dlg, 'Error', u'Please select one or more feature(s) first!')
            return
        else:
            self.dlg.show()

        features = OrderedDict()
        i = 0
        for feature in layer.selectedFeatures():
            if feature.attribute('gml_id'):
                i+=1
                gml_id = feature.attribute('gml_id')
                features['Selected feature [' + str(i) +']'] = gml.getFeature(gml_id)
        self.fill_widget(self.dlg.treeWidget, features)


    def fill_item(self, item, value):
        item.setExpanded(True)
        if type(value) is OrderedDict:
            for key, val in sorted(value.items()):
                if type(val) is unicode:
                    if '@xmlns' not in key: # hack
                        child = QTreeWidgetItem()
                        text = unicode(key + " '" + val + "'")
                        child.setTextColor(0, self.getQColor(text))
                        child.setText(0, text)
                        item.addChild(child)
                else:
                    child = QTreeWidgetItem()
                    text = unicode(key)
                    #child.setTextColor(0, self.getQColor(text))
                    child.setText(0, text)
                    item.addChild(child)
                    self.fill_item(child, val)
        elif type(value) is list:
            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)
                if type(val) is OrderedDict:
                    child.setText(0, '[' + str(value.index(val)) +']')
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, '[' + str(value.index(val)) +']')
                    self.fill_item(child, val)
                else:
                    child.setText(0, unicode(val))
                    child.setExpanded(True)
        else:
            child = QTreeWidgetItem()
            child.setText(0, str(value))
            item.addChild(child)


    def fill_widget(self, widget, value):
        widget.clear()
        self.fill_item(widget.invisibleRootItem(), value)

    def getQColor(self, text):
        for indicator in ['nil']:
            if indicator in text.lower():
                return QColor('lightgrey')
        for indicator in ['gml:id', 'localid', 'identifier', 'xlink:href', 'xlink:type', 'namespace', 'codespace', '#text']:
            if indicator in text.lower():
                return QColor('darkslategray')
        return QColor('red')

