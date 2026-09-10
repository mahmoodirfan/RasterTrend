# RasterTrend
### Map gradual change through time.

A QGIS Processing plugin for pixel-wise Standard or Seasonal Mann–Kendall analysis and Sen’s slope estimation on time-ordered rasters.

**QGIS 3.16+ declared in plugin metadata** · Python · QGIS Processing

[Detailed guide](docs/guide.md) · [Report a problem](https://github.com/mahmoodirfan/RasterTrend/issues) · [Contribute](CONTRIBUTING.md)

## Start here

1. Load a small set of aligned, chronologically ordered raster layers. The algorithm reads **band 1 of each layer**.
2. Open **Processing Toolbox → RasterTrend → Trend Analysis → Mann-Kendall Trend Analysis**.
3. Select Standard or Seasonal Mann-Kendall. For monthly seasonal data, set the period to `12`.
4. Choose a significance threshold and a new output folder, then run.
5. Inspect slope, p-value and significance together. A significance mask alone does not describe effect size.

## Install

In QGIS, open **Plugins → Manage and Install Plugins** and search for **RasterTrend**. If a compatible listing is unavailable, install from this repository:

1. Download and extract the source archive.
2. Rename the extracted plugin directory to `RasterTrend` (remove a branch suffix such as `-main`).
3. In QGIS, open **Settings → User Profiles → Open Active Profile Folder**.
4. Copy the directory into `python/plugins/`, creating those subfolders if needed. `metadata.txt` and `__init__.py` must sit directly inside `python/plugins/RasterTrend/`.
5. Restart QGIS and enable **RasterTrend** in the plugin manager.

A GitHub source ZIP is not necessarily a correctly packaged QGIS install ZIP. Use the extracted-folder steps above for source downloads. Declared minimum versions are not a substitute for testing your QGIS build.

## What you get

| File | Meaning |
| :--- | :--- |
| `sens_slope.tif` | Median pairwise slope per input time step |
| `p_value.tif` | Two-sided approximate test p-value |
| `kendall_tau.tif` | Standard mode: Kendall's tau-a; see seasonal limitation below |
| `significance_mask.tif` | 1 where p ≤ selected threshold, otherwise 0 |

## Before interpreting results

- Use equally spaced dates and matching units, CRS, extent, dimensions and pixel alignment. This version does not check all alignment properties for you.
- Standard mode accepts at least 4 layers. Seasonal mode's interface accepts 2 cycles, but the current engine skips seasons with fewer than 3 observations: use **at least 3 complete cycles**.
- Pixels missing an observation anywhere in the stack are excluded.
- The current seasonal `kendall_tau.tif` contains S divided by Var(S), **not conventional Kendall's tau**. Do not report it as a correlation coefficient.
- Sen's slope uses all time-step pairs in both modes; it is not a season-specific slope estimator.
- The engine does not correct variance for ties, temporal autocorrelation or spatial multiple testing.
- The stack and pairwise slopes are held in memory. Begin with a small spatial subset.

## Documentation & support

The [detailed guide](docs/guide.md) contains extended settings, interpretation examples and workflow notes.

For a bug report, include your QGIS version, operating system, plugin version, parameters, Processing log and a small shareable example. See [contribution guidance](CONTRIBUTING.md).

## Related tools

[RasterTrend](https://github.com/mahmoodirfan/RasterTrend) · [TrendShift](https://github.com/mahmoodirfan/TrendShift) · [OpenGeoEnrich](https://github.com/mahmoodirfan/OpenGeoEnrich) · [spatialdrought](https://github.com/mahmoodirfan/spatialdrought)

## Author & license

**[Irfan Mahmood](https://github.com/mahmoodirfan)** · Remote Sensing & GIS Specialist  
[Email](mailto:irfan-mahmood@outlook.com) · [License](LICENSE)

For research use, cite the repository and record the version or commit you used. Existing citation details are retained in the detailed guide where provided.
