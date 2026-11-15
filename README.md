# Self-Potential (SP) Subsurface Delineation and Visualisation

A Python script for processing Self-Potential (SP) field measurements
along a geophysical traverse and producing 2D and 3D visualisations to
support preliminary subsurface delineation.

The script reads SP measurements from an Excel spreadsheet, assigns
geographic coordinates to measurement midpoints, interpolates the
readings onto a 2D section, and displays an extruded 3D block-style view
of the section.

## Features

-   Reads traverse SP data from an Excel workbook using `pandas`.
-   Converts start and end coordinates from degrees, minutes and seconds
    (DMS) to decimal degrees.
-   Interpolates latitude and longitude for each measurement midpoint
    along the traverse.
-   Organises SP readings collected at electrode spacings of 5, 10, 15,
    20, 25 and 30 (as represented by the spreadsheet column names).
-   Produces a 2D SP pseudosection with latitude, pseudodepth and
    colour-coded SP values.
-   Applies a tapered display boundary to the 2D section.
-   Produces a 3D block-style visualisation by extruding the
    interpolated 2D section across a user-defined display width.
-   Displays SP values in millivolts (mV).

## Important note about the outputs

The plots are visualisation products based on the supplied SP
measurements and the script's interpolation and display assumptions. The
vertical axis is generated from electrode spacing, multiplied by a fixed
factor of 1.34. It is therefore a **pseudodepth/display coordinate**,
not a measured or independently resolved geological depth.

The 3D view is created by extruding a single 2D traverse section across
an artificial width. It is **not a true 3D inversion or a multi-traverse
3D subsurface model**. The script does not perform an SP inversion,
estimate subsurface physical-property distributions, or uniquely
identify geological materials. Use the plots alongside field geology,
other geophysical results and ground-truth information when making
subsurface interpretations.

## Project files

A basic project folder can be organised as follows:

``` text
project-folder/
├── spyy.py
├── TR2_sp.xlsx
└── README.md
```

-   `spyy.py` --- the Python processing and plotting script.
-   `TR2_sp.xlsx` --- example input workbook. Replace this with your own
    traverse workbook or update the filename in the script.
-   `README.md` --- project documentation.

## Requirements

Use Python 3 and install the required packages:

``` bash
pip install numpy pandas matplotlib scipy openpyxl
```

The script uses:

-   **NumPy** for numerical arrays and coordinate calculations.
-   **Pandas** for reading and organising Excel data.
-   **Matplotlib** for 2D contour and 3D surface plots.
-   **SciPy** (`scipy.interpolate.griddata`) for spatial interpolation.
-   **openpyxl** as the Excel engine used by Pandas to read `.xlsx`
    files.

## Input Excel format

The workbook must contain a worksheet with the following columns:

  -----------------------------------------------------------------------
  Column                              Description
  ----------------------------------- -----------------------------------
  `Midpoint`                          Distance in metres along the
                                      traverse to the measurement
                                      midpoint.

  `a=5`                               SP reading for electrode spacing 5.

  `a=10`                              SP reading for electrode spacing
                                      10.

  `a=15`                              SP reading for electrode spacing
                                      15.

  `a=20`                              SP reading for electrode spacing
                                      20.

  `a=25`                              SP reading for electrode spacing
                                      25.

  `a=30`                              SP reading for electrode spacing
                                      30.
  -----------------------------------------------------------------------

Example layout:

    Midpoint      a=5     a=10      a=15     a=20     a=25     a=30
  ---------- -------- -------- --------- -------- -------- --------
         7.5   -57.78   -18.70   -204.60   123.00   -13.03   285.60
        12.5      ...      ...       ...      ...      ...      ...

The values above illustrate the expected table structure; replace them
with actual field readings. Keep the column names exactly as shown
because the script searches for these names. The `Midpoint` values
should be numeric and should use the same distance unit as the traverse
length (metres in the supplied configuration).

The script reads the first worksheet by default through
`pd.read_excel(excel_file)`. Ensure that the workbook has the intended
data on its first worksheet.

## Configure the traverse

Open `spyy.py` and edit the user configuration section at the bottom of
the file.

### 1. Set the Excel filename

``` python
excel_path = "TR2_sp.xlsx"
```

Change the filename to match your input workbook. If the workbook is in
another directory, provide its path.

### 2. Set the traverse length

``` python
traverse_total_length = 300
```

Enter the total measured traverse length in metres. The midpoint
distances in the Excel file must fall within this traverse length.

### 3. Enter the start and end coordinates

Provide both endpoints in DMS format:

``` python
start_point = {
    "lat": (6, 30, 17.26),
    "lon": (3, 23, 34.99)
}

end_point = {
    "lat": (6, 30, 30.17),
    "lon": (3, 23, 37.64)
}
```

