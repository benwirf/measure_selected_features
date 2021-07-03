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

def classFactory(iface):
    from .measure_selected_features import MeasureSelectedFeatures
    return MeasureSelectedFeatures(iface)