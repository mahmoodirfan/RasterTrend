import numpy as np
from osgeo import gdal

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFolderDestination,
    QgsProcessingOutputMultipleLayers,
    QgsProcessingException,
    QgsRasterLayer,
    QgsProject,
    QgsProcessingParameterString,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsRasterFileWriter,
    QgsRasterPipe,
)
from qgis.core import QgsProcessing
import os


class RasterTrendAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYERS   = 'INPUT_LAYERS'
    TEST_TYPE      = 'TEST_TYPE'
    SEASON_PERIOD  = 'SEASON_PERIOD'
    SIG_THRESHOLD  = 'SIG_THRESHOLD'
    OUTPUT_FOLDER  = 'OUTPUT_FOLDER'

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                'Input raster layers (time-ordered)',
                QgsProcessing.TypeRaster
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.TEST_TYPE,
                'Trend test type',
                options=['Standard Mann-Kendall', 'Seasonal Mann-Kendall'],
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SEASON_PERIOD,
                'Season period (for Seasonal MK only, e.g. 12 for monthly)',
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=12,
                minValue=2,
                maxValue=365,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SIG_THRESHOLD,
                'Significance threshold (p-value)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.05,
                minValue=0.001,
                maxValue=0.1
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                'Output folder'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        from .mk_engine import (
            mann_kendall_vectorized,
            seasonal_mann_kendall_vectorized,
            sens_slope_vectorized
        )

        layers    = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        test_type = self.parameterAsEnum(parameters, self.TEST_TYPE, context)
        period    = self.parameterAsInt(parameters, self.SEASON_PERIOD, context)
        sig_thr   = self.parameterAsDouble(parameters, self.SIG_THRESHOLD, context)
        out_dir   = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

        if len(layers) < 4:
            raise QgsProcessingException(
                'At least 4 raster layers required for meaningful trend analysis.'
            )

        if test_type == 1 and len(layers) < period * 2:
            raise QgsProcessingException(
                f'Seasonal MK with period={period} requires at least {period*2} layers. '
                f'You provided {len(layers)}.'
            )

        # ── Read reference raster metadata from first layer ──────────────────
        ref_path = layers[0].source()
        ref_ds   = gdal.Open(ref_path)
        if ref_ds is None:
            raise QgsProcessingException(f'Cannot open raster: {ref_path}')

        cols      = ref_ds.RasterXSize
        rows      = ref_ds.RasterYSize
        geo_trans = ref_ds.GetGeoTransform()
        projection = ref_ds.GetProjection()
        nodata    = ref_ds.GetRasterBand(1).GetNoDataValue()
        ref_ds    = None

        n_pixels = rows * cols
        n_layers = len(layers)

        feedback.pushInfo(f'Raster size: {cols} x {rows} = {n_pixels:,} pixels')
        feedback.pushInfo(f'Time steps : {n_layers}')
        feedback.pushInfo(f'Test type  : {"Seasonal MK" if test_type == 1 else "Standard MK"}')
        feedback.pushInfo('Loading raster stack...')

        # ── Stack all bands into array (time x pixels) ───────────────────────
        stack = np.full((n_layers, n_pixels), np.nan, dtype=np.float32)

        for i, layer in enumerate(layers):
            if feedback.isCanceled():
                return {}
            ds   = gdal.Open(layer.source())
            band = ds.GetRasterBand(1)
            arr  = band.ReadAsArray().astype(np.float32).ravel()

            # Mask nodata
            nd = band.GetNoDataValue()
            if nd is not None:
                arr[arr == nd] = np.nan

            stack[i] = arr
            ds = None
            feedback.setProgress(int(20 * (i + 1) / n_layers))

        feedback.pushInfo('Running trend analysis...')

        # ── Identify valid pixels (no NaN across entire time series) ─────────
        valid_mask = ~np.any(np.isnan(stack), axis=0)
        n_valid    = int(valid_mask.sum())

        feedback.pushInfo(f'Valid pixels: {n_valid:,} / {n_pixels:,}')

        if n_valid == 0:
            raise QgsProcessingException(
                'No valid pixels found. Check NoData values in your raster stack.'
            )

        data_valid = stack[:, valid_mask].astype(np.float64)

        # ── Run selected test ────────────────────────────────────────────────
        feedback.setProgress(25)

        if test_type == 0:
            tau, p_val, trend = mann_kendall_vectorized(data_valid)
        else:
            tau, p_val, trend = seasonal_mann_kendall_vectorized(data_valid, period)

        feedback.setProgress(75)
        feedback.pushInfo('Computing Sen\'s Slope...')
        slope = sens_slope_vectorized(data_valid)

        # ── Significance mask ────────────────────────────────────────────────
        sig_mask = (p_val <= sig_thr).astype(np.float32)

        # ── Reconstruct full spatial arrays ──────────────────────────────────
        out_slope = np.full(n_pixels, np.nan, dtype=np.float32)
        out_pval  = np.full(n_pixels, np.nan, dtype=np.float32)
        out_tau   = np.full(n_pixels, np.nan, dtype=np.float32)
        out_sig   = np.full(n_pixels, np.nan, dtype=np.float32)

        out_slope[valid_mask] = slope.astype(np.float32)
        out_pval[valid_mask]  = p_val.astype(np.float32)
        out_tau[valid_mask]   = tau.astype(np.float32)
        out_sig[valid_mask]   = sig_mask

        feedback.setProgress(85)
        feedback.pushInfo('Writing output rasters...')

        # ── Write outputs ─────────────────────────────────────────────────────
        os.makedirs(out_dir, exist_ok=True)

        outputs = {
            'sens_slope'  : ('sens_slope.tif',   out_slope, "Sen's Slope"),
            'p_value'     : ('p_value.tif',       out_pval,  'P-Value'),
            'kendall_tau' : ('kendall_tau.tif',   out_tau,   "Kendall's Tau"),
            'sig_mask'    : ('significance_mask.tif', out_sig, f'Significant trend (p≤{sig_thr})'),
        }

        driver = gdal.GetDriverByName('GTiff')
        out_paths = []

        for key, (fname, arr, desc) in outputs.items():
            path = os.path.join(out_dir, fname)
            ds_out = driver.Create(path, cols, rows, 1, gdal.GDT_Float32,
                                   options=['COMPRESS=LZW', 'TILED=YES'])
            ds_out.SetGeoTransform(geo_trans)
            ds_out.SetProjection(projection)
            band_out = ds_out.GetRasterBand(1)
            band_out.WriteArray(arr.reshape(rows, cols))
            band_out.SetNoDataValue(np.nan)
            band_out.SetDescription(desc)
            ds_out.FlushCache()
            ds_out = None
            out_paths.append(path)
            feedback.pushInfo(f'  Written: {fname}')

        # ── Auto-load results into QGIS ───────────────────────────────────────
        feedback.setProgress(95)
        for path in out_paths:
            name  = os.path.splitext(os.path.basename(path))[0]
            layer = QgsRasterLayer(path, name)
            if layer.isValid():
                context.temporaryLayerStore().addMapLayer(layer)
                context.addLayerToLoadOnCompletion(
                    layer.id(),
                    QgsProcessingContext.LayerDetails(name, QgsProject.instance(), name)
                )

        feedback.setProgress(100)
        feedback.pushInfo('RasterTrend analysis complete.')

        return {'OUTPUT_FOLDER': out_dir}

    def name(self):
        return 'mannykendalltrendanalysis'

    def displayName(self):
        return 'Mann-Kendall Trend Analysis'

    def group(self):
        return 'Trend Analysis'

    def groupId(self):
        return 'trendanalysis'

    def shortHelpString(self):
        return """
<h3>RasterTrend – Mann-Kendall Trend Analysis</h3>
<p>Performs pixel-wise monotonic trend detection on a time-ordered raster stack.</p>

<h4>Outputs</h4>
<ul>
  <li><b>sens_slope.tif</b> – Sen's Slope (trend magnitude per time step)</li>
  <li><b>p_value.tif</b> – Two-tailed p-value per pixel</li>
  <li><b>kendall_tau.tif</b> – Kendall's Tau correlation coefficient</li>
  <li><b>significance_mask.tif</b> – Binary mask: 1 = significant trend, 0 = not significant</li>
</ul>

<h4>Test Types</h4>
<ul>
  <li><b>Standard MK</b> – Use for annual or interannual data without strong seasonality</li>
  <li><b>Seasonal MK</b> – Use for monthly/seasonal data (e.g. NDVI, precipitation) to account for periodic cycles</li>
</ul>

<h4>Notes</h4>
<ul>
  <li>Input layers must share the same extent, resolution, and CRS</li>
  <li>Layers must be ordered chronologically</li>
  <li>Minimum 4 layers required; 10+ recommended for statistical reliability</li>
</ul>

<h4>Author</h4>
<p>Irfan Mahmood – Remote Sensing &amp; GIS Specialist<br>
<a href="https://github.com/mahmoodirfan">github.com/mahmoodirfan</a></p>
        """

    def createInstance(self):
        return RasterTrendAlgorithm()