Each tuple is `(degrees, minutes, seconds)`. The supplied conversion
function treats the values as positive coordinates. For locations in the
southern or western hemispheres, the coordinate sign must be handled
appropriately before using the script; the current implementation does
not accept hemisphere letters or negative DMS components explicitly.

### 4. Set the traverse name

``` python
traverse_name = "Traverse 2"
```

Use a name that identifies the profile in the generated plot titles.

## Run the script

From a terminal opened in the project folder, run:

``` bash
python spyy.py
```

The script reads the configured Excel workbook and displays the 2D and
3D Matplotlib figures. Close the plot windows to finish the run.

## How the script works

1.  **Load the data:** Reads the Excel workbook and removes leading or
    trailing spaces from column names.
2.  **Convert coordinates:** Converts the start and end
    latitude/longitude values from DMS to decimal degrees.
3.  **Locate the midpoints:** Uses linear interpolation between the
    traverse endpoints to assign a latitude and longitude to each
    midpoint distance.
4.  **Organise the readings:** Reshapes the available SP values into
    distance, electrode-spacing, reading and coordinate arrays.
5.  **Create the pseudodepth coordinate:** Converts electrode spacing to
    negative values and multiplies by 1.34 to establish the plotted
    vertical coordinate.
6.  **Interpolate the 2D section:** Uses linear `griddata` interpolation
    to estimate SP values on a regular latitude--pseudodepth grid.
7.  **Apply the display boundary:** Masks cells below a symmetric
    tapered boundary at the two ends of the section.
8.  **Build the 3D display:** Reconstructs the traverse coordinates and
    repeats the 2D SP section across a fixed cross-profile offset to
    create the block-style visualisation.
9.  **Plot the results:** Displays the 2D contour section and the 3D
    block-style view with SP colour scales.

## Outputs

### 2D SP coordinate pseudosection

The 2D figure displays interpolated SP values against latitude and the
script-generated pseudodepth coordinate. The colour scale represents SP
readings in mV.

### 3D solid block-style visualisation

The 3D figure displays the same interpolated SP section in geographic
coordinates and extends it across a fixed width for visual presentation.
The displayed width is controlled in the script by `extrusion_width` and
`w_steps`.

Neither output is automatically saved to an image file by the current
script; the figures are displayed with `plt.show()`. Use Matplotlib's
`savefig()` if you want to export figures.

## Assumptions and limitations

-   The traverse is represented by a straight-line interpolation between
    its start and end geographic coordinates.
-   The coordinate interpolation is linear in decimal latitude and
    longitude; it is not a geodesic calculation.
-   The midpoint distances and traverse length must use consistent
    units.
-   The script expects the electrode-spacing columns to be named `a=5`,
    `a=10`, `a=15`, `a=20`, `a=25` and `a=30`.
-   The fixed factor `1.34` is a display scaling factor in this
    implementation. It should not be treated as a validated conversion
    from electrode spacing to true investigation depth without a
    method-specific justification.
-   Linear interpolation can leave blank (`NaN`) areas where the
    requested grid lies outside the convex hull of the input points or
    where the input data are insufficient.
-   The 3D extrusion width is specified in decimal degrees in the code.
    A fixed angular offset does not represent a constant ground distance
    everywhere and is not a surveyed cross-line dimension.
-   The 3D plot repeats one traverse section across the extrusion width;
    it does not add independent subsurface information.
-   The current script displays plots but does not export figures,
    grids, or processed data files.
-   The script assumes the required Excel columns contain usable numeric
    values. Missing or non-numeric readings may need to be cleaned
    before processing.

## Suggested checks before interpretation

-   Confirm that the SP instrument readings, units, electrode
    arrangement and field procedures are documented.
-   Check that the traverse length, midpoint distances and endpoint
    coordinates are correct.
-   Inspect the input table for missing values, duplicated midpoints and
    inconsistent column names.
-   Compare the SP patterns with geological observations, topography,
    groundwater conditions and other available geophysical or
    geotechnical data.
-   Avoid assigning lithology, depth to a boundary, groundwater
    occurrence or other geological features from colour patterns alone.

## Possible future improvements

Potential extensions include exporting figures and interpolated grids,
allowing users to select electrode spacings, supporting multiple
traverses, using projected coordinates in metres for mapping, and
developing a properly constrained 3D workflow using independent
measurements from multiple profiles.

## Author and project information

Add the author's name, institution, project title, version, licence and
contact details here if the code will be shared publicly.

## Disclaimer

This code is provided as a research and visualisation aid. The quality
and meaning of the output depend on the input data, field acquisition,
coordinate information and processing assumptions. The figures should
not be treated as a definitive subsurface model or used as the sole
basis for engineering, groundwater or other site decisions.
