"""
/****************************************************************************************
Copyright:  (C) Ben Wirf
Date:       April 2020
Email:      ben.wirf@gmail.com
****************************************************************************************/
"""

import os
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsDistanceArea, QgsUnitTypes
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar, QLineEdit
from .measure_selected_features_dialog import MeasureSelectedFeaturesDialog

class MeasureSelectedFeatures:
    
    def __init__(self, iface):
        self.iface = iface
        self.window = self.iface.mainWindow()
        self.proj_close_action = [a for a in self.iface.projectMenu().actions() if a.objectName() == 'mActionCloseProject'][0]
        self.dlg = MeasureSelectedFeaturesDialog()
        self.toolbar = self.iface.pluginToolBar()
        self.folder_name = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.folder_name, 'msf_icon.png')
        self.action = QAction(QIcon(self.icon_path), 'Sum selected feature size', self.window)
        self.action.setToolTip('Display total dimensions of selected features')
        self.da = QgsDistanceArea()
        self.da.setEllipsoid('WGS84')
        self.Distance_Units = {0:'m', 1:'km', 2:'Feet', 3:'NM', 4:'Yards',
                5:'Miles', 6:'Degrees', 7:'cm', 8:'mm', 9:'Unknown units'}
        self.Area_Units = {0:'m2', 1:'km2', 2:'Square feet', 3:'NM2', 4:'Square yards',
                5:'Square miles', 6:'Square degrees', 7:'cm2', 8:'mm2', 9:'Unknown units'}
        self.layer = None
        
    def initGui(self):
        """This method is where we add the plugin action to the plugin toolbar."""
        self.action.setObjectName('btnMSF')
        self.toolbar.addAction(self.action)
        if self.iface.activeLayer():
            self.layer = self.iface.activeLayer()
        else:
            self.action.setEnabled(False)
        self.action.triggered.connect(self.action_triggered)
        self.iface.projectRead.connect(self.project_opened)
        self.dlg.was_closed.connect(self.dockwidget_closed)
        self.dlg.topLevelChanged.connect(self.widget_moved)
        self.iface.projectMenu().aboutToShow.connect(self.project_menu_shown)
        self.proj_close_action.triggered.connect(self.project_closed_via_menu_action)
    
    def project_menu_shown(self):
        if self.dlg.isVisible():
            self.dlg.close()
    
    def project_opened(self):
        self.layer = self.iface.activeLayer()
        a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
        if not a.isEnabled():
            a.setEnabled(True)
        self.set_title()
        
    def project_closed_via_menu_action(self):
        a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
        a.setEnabled(False)
        
    def widget_moved(self, top_level):
        if top_level is True:
            self.set_gui_geometry()
            
    def set_gui_geometry(self):
        self.dlg.le_geo.setMinimumSize(QSize(150, 10))
        self.dlg.le_proj.setMinimumSize(QSize(150, 10))
        self.dlg.setGeometry(750, 300, 850, 50)
                    
    def action_triggered(self):
        self.window.addDockWidget(Qt.TopDockWidgetArea, self.dlg)
        self.dlg.setAllowedAreas(Qt.TopDockWidgetArea)
        self.dlg.show()
        if isinstance(self.iface.activeLayer(), QgsVectorLayer):
            self.layer = self.iface.activeLayer()
        if isinstance(self.layer, QgsVectorLayer):
            self.layer.selectionChanged.connect(self.total_length)
        self.iface.currentLayerChanged.connect(self.active_changed)
        self.set_title() # V2 change
        self.total_length() # V2 change

    def active_changed(self, new_layer):
        self.tool_reset(self.layer)
        self.set_title() # V3 change
        if isinstance(new_layer, QgsVectorLayer):
            self.layer.selectionChanged.disconnect(self.total_length)
            self.layer = new_layer
            self.layer.selectionChanged.connect(self.total_length)
        self.total_length() # V2 change
            
    def tool_reset(self, layer):
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == 0: # V2 change
            layer.selectByIds([])
        for le in self.dlg.findChildren(QLineEdit):
            le.clear()
            
    def set_title(self):
        active_layer = self.iface.activeLayer()
        if isinstance(active_layer, QgsVectorLayer):
            self.dlg.setWindowTitle('Measure selected features: {}'. format(self.layer.name())) # V2 change
            for le in self.dlg.findChildren(QLineEdit):
                le.setEnabled(True)
        elif isinstance(active_layer, QgsRasterLayer):
            self.dlg.setWindowTitle('Measure selected features')
            for le in self.dlg.findChildren(QLineEdit):
                le.setEnabled(False)
        
    def geodetic_length(self, feat):
        geo_m = self.da.measureLength(feat.geometry())
        geo_km = self.da.convertLengthMeasurement(geo_m, QgsUnitTypes.DistanceKilometers)
        return (geo_m, geo_km)
        
    def geodetic_area(self, feat):
        geo_m2 = self.da.measureArea(feat.geometry())
        geo_km2 = self.da.convertAreaMeasurement(geo_m2, QgsUnitTypes.AreaSquareKilometers)
        geo_ha = self.da.convertAreaMeasurement(geo_m2, QgsUnitTypes.AreaHectares)
        return (geo_m2, geo_km2, geo_ha)
        
    def planar_length(self, feat):
        proj_m = feat.geometry().length()
        proj_km = proj_m/1000
        return (proj_m, proj_km)
        
    def planar_area(self, feat):
        proj_m2 = feat.geometry().area()
        proj_km2 = proj_m2/1000000
        proj_ha = proj_m2/10000
        return (proj_m2, proj_km2, proj_ha)
            
    def total_length(self):
        layer = self.layer
        self.set_title()
        if isinstance(layer, QgsVectorLayer):
            select_fts = [f for f in layer.selectedFeatures()]
            l_units = layer.crs().mapUnits()
            if layer.geometryType() == 1:# Lines
                if layer.crs().isGeographic():
                    total_geo_m = sum([self.geodetic_length(f)[0] for f in select_fts])
                    total_geo_km = sum([self.geodetic_length(f)[1] for f in select_fts])
                    self.dlg.le_geo.setText(str('{:.3f}m'.format(total_geo_m)))
                    self.dlg.le_converted_km.setText(str('{:.3f}km'.format(total_geo_km)))
                else:
                    total_proj_m = sum([self.planar_length(f)[0] for f in select_fts])
                    self.dlg.le_proj.setText(str('{:.3f}{}'.format(total_proj_m, self.Distance_Units[l_units])))
                    if l_units == 0:
                        total_proj_km = sum([self.planar_length(f)[1] for f in select_fts])
                        self.dlg.le_converted_km.setText(str('{:.3f}km'.format(total_proj_km)))
            elif layer.geometryType() == 2:# Polygons
                if layer.crs().isGeographic():
                    total_geo_m2 = sum([self.geodetic_area(f)[0] for f in select_fts])
                    total_geo_km2 = sum([self.geodetic_area(f)[1] for f in select_fts])
                    total_geo_ha = sum([self.geodetic_area(f)[2] for f in select_fts])
                    self.dlg.le_geo.setText(str('{:.3f}m'.format(total_geo_m2)))
                    self.dlg.le_converted_km.setText(str('{:.3f}km2'.format(total_geo_km2)))
                    self.dlg.le_converted_ha.setText(str('{:.3f}ha'.format(total_geo_ha)))
                else:
                    total_proj_m2 = sum([self.planar_area(f)[0] for f in select_fts])
                    self.dlg.le_proj.setText(str('{:.3f}{}'.format(total_proj_m2, self.Area_Units[l_units])))
                    if l_units == 0:
                        total_proj_km2 = sum([self.planar_area(f)[1] for f in select_fts])
                        total_proj_ha = sum([self.planar_area(f)[2] for f in select_fts])
                        self.dlg.le_converted_km.setText(str('{:.3f}km2'.format(total_proj_km2)))
                        self.dlg.le_converted_ha.setText(str('{:.3f}ha'.format(total_proj_ha)))
            if layer.geometryType() in [0, 3, 4]:
                if len(layer.selectedFeatures())>0:
                    self.iface.messageBar().pushMessage('Please select a line or polygon layer', duration=2)
    
    def dockwidget_closed(self):
        self.tool_reset(self.layer)
        self.dlg.setFloating(False)
        if isinstance(self.layer, QgsVectorLayer):
            self.layer.selectionChanged.disconnect(self.total_length)
        self.iface.currentLayerChanged.disconnect(self.active_changed)
    
    def unload(self):
        self.toolbar.removeAction(self.action)
        del self.action