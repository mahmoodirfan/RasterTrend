def classFactory(iface):
    from .plugin import RasterTrendPlugin
    return RasterTrendPlugin(iface)
