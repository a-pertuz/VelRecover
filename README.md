# velrecover

A tool for interpolating 2D seismic velocity data from sparse velocity analysis found in seismic sections.

## Overview

velrecover helps geophysicists and seismic interpreters to create complete velocity models from sparse velocity picks. The application facilitates the interpolation of velocity data, visualization of results, and export in various formats suitable for seismic processing workflows.

## Installation

### Requirements
- Python 3.8 or higher
- Required Python packages:
  - PySide6
  - NumPy
  - pandas
  - appdirs
  - matplotlib
  - seisio

### Installation Methods

#### Using pip

```bash
pip install velrecover
```

#### From Source

```bash
pip install git+https://github.com/username/velrecover.git
```


## Getting Started

After installation, you can launch velrecover by running:

```bash
velrecover
```


### First Run Setup

When you run velrecover for the first time:

1. You'll be prompted to choose a data storage location
2. Example files will be copied to your selected location
3. The application will create the necessary folder structure

## Usage Guide

### Folder Structure

velrecover organizes data in the following folder structure:
- **SEGY/** - Store seismic SEGY files
- **VELS/RAW/** - Store input velocity data files
- **VELS/2D/** - Store interpolated velocity models

### Step-by-Step Workflow

#### Step 1: Load Velocity Data
1. Click "Load Text File"
2. Select a velocity text file (formats: .dat, .txt, .tsv, .csv)
3. The file should contain 3 columns: CDP, TWT, Velocity
4. View the velocity distribution in the scatter plot

#### Step 2: Load SEGY File
1. Click "Load SEGY File" 
2. Select a SEGY file (.sgy, .segy) that corresponds to the same seismic line
3. The SEGY file provides the spatial context for the interpolation

#### Step 3: Run Interpolation
1. Click "Interpolate" to process the data
2. The interpolation algorithm will fill gaps between sparse velocity picks
3. View the interpolated velocity model in the visualization window

#### Step 4: Apply Smoothing (Optional)
1. Enter a Gaussian blur value (1-100) in the text field
2. Click "Apply Gaussian Blur"
3. Higher values create smoother results

#### Step 5: Export Results
1. Click "Save Data as TXT" to export as text format
   - Saves X, Y coordinates and CDP, TWT, VEL values
2. Click "Save Data as BIN" to export in binary format
   - Saves velocity data in a grid (TWT, CDP) in float32 format
   - Suitable for migration in Seismic Unix

### Visualization Controls

The velocity visualization window provides several tools:
- **Pan**: Click and drag to move around
- **Zoom**: Use scroll wheel or click and drag to zoom
- **Reset View**: Return to original view
- **Save Figure**: Save the current visualization as an image

## Troubleshooting

If you encounter issues:
1. Check the console output in the main window
2. Ensure your input files are in the correct format
3. Try restarting the application

## License

velrecover is released under the GPL-3.0 License.

© 2025 Alejandro Pertuz
