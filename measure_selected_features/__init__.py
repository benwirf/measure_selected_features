
def classFactory(iface):
    from .measure_selected_features import MeasureSelectedFeatures
    return MeasureSelectedFeatures(iface)