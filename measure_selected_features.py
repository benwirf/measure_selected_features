"""
/****************************************************************************************
 *   Copyright:  (C) Ben Wirf
 *   Date:       April 2020 (updated June 2021)
 *   Email:      ben.wirf@gmail.com
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsDistanceArea, QgsUnitTypes, QgsProject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar, QLineEdit, QRadioButton, QComboBox
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
#        self.da.setEllipsoid('WGS84')
        self.Distance_Units = {0:'m', 1:'km', 2:'Feet', 3:'NM', 4:'Yards',
                5:'Miles', 6:'Degrees', 7:'cm', 8:'mm', 9:'Unknown units'}
        self.Area_Units = {0:'m2', 1:'km2', 2:'Square feet', 3:'Square yards',
                4:'Square miles', 5:'Hectares', 6:'Acres', 7:'NM2',
                8:'Square degrees', 9:'cm2', 10:'mm2', 11: 'Unknown units'}
                
        
        self.cb_linear_items = ['meters', 'kilometers', 'feet', 'nautical miles',
                'yards', 'miles', 'degrees', 'centimeters', 'millimeters']
                
        self.cb_area_items = ['square meters', 'square kilometers', 'square feet',
                'square yards', 'square miles', 'hectares', 'acres', 'square nautical miles',
                'square degrees', 'square centimeters', 'square millimeters']
        
        self.project = None
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
        self.iface.newProjectCreated.connect(self.project_opened)
        self.dlg.was_closed.connect(self.dockwidget_closed)
        self.dlg.topLevelChanged.connect(self.widget_moved)
        self.iface.projectMenu().aboutToShow.connect(self.project_menu_shown)
        self.proj_close_action.triggered.connect(self.project_closed_via_menu_action)
        self.dlg.rad_1.setChecked(True)# 03-06-21
        #####31-05-21
        self.dlg.rad_1.toggled.connect(self.radios_toggled)#############25-06-21
        self.dlg.cb_units.currentIndexChanged.connect(self.total_length)

    
    def project_menu_shown(self):
        if self.dlg.isVisible():
            self.dlg.close()
    
    def project_opened(self):
        if self.project is not None:
            self.project.layerWasAdded.disconnect(self.layer_added)
            self.project.layersRemoved.disconnect(self.layers_removed)
        self.project = QgsProject.instance()
        a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
        if self.iface.activeLayer():
            self.layer = self.iface.activeLayer()
            if not a.isEnabled():
                a.setEnabled(True)
            self.set_title()
        else:
            if a.isEnabled():
                a.setEnabled(False)
        self.project.layerWasAdded.connect(self.layer_added)
        self.project.layersRemoved.connect(self.layers_removed)
            
    def layer_added(self, l):
        if self.layer is None:
            if isinstance(l, QgsVectorLayer):
                self.layer = l
        if len(self.project.mapLayers()) == 1:
            a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
            if not a.isEnabled():
                a.setEnabled(True)
                
    def layers_removed(self, lyr_ids):
        if len(self.project.mapLayers()) == 0:
            self.layer = None
            if self.dlg.isVisible():
                self.dlg.close()
            a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
            if a.isEnabled():
                a.setEnabled(False)
                
    def project_closed_via_menu_action(self):
        a = [a for a in self.toolbar.actions() if a.objectName() == 'btnMSF'][0]
        a.setEnabled(False)
        QgsProject.instance().layerWasAdded.disconnect(self.layer_added)
        
    def widget_moved(self, top_level):
        if top_level is True:
            self.set_gui_geometry()
            
    def set_gui_geometry(self):
        self.dlg.setGeometry(750, 300, 750, 50)

            
    def action_triggered(self):
        self.window.addDockWidget(Qt.TopDockWidgetArea, self.dlg)
        self.dlg.setAllowedAreas(Qt.TopDockWidgetArea)
        self.dlg.show()
        if self.layer is not None:
            if isinstance(self.iface.activeLayer(), QgsVectorLayer):
                self.layer = self.iface.activeLayer()
            if isinstance(self.layer, QgsVectorLayer):
                self.layer.selectionChanged.connect(self.total_length)
        self.iface.currentLayerChanged.connect(self.active_changed)
        self.set_title() # V2 change
        self.total_length() # V2 change
        #####25-05-21
        self.action.setEnabled(False)
        #####
        
    def active_changed(self, new_layer):
        self.tool_reset(self.layer)
        self.set_title() # V3 change
        if isinstance(new_layer, QgsVectorLayer):
            if self.layer is not None:
#                print(self.layer.name())
                if len(QgsProject.instance().mapLayers()) > 1:
                    self.layer.selectionChanged.disconnect(self.total_length)
            self.layer = new_layer
            self.layer.selectionChanged.connect(self.total_length)
            self.total_length() # V2 change
            
    def tool_reset(self, layer):
        if layer is not None:
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == 0: # V2 change
                layer.selectByIds([])
            for le in self.dlg.findChildren(QLineEdit):
                le.clear()
            for cb in self.dlg.findChildren(QComboBox):
                cb.clear()
                cb.setEnabled(False)
            
    def set_title(self):
        self.dlg.lbl_1.setText('Total')
        for le in self.dlg.findChildren(QLineEdit):
            le.setEnabled(False)
        active_layer = self.iface.activeLayer()
        if isinstance(active_layer, QgsVectorLayer):
            if active_layer.isSpatial():
                #####25-05-21
                if active_layer.geometryType() == 0: # points
                    self.dlg.setWindowTitle('Point layer selected')
                    for le in self.dlg.findChildren(QLineEdit):
                        le.setEnabled(False)
                    for rb in self.dlg.findChildren(QRadioButton):
                        rb.setEnabled(False)
                    for cb in self.dlg.findChildren(QComboBox):
                        cb.clear()
                        cb.setEnabled(False)
                elif active_layer.geometryType() in [1, 2]:
#                    self.dlg.setWindowTitle('Measuring {} selected features from layer: {}'.format(active_layer.selectedFeatureCount(), active_layer.name())) # V2 change
                    for le in self.dlg.findChildren(QLineEdit):
                        le.setEnabled(True)
                    self.dlg.cb_units.setEnabled(True)
                    if active_layer.crs().isGeographic():
                        self.dlg.rad_1.setChecked(True)
                        self.dlg.rad_1.setEnabled(True)
                        self.dlg.rad_2.setEnabled(False)
                        ###25-06-21
                        self.dlg.cb_units.clear()
                        if active_layer.geometryType() == 1: # lines
                            self.dlg.cb_units.addItems(self.cb_linear_items)
                        elif active_layer.geometryType() == 2: # polygons
                            self.dlg.cb_units.addItems(self.cb_area_items)
                    else: # projected CRS
                        for rb in self.dlg.findChildren(QRadioButton):
                            rb.setEnabled(True)
                        ###25-06-21
                        if active_layer.geometryType() == 1: # lines
                            self.dlg.cb_units.clear()
                            self.dlg.cb_units.addItems(self.cb_linear_items)
                            if self.dlg.rad_2.isChecked():
                                self.dlg.cb_units.removeItem(self.cb_linear_items.index('degrees'))
                        elif active_layer.geometryType() == 2: # polygons
                            self.dlg.cb_units.clear()
                            self.dlg.cb_units.addItems(self.cb_area_items)
                            if self.dlg.rad_2.isChecked():
                                self.dlg.cb_units.removeItem(self.cb_area_items.index('square degrees')) 
                        
                #####
            elif not active_layer.isSpatial():
                self.dlg.setWindowTitle('Raster or non-spatial vector layer selected')
                for le in self.dlg.findChildren(QLineEdit):
                    le.setEnabled(False)
                for rb in self.dlg.findChildren(QRadioButton):
                    rb.setEnabled(False)
                for cb in self.dlg.findChildren(QComboBox):
                    cb.clear()
                    cb.setEnabled(False)
        elif isinstance(active_layer, QgsRasterLayer):
            self.dlg.setWindowTitle('Raster or non-spatial vector layer selected')
            for le in self.dlg.findChildren(QLineEdit):
                le.setEnabled(False)
            for rb in self.dlg.findChildren(QRadioButton):
                rb.setEnabled(False)
            for cb in self.dlg.findChildren(QComboBox):
                cb.clear()
                cb.setEnabled(False)
        elif active_layer is None:
            self.dlg.setWindowTitle('No layer selected')
    
    def radios_toggled(self):
        if self.iface.activeLayer().geometryType() == 1: # lines
            if self.dlg.rad_2.isChecked(): # planimetric
                if self.dlg.cb_units.currentText() == 'degrees':
                    # reload combobox items without degree option
                    self.dlg.cb_units.clear()
                    self.dlg.cb_units.addItems(self.cb_linear_items)
                    self.dlg.cb_units.removeItem(self.cb_linear_items.index('degrees'))
                else:
                    # just remove the degree option
                    self.dlg.cb_units.removeItem(self.cb_linear_items.index('degrees'))
            elif self.dlg.rad_1.isChecked(): # ellipsoidal
                if self.dlg.cb_units.count() == 0:
                    self.dlg.cb_units.addItems(self.cb_linear_items)
                    if not self.dlg.cb_units.isEnabled():
                        self.dlg.cb_units.setEnabled(True)
                    if self.layer.crs().mapUnits() != QgsUnitTypes.DistanceUnknownUnit:
                        self.dlg.cb_units.setCurrentText(QgsUnitTypes.encodeUnit(self.layer.crs().mapUnits()))
                else:
                    self.dlg.cb_units.insertItem(6, 'degrees')
        elif self.iface.activeLayer().geometryType() == 2: # polygons
            if self.dlg.rad_2.isChecked():
                if self.dlg.cb_units.currentText() == 'square degrees':
                    self.dlg.cb_units.clear()
                    self.dlg.cb_units.addItems(self.cb_area_items)
                    self.dlg.cb_units.removeItem(self.cb_area_items.index('square degrees'))
                else:
                    self.dlg.cb_units.removeItem(self.cb_area_items.index('square degrees'))
            elif self.dlg.rad_1.isChecked():
                if self.dlg.cb_units.count() == 0:
                    self.dlg.cb_units.addItems(self.cb_area_items)
                    if not self.dlg.cb_units.isEnabled():
                        self.dlg.cb_units.setEnabled(True)
                    if self.layer.crs().mapUnits() != QgsUnitTypes.DistanceUnknownUnit:
                        self.dlg.cb_units.setCurrentText('square {}'.format(QgsUnitTypes.encodeUnit(self.layer.crs().mapUnits())))
                else:
                    self.dlg.cb_units.insertItem(8, 'square degrees')
        self.total_length()
    
    def geodetic_length(self, feat):
        geo_m = self.da.measureLength(feat.geometry())
        return geo_m
        
    def geodetic_area(self, feat):
        geo_m2 = self.da.measureArea(feat.geometry())
        return geo_m2
        
    def planar_length(self, feat):
        proj_m = feat.geometry().length()
        return proj_m
        
    def planar_area(self, feat):
        proj_m2 = feat.geometry().area()
        return proj_m2
            
    def total_length(self):
#        print('func called')
        layer = self.layer
#        self.set_title()
        if isinstance(layer, QgsVectorLayer) and layer.isSpatial():
            #####04-06-21
            self.da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
            self.da.setEllipsoid(layer.crs().ellipsoidAcronym())
            #####04-06-21
            select_fts = [f for f in layer.selectedFeatures()]
            
            
            epsg_code = layer.crs().authid()
            if layer.crs().isGeographic():
                crs_type = 'Geographic'
            else:
                crs_type = 'Projected'
            
            l_units = layer.crs().mapUnits()
            if layer.geometryType() == 1:# Lines
                self.dlg.setWindowTitle('Measuring {} selected features from layer: {} - {} ({})'.format(layer.selectedFeatureCount(),
                layer.name(), epsg_code, crs_type))
                self.dlg.lbl_1.setText('Total length of selected features: ')
                if layer.crs().isGeographic() or (not layer.crs().isGeographic() and self.dlg.rad_1.isChecked()):
                    total_geo_m = sum([self.geodetic_length(f) for f in select_fts])
                    if self.dlg.cb_units.currentText() == 'meters':
                        self.dlg.le_total.setText(str('{:.3f}m'.format(total_geo_m)))
                    elif self.dlg.cb_units.currentText() == 'kilometers':
                        total_geo_km = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceKilometers)
                        self.dlg.le_total.setText(str('{:.3f}km'.format(total_geo_km)))
                    elif self.dlg.cb_units.currentText() == 'feet':
                        total_geo_ft = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceFeet)
                        self.dlg.le_total.setText(str('{:.3f}ft'.format(total_geo_ft)))
                    elif self.dlg.cb_units.currentText() == 'nautical miles':
                        total_geo_nm = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceNauticalMiles)
                        self.dlg.le_total.setText(str('{:.3f}NM'.format(total_geo_nm)))
                    elif self.dlg.cb_units.currentText() == 'yards':
                        total_geo_yds = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceYards)
                        self.dlg.le_total.setText(str('{:.3f}yds'.format(total_geo_yds)))
                    elif self.dlg.cb_units.currentText() == 'miles':
                        total_geo_mi = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceMiles)
                        self.dlg.le_total.setText(str('{:.3f}mi'.format(total_geo_mi)))
                    elif self.dlg.cb_units.currentText() == 'degrees':
                        total_geo_deg = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceDegrees)
                        self.dlg.le_total.setText(str('{:.3f}deg'.format(total_geo_deg)))
                    elif self.dlg.cb_units.currentText() == 'centimeters':
                        total_geo_cm = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceCentimeters)
                        self.dlg.le_total.setText(str('{:.3f}cm'.format(total_geo_cm)))
                    elif self.dlg.cb_units.currentText() == 'millimeters':
                        total_geo_mm = self.da.convertLengthMeasurement(total_geo_m, QgsUnitTypes.DistanceMillimeters)
                        self.dlg.le_total.setText(str('{:.3f}mm'.format(total_geo_mm)))
                    
                else: # projected CRS
                    total_length_proj = sum([self.planar_length(f) for f in select_fts])
                    if l_units != 6: # Units are NOT degrees
                        if self.dlg.cb_units.currentText() == 'meters':
                            self.dlg.le_total.setText(str('{:.3f}m'.format(self.convert_planar_length(total_length_proj, l_units, 0))))
                        elif self.dlg.cb_units.currentText() == 'kilometers':
                            self.dlg.le_total.setText(str('{:.3f}km'.format(self.convert_planar_length(total_length_proj, l_units, 1))))
                        elif self.dlg.cb_units.currentText() == 'feet':
                            self.dlg.le_total.setText(str('{:.3f}ft'.format(self.convert_planar_length(total_length_proj, l_units, 2))))
                        elif self.dlg.cb_units.currentText() == 'nautical miles':
                            self.dlg.le_total.setText(str('{:.3f}NM'.format(self.convert_planar_length(total_length_proj, l_units, 3))))
                        elif self.dlg.cb_units.currentText() == 'yards':
                            self.dlg.le_total.setText(str('{:.3f}yd'.format(self.convert_planar_length(total_length_proj, l_units, 4))))
                        elif self.dlg.cb_units.currentText() == 'miles':
                            self.dlg.le_total.setText(str('{:.3f}mi'.format(self.convert_planar_length(total_length_proj, l_units, 5))))
                        elif self.dlg.cb_units.currentText() == 'centimeters':
                            self.dlg.le_total.setText(str('{:.3f}cm'.format(self.convert_planar_length(total_length_proj, l_units, 7))))
                        elif self.dlg.cb_units.currentText() == 'millimeters':
                            self.dlg.le_total.setText(str('{:.3f}mm'.format(self.convert_planar_length(total_length_proj, l_units, 8))))
                    else: # degree units
                        self.dlg.cb_units.clear()
                        self.dlg.cb_units.setEnabled(False)
                        self.dlg.le_total.setText(str('{:.3f}{}'.format(total_length_proj, self.Distance_Units[l_units])))
                        
                        
            elif layer.geometryType() == 2:# Polygons
                self.dlg.setWindowTitle('Measuring {} selected features from layer: {} - {} ({})'.format(layer.selectedFeatureCount(),
                layer.name(), epsg_code, crs_type))
                self.dlg.lbl_1.setText('Total area of selected features: ')
                if layer.crs().isGeographic() or (not layer.crs().isGeographic() and self.dlg.rad_1.isChecked()):
                    total_geo_m = sum([self.geodetic_area(f) for f in select_fts])
                    if self.dlg.cb_units.currentText() == 'square meters':
                        self.dlg.le_total.setText(str('{:.3f}m2'.format(total_geo_m)))
                    elif self.dlg.cb_units.currentText() == 'square kilometers':
                        total_geo_km = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareKilometers)
                        self.dlg.le_total.setText(str('{:.3f}km2'.format(total_geo_km)))
                    elif self.dlg.cb_units.currentText() == 'square feet':
                        total_geo_ft = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareFeet)
                        self.dlg.le_total.setText(str('{:.3f}ft2'.format(total_geo_ft)))
                    elif self.dlg.cb_units.currentText() == 'square yards':
                        total_geo_yds = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareYards)
                        self.dlg.le_total.setText(str('{:.3f}yd2'.format(total_geo_yds)))
                    elif self.dlg.cb_units.currentText() == 'square miles':
                        total_geo_mi = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareMiles)
                        self.dlg.le_total.setText(str('{:.3f}mi2'.format(total_geo_mi)))
                    elif self.dlg.cb_units.currentText() == 'hectares':
                        total_geo_ha = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaHectares)
                        self.dlg.le_total.setText(str('{:.3f}ha'.format(total_geo_ha)))
                    elif self.dlg.cb_units.currentText() == 'acres':
                        total_geo_ac = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaAcres)
                        self.dlg.le_total.setText(str('{:.3f}ac'.format(total_geo_ac)))
                    elif self.dlg.cb_units.currentText() == 'square nautical miles':
                        total_geo_nm = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareNauticalMiles)
                        self.dlg.le_total.setText(str('{:.3f}NM2'.format(total_geo_nm)))
                    elif self.dlg.cb_units.currentText() == 'square degrees':
                        total_geo_deg = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareDegrees)
                        self.dlg.le_total.setText(str('{:.3f}deg2'.format(total_geo_deg)))
                    elif self.dlg.cb_units.currentText() == 'square centimeters':
                        total_geo_cm = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareCentimeters)
                        self.dlg.le_total.setText(str('{:.3f}cm2'.format(total_geo_cm)))
                    elif self.dlg.cb_units.currentText() == 'square millimeters':
                        total_geo_mm = self.da.convertAreaMeasurement(total_geo_m, QgsUnitTypes.AreaSquareMillimeters)
                        self.dlg.le_total.setText(str('{:.3f}mm2'.format(total_geo_mm)))
                    
                else: # projected CRS
                    total_area_proj = sum([self.planar_area(f) for f in select_fts])
                    if l_units != 6: # Units are NOT degrees
                        if self.dlg.cb_units.currentText() == 'square meters':
                            self.dlg.le_total.setText(str('{:.3f}m2'.format(self.convert_planar_area(total_area_proj, l_units, 'square meters'))))
                        elif self.dlg.cb_units.currentText() == 'square kilometers':
                            self.dlg.le_total.setText(str('{:.3f}km2'.format(self.convert_planar_area(total_area_proj, l_units, 'square kilometers'))))
                        elif self.dlg.cb_units.currentText() == 'square feet':
                            self.dlg.le_total.setText(str('{:.3f}ft2'.format(self.convert_planar_area(total_area_proj, l_units, 'square feet'))))
                        elif self.dlg.cb_units.currentText() == 'square yards':
                            self.dlg.le_total.setText(str('{:.3f}yd2'.format(self.convert_planar_area(total_area_proj, l_units, 'square yards'))))
                        elif self.dlg.cb_units.currentText() == 'square miles':
                            self.dlg.le_total.setText(str('{:.3f}mi2'.format(self.convert_planar_area(total_area_proj, l_units, 'square miles'))))
                        elif self.dlg.cb_units.currentText() == 'hectares':
                            self.dlg.le_total.setText(str('{:.3f}ha'.format(self.convert_planar_area(total_area_proj, l_units, 'hectares'))))
                        elif self.dlg.cb_units.currentText() == 'acres':
                            self.dlg.le_total.setText(str('{:.3f}ac'.format(self.convert_planar_area(total_area_proj, l_units, 'acres'))))
                        elif self.dlg.cb_units.currentText() == 'square nautical miles':
                            self.dlg.le_total.setText(str('{:.3f}NM2'.format(self.convert_planar_area(total_area_proj, l_units, 'square nautical miles'))))
                        elif self.dlg.cb_units.currentText() == 'square centimeters':
                            self.dlg.le_total.setText(str('{:.3f}cm2'.format(self.convert_planar_area(total_area_proj, l_units, 'square centimeters'))))
                        elif self.dlg.cb_units.currentText() == 'square millimeters':
                            self.dlg.le_total.setText(str('{:.3f}mm2'.format(self.convert_planar_area(total_area_proj, l_units, 'square millimeters'))))
                    else: # Degree units
                        self.dlg.cb_units.clear()
                        if self.dlg.cb_units.isEnabled():
                            self.dlg.cb_units.setEnabled(False)
                        self.dlg.le_total.setText(str('{:.3f}{}2'.format(total_area_proj, self.Distance_Units[l_units])))
                        
            if layer.geometryType() in [3, 4]:
                self.iface.messageBar().pushMessage('Layer has unknown or Null geometry type', duration=2)

###########################UNIT CONVERSIONS FOR PROJECTED CRS'S#####################################

    def convert_planar_length(self, length, input_units, output_units):
        if input_units == 0: # Meters
            if output_units == 0: # Meters
                result = length
            elif output_units == 1: # Kilometers
                result = length/1000
            elif output_units == 2: # Imperial feet
                result = length*3.28084
            elif output_units == 3: # Nautical miles
                result = length/1852
            elif output_units == 4: # Imperial yards
                result = length*1.09361
            elif output_units == 5: # Terrestrial miles
                result = length/1609.344
            elif output_units == 7: # Centimeters
                result = length*100
            elif output_units == 8: # Millimeters
                result = length*1000
        elif input_units == 1: # Kilometers
            if output_units == 0: # Meters
                result = length*1000
            elif output_units == 1: # Kilometers
                result = length
            elif output_units == 2: # Imperial feet
                result = length*3280.84
            elif output_units == 3: # Nautical miles
                result = length/1.852
            elif output_units == 4: # Imperial yards
                result = length*1093.61
            elif output_units == 5: # Terrestrial miles
                result = length/1.609
            elif output_units == 7: # Centimeters
                result = length*100000
            elif output_units == 8: # Millimeters
                result = length*1000000
        elif input_units == 2: # Imperial feet
            if output_units == 0: # Meters
                result = length/3.281
            elif output_units == 1: # Kilometers
                result = length/3281
            elif output_units == 2: # Imperial feet
                result = length
            elif output_units == 3: # Nautical Miles
                result = length/6076
            elif output_units == 4: # Imperial yards
                result = length/3
            elif output_units == 5: # Terrestrial miles
                result = length/5280
            elif output_units == 7: # Centimeters
                result = length*30.48
            elif output_units == 8: # Millimeters
                result = length*304.8
        elif input_units == 3: # Nautical miles
            if output_units == 0: # Meters
                result = length*1852
            if output_units == 1: # Kilometers
                result = length*1.852
            elif output_units == 2: # Imperial feet
                result = length*6076
            elif output_units == 3: # Nautical miles
                result = length
            elif output_units == 4: # Imperial yards
                result = length*2025.37
            elif output_units == 5: # Terrestrial miles
                result = length*1.15078
            elif output_units == 7: # Centimeters
                result = length*185200
            elif output_units == 8: # Millimeters
                result = length*1852000
        elif input_units == 4: # Imperial yards
            if output_units == 0: # Meters
                result = length/1.094
            elif output_units == 1: # Kilometers
                result = length/1094
            elif output_units == 2: # Imperial feet
                result = length*3
            elif output_units == 3: # Nautical miles
                result = length/2025
            elif output_units == 4: # Imperial yards
                result = length
            elif output_units == 5: # Terrestrial miles
                result = length/1760
            elif output_units == 7: # Centimeters
                result = length*91.44
            elif output_units == 8: # Millimeters
                result = length*914.4
        elif input_units == 5: # Terrestrial miles
            if output_units == 0: # Meters
                result = length*1609.34
            elif output_units == 1: # Kilometers
                result = length*1.609
            elif output_units == 2: # Imperial feet
                result = length*5280
            elif output_units == 3: # Nautical miles
                result = length/1.151
            elif output_units == 4: # Imperial yards
                result = length*1760
            elif output_units == 5: # Terrestrial miles
                result = length
            elif output_units == 7: # Centimeters
                result = length*160934
            elif output_units == 8: # Millimeters
                result = length*1609340
        elif input_units == 7: # Centimeters
            if output_units == 0: # Meters
                result = length/100
            elif output_units == 1: # Kilometers
                result = length/100000
            elif output_units == 2: # Imperial feet
                result = length/30.48
            elif output_units == 3: # Nautical miles
                result = length/185200
            elif output_units == 4: # Imperial yards
                result = length/91.44
            elif output_units == 5: # Terrestrial miles
                result = length/160934
            elif output_units == 7: # Centimeters
                result = length
            elif output_units == 8: # Millimeters
                result = length*10
        elif input_units == 8: # Millimeters
            if output_units == 0: # Meters
                result = length/1000
            elif output_units == 1: # Kilometers
                result = length/1000000
            elif output_units == 2: # Imperial feet
                result = length/305
            elif output_units == 3: # Nautical miles
                result = length/1852000
            elif output_units == 4: # Imperial yards
                result = length/914
            elif output_units == 5: # Terrestrial miles
                result = length/1609000
            elif output_units == 7: # Centimeters
                result = length/10
            elif output_units == 8: # Millimeters
                result = length
                
        return result

#####################################AREA UNITS#####################################################

    def convert_planar_area(self, area, input_units, output_units):
        if input_units == 0: # Meters
            if output_units == 'square meters': # Square meters
                result = area
            elif output_units == 'square kilometers': # Square kilometers
                result = area/1000000
            elif output_units == 'square feet': # Square feet
                result = area*10.764
            elif output_units == 'square yards': # Square yards
                result = area*1.196
            elif output_units == 'square miles': # Square miles
                result = area/2589988.1
            elif output_units == 'hectares': # Hectares
                result = area/10000
            elif output_units == 'acres': # Acres
                result = area/4047
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/3429904
            elif output_units == 'square centimeters': # Square centimeters
                result = area*10000
            elif output_units == 'square millimeters': # Square millimeters
                result = area*1000000

    #--------------------------------------------------------------------

        elif input_units == 1: # Kilometers
            if output_units == 'square meters': # Square meters
                result = area*10000
            elif output_units == 'square kilometers': # Square kilometers
                result = area
            elif output_units == 'square feet': # Square feet
                result = area*10763910.417
            elif output_units == 'square yards': # Square yards
                result = area*1195990.05
            elif output_units == 'square miles': # Square miles
                result = area/2.59
            elif output_units == 'hectares': # Hectares
                result = area*100
            elif output_units == 'acres': # Acres
                result = area*247.105
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/3.43
            elif output_units == 'square centimeters': # Square centimeters
                result = area*10000000000
            elif output_units == 'square millimeters': # Square millimeters
                result = area*1000000000000

    #--------------------------------------------------------------------

        elif input_units == 2: # Imperial feet
            if output_units == 'square meters': # Square meters
                result = area/10.764
            elif output_units == 'square kilometers': # Square kilometers
                result = area/10763910.417
            elif output_units == 'square feet': # Square feet
                result = area
            elif output_units == 'square yards': # Square yards
                result = area/9
            elif output_units == 'square miles': # Square miles
                result = area/27878400
            elif output_units == 'hectares': # Hectares
                result = area/107639
            elif output_units == 'acres': # Acres
                result = area/43560
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/36920000
            elif output_units == 'square centimeters': # Square centimeters
                result = area*929
            elif output_units == 'square millimeters': # Square millimeters
                result = area*92903

    #--------------------------------------------------------------------

        elif input_units == 3: # Nautical miles
            if output_units == 'square meters': # Square meters
                result = area*3430000
            elif output_units == 'square kilometers': # Square kilometers
                result = area*3.43
            elif output_units == 'square feet': # Square feet
                result = area*36920000
            elif output_units == 'square yards': # Square yards
                result = area*4102000
            elif output_units == 'square miles': # Square miles
                result = area*1.324
            elif output_units == 'hectares': # Hectares
                result = area*343
            elif output_units == 'acres': # Acres
                result = area*847.548
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area
            elif output_units == 'square centimeters': # Square centimeters
                result = area*34300000000
            elif output_units == 'square millimeters': # Square millimeters
                result = area*3430000000000

    #--------------------------------------------------------------------

        elif input_units == 4: # Imperial yards
            if output_units == 'square meters': # Square meters
                result = area/1.196
            elif output_units == 'square kilometers': # Square kilometers
                result = area/1196000
            elif output_units == 'square feet': # Square feet
                result = area*9
            elif output_units == 'square yards': # Square yards
                result = area
            elif output_units == 'square miles': # Square miles
                result = area/3098000
            elif output_units == 'hectares': # Hectares
                result = area/11960
            elif output_units == 'acres': # Acres
                result = area/4840
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/4102000
            elif output_units == 'square centimeters': # Square centimeters
                result = area*8361
            elif output_units == 'square millimeters': # Square millimeters
                result = area*836127
                
    #--------------------------------------------------------------------

        elif input_units == 5: # Terrestrial miles
            if output_units == 'square meters': # Square meters
                result = area*2590000
            elif output_units == 'square kilometers': # Square kilometers
                result = area*2.59
            elif output_units == 'square feet': # Square feet
                result = area*27880000
            elif output_units == 'square yards': # Square yards
                result = area*3098000
            elif output_units == 'square miles': # Square miles
                result = area
            elif output_units == 'hectares': # Hectares
                result = area*259
            elif output_units == 'acres': # Acres
                result = length*640
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/1.324
            elif output_units == 'square centimeters': # Square centimeters
                result = area*25900000000
            elif output_units == 'square millimeters': # Square millimeters
                result = area*2590000000000

    #--------------------------------------------------------------------

        elif input_units == 7: # Centimeters
            if output_units == 'square meters': # Square meters
                result = area/10000
            elif output_units == 'square kilometers': # Square kilometers
                result = area/10000000000
            elif output_units == 'square feet': # Square feet
                result = area/929.03
            elif output_units == 'square yards': # Square yards
                result = area/8361.27
            elif output_units == 'square miles': # Square miles
                result = area/25899881103.36
            elif output_units == 'hectares': # Hectares
                result = area/100000000
            elif output_units == 'acres': # Acres
                result = area/40468564.224
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/34299040000
            elif output_units == 'square centimeters': # Square centimeters
                result = area
            elif output_units == 'square millimeters': # Square millimeters
                result = area*100
                
    #--------------------------------------------------------------------

        elif input_units == 8: # Millimeters
            if output_units == 'square meters': # Square meters
                result = area/1000000
            elif output_units == 'square kilometers': # Square kilometers
                result = area/1000000000000
            elif output_units == 'square feet': # Square feet
                result = area/92903
            elif output_units == 'square yards': # Square yards
                result = area/836127
            elif output_units == 'square miles': # Square miles
                result = area/2589988110336
            elif output_units == 'hectares': # Hectares
                result = area/10000000000
            elif output_units == 'acres': # Acres
                result = area/4046856422
            elif output_units == 'square nautical miles': # Square Nautical miles
                result = area/3429904000000
            elif output_units == 'square centimeters': # Square centimeters
                result = area/100
            elif output_units == 'square millimeters': # Square millimeters
                result = area

        return result

####################################################################################################
    
    def dockwidget_closed(self):
#        print('dockwidget closed!!')
        self.dlg.setFloating(False)
        if self.layer is not None:
            self.tool_reset(self.layer)
            if isinstance(self.layer, QgsVectorLayer):
                self.layer.selectionChanged.disconnect(self.total_length)
        self.iface.currentLayerChanged.disconnect(self.active_changed)
        #####25-05-21
        self.action.setEnabled(True)
    
    def unload(self):
        self.toolbar.removeAction(self.action)
        del self.action