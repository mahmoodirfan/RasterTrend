import os
from qgis.core import QgsProcessingProvider
from .algorithm import RasterTrendAlgorithm


class RasterTrendProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(RasterTrendAlgorithm())

    def id(self):
        return 'rastertrend'

    def name(self):
        return 'RasterTrend'

    def longName(self):
        return 'RasterTrend - Mann-Kendall Trend Analysis'

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
        return QIcon(icon_path)

    def svgIconPath(self):
        return os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
