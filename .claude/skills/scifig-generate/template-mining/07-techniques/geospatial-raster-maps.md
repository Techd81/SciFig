# Technique: Geospatial Raster Maps

Use this when the source workflow reads aligned rasters, computes a pixel-wise
index, and renders continuous plus classified map outputs.

## TTOP Permafrost Raster Map

## Hallmark Elements

1. Read and align landtype, DDF, and DDT rasters before applying any formula.
2. Map land-cover classes to `rk` coefficients with an explicit dictionary.
3. Compute continuous TTOP as `(rk * DDT - DDF) / 365`.
4. Split visual output into two map panels: continuous TTOP magnitude and binary
   permafrost extent.
5. Preserve NoData or unmapped land classes as a visible category rather than
   silently recoding them as non-permafrost.
6. Use a diverging continuous color scale centered on zero for the TTOP panel.
7. Use a discrete class legend for `TTOP >= 0`, `TTOP < 0`, and NoData in the
   binary panel.
8. Include north-arrow and scale-bar context when geographic axes are hidden.

## Rendering Contract

```python
ttop = (rk_array * ddt - ddf) / 365.0
permafrost = np.where(np.isnan(ttop), np.nan, np.where(ttop < 0, 1, 0))

fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
axes[0].imshow(ttop, cmap="RdBu_r", norm=TwoSlopeNorm(vcenter=0))
axes[0].contour(ttop, levels=[0], colors="black", linestyles="--")
axes[1].imshow(class_map, cmap=ListedColormap([...]), norm=BoundaryNorm(...))
```

## QA Contract

- `continuous_raster_panel_count == 1`
- `binary_raster_panel_count == 1`
- `zero_contour_count >= 1`
- `discrete_legend_category_count >= 3`
- `colorbar_count >= 1`
- `nodata_preserved == true`
- `ttop_formula == "(rk * DDT - DDF) / 365"`

## Runtime Boundary

No public generator currently reads or writes GeoTIFF. For now, this motif is a
template-mining contract for raster-derived map figures; executable promotion
should add explicit raster dependency handling and NoData QA before exposing it
as a generator.

## Freeze-Thaw Raster Parameter Atlas

Use this when daily or regular-interval ground-temperature GeoTIFFs are stacked
by date and converted into freeze-thaw cycle parameters.

## Hallmark Elements

1. Parse dates from raster filenames and sort them before stacking.
2. Build a 3D raster stack with shape `(time, rows, cols)`.
3. Define the freeze-thaw cycle as July through the following June, not a plain
   calendar year.
4. Skip incomplete cycles before pixel-level metrics are computed.
5. For each pixel, use the first temperature below zero as `freeze_time`.
6. Use the last temperature below zero as `melt_time` or last frozen day.
7. Compute `freeze_duration` across year boundaries with leap-year handling.
8. Compute `actual_freeze_days` as below-zero sample count multiplied by the
   explicit `TIME_STEP_DAYS` assumption.
9. Preserve NoData masks across all derived output rasters.

## Rendering Contract

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 8.6))
panels = [
    (freeze_time, "Freeze start day", "DOY"),
    (melt_time, "Last frozen / melt day", "DOY"),
    (freeze_duration, "Freeze duration", "days"),
    (actual_freeze_days, "Actual frozen days", "days"),
]
for ax, (arr, title, label) in zip(axes.flat, panels):
    im = ax.imshow(arr, interpolation="nearest")
    fig.colorbar(im, ax=ax, label=label)
```

## QA Contract

- `parameter_panel_count == 4`
- `freeze_time_panel == true`
- `melt_time_panel == true`
- `freeze_duration_panel == true`
- `actual_freeze_days_panel == true`
- `colorbar_count == 4`
- `nodata_mask_panel_count == 4`
- `cycle_definition == "July 1 through next June 30"`
- `time_step_days` is present and documented

## Raster Zonal Statistics Export

Use this when the article or user request is not a map figure but a geospatial
source-data preparation step that batch-computes statistics for many GeoTIFFs
inside one vector boundary and exports the result table.

## Source-Data Contract

1. Load the Shapefile boundary once and keep all geometries for masking.
2. Iterate only raster files, using case-insensitive `.tif` detection.
3. Use `rasterio.mask.mask(..., crop=True)` to reduce the working raster window.
4. Use `rasterio.features.geometry_mask(..., invert=True)` after cropping so
   statistics are computed inside the exact polygon, not the crop rectangle.
5. Treat missing pixels as `NaN` or `dataset.nodata` only inside the polygon
   mask.
6. Record `valid_pixels`, `mask_pixels`, and `missing_pixels` before computing
   max, min, mean, and standard deviation.
7. Preserve rows for no-overlap, no-pixel, memory, and unknown-error cases so
   downstream figures can disclose missing source files.
8. Export the results table to Excel or CSV with one row per input raster.

## QA Contract

- `visual_chart_present == false`
- `export_table_present == true`
- `shapefile_mask_required == true`
- `geometry_mask_required == true`
- `nodata_nan_checked == true`
- `valid_pixel_count_column == true`
- `mask_pixel_count_column == true`
- `missing_pixel_count_column == true`
- `summary_stat_columns` contains `max`, `min`, `mean`, and `std`
- `error_rows_preserved == true`
- `excel_export_required == true` when the source specifically asks for Excel

## Temporal NoData Raster Fill

Use this when the article or user request repairs a damaged GeoTIFF by filling
NoData pixels from a complete historical same-period raster, then writes a new
metadata-preserving GeoTIFF. This is a source-data repair workflow, not a chart
motif.

## Source-Data Contract

1. Open the complete donor raster and target/incomplete raster explicitly.
2. Require matching shape, grid alignment, geotransform, and projection before
   pixel-level replacement.
3. Read each raster's NoData value from band metadata and fall back only when
   the source code provides a sentinel.
4. Convert both donor and target NoData sentinels to `NaN` before building the
   fill mask.
5. Fill only pixels where the target is missing and the donor is valid at the
   same row and column.
6. Preserve pixels as NoData when the donor is also missing.
7. Write a GeoTIFF output with the source geotransform, projection, dtype, and
   output band NoData value set.
8. Record target-missing, donor-filled, and still-missing pixel counts for QA.

## Rendering / Processing Contract

```python
donor = donor_band.ReadAsArray().astype(float)
target = target_band.ReadAsArray().astype(float)
donor[donor == donor_nodata] = np.nan
target[target == target_nodata] = np.nan

fill_mask = np.isnan(target)
filled = target.copy()
filled[fill_mask] = donor[fill_mask]
filled[np.isnan(filled)] = output_nodata
```

## QA Contract

- `visual_chart_present == false`
- `raster_preprocessing_present == true`
- `donor_raster_required == true`
- `target_raster_required == true`
- `aligned_shape_required == true`
- `nodata_to_nan == true`
- `fill_mask_formula == "np.isnan(target)"`
- `donor_fill_applied == true`
- `remaining_nodata_preserved == true`
- `geotransform_preserved == true`
- `projection_preserved == true`
- `output_nodata_set == true`
- `output_driver == "GTiff"`
- `target_missing_count`, `filled_pixel_count`, and
  `remaining_missing_count` are present
