# RasterTrend – Mann-Kendall Trend Analysis for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.16%2B-green)](https://qgis.org)
[![License](https://img.shields.io/badge/License-GPL--2.0-blue)](LICENSE)

A QGIS Processing plugin for pixel-wise monotonic trend detection on raster time series stacks using the **Mann-Kendall test** and **Sen's Slope estimator**.

---

## Features

- **Standard Mann-Kendall** – for annual/interannual data without strong seasonality
- **Seasonal Mann-Kendall** – for periodic data (e.g. monthly NDVI, precipitation) that accounts for seasonal cycles
- **Sen's Slope** – non-parametric trend magnitude estimator
- **Significance mask** – binary output at user-defined p-value threshold
- Fully integrated into the **QGIS Processing Toolbox** — works in batch mode and Model Builder
- No external dependencies beyond NumPy and SciPy (included in QGIS)

---

## Outputs

| File | Description |
|------|-------------|
| `sens_slope.tif` | Sen's Slope – trend magnitude per time step |
| `p_value.tif` | Two-tailed p-value per pixel |
| `kendall_tau.tif` | Kendall's Tau correlation coefficient |
| `significance_mask.tif` | 1 = significant trend, 0 = not significant |

---

## Installation

### From QGIS Plugin Repository
1. Open QGIS → **Plugins → Manage and Install Plugins**
2. Search for **RasterTrend**
3. Click **Install**

### Manual Installation
1. Download or clone this repository
2. Copy the `RasterTrend` folder to your QGIS plugins directory:
   - **Windows:** `C:\Users\<user>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux/Mac:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Open QGIS → **Plugins → Manage and Install Plugins → Installed**
4. Enable **RasterTrend**

---

## Usage

1. Open **Processing Toolbox** (`Ctrl+Alt+T`)
2. Navigate to **RasterTrend → Mann-Kendall Trend Analysis**
3. Configure parameters:
   - **Input raster layers** – select time-ordered raster stack
   - **Test type** – Standard or Seasonal Mann-Kendall
   - **Season period** – number of seasons per cycle (Seasonal MK only)
   - **Significance threshold** – p-value cutoff (default 0.05)
   - **Output folder** – where results will be saved
4. Click **Run**

---

## Input Requirements

- All input rasters must share the **same extent, resolution, and CRS**
- Layers must be **ordered chronologically**
- **Minimum 4 layers** required; 10+ recommended for statistical reliability
- Seasonal MK requires at least `2 × period` layers

---

## Statistical Background

### Mann-Kendall Test
Non-parametric test for monotonic trends in time series. Does not assume normality or homoscedasticity. Resistant to outliers. Widely used in hydrology, climatology, and vegetation monitoring.

### Seasonal Mann-Kendall
Extension of the standard MK test that computes statistics separately for each season before combining them. Prevents spurious trend detection caused by seasonal cycles in data like monthly NDVI or precipitation.

### Sen's Slope
Non-parametric estimator of trend magnitude. Computed as the median of all pairwise slopes across the time series. More robust than ordinary least squares for skewed or outlier-affected data.

---

## Example Applications

- NDVI trend analysis from Landsat/Sentinel-2 time series
- Precipitation or temperature trend detection from climate rasters
- Rangeland degradation monitoring
- Vegetation recovery assessment post-disturbance
- Cropland productivity trend mapping

---

## Citation

If you use RasterTrend in your research, please cite:

```
Mahmood, I. (2025). RasterTrend: A QGIS Plugin for Mann-Kendall Trend Analysis 
on Raster Time Series. GitHub: https://github.com/mahmoodirfan/RasterTrend
```

---

## Author

**Irfan Mahmood**  
Remote Sensing & GIS Specialist
📧 irfan-mahmood@outlook.com  
🔗 [github.com/mahmoodirfan](https://github.com/mahmoodirfan)

---

## License

GNU General Public License v2.0 — see [LICENSE](LICENSE)
