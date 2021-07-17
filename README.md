# qgis-Measure_Selected_Features
A plugin which enables quick claculations of total dimensions of selected features in line and polygon layers.
Results are shown in a dock widget at the top of the map canvas which can also be undocked and floated.
For layers in a geographic coordinate reference system, distance and area calculations are ellipsoidal, using the layer's crs ellipsoid.
For layers in a projected coordinate system, the calculation method is selected via radio buttons and may either be geodetic
using the layer's crs ellipsoid, or planimetric. Ellipsoidal calculations utilise the QgsDistanceArea class, while planimetric
calculations simply sum the lengths or areas of the selected feature geometries in the layer crs.
The resulting calculations may be converted to any available QgsUnitTypes.
