# VelRecover

[![DOI](https://zenodo.org/badge/DOI/zenodo.15053268.svg)](https://doi.org/10.5281/zenodo.15053268)
![PyPI](https://img.shields.io/pypi/v/velrecover)
![Last Commit](https://img.shields.io/github/last-commit/a-pertuz/velrecover)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-yellow.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-green)

A Python tool for interpolating 2D seismic velocity data from sparse velocity analysis found in seismic sections. VelRecover provides multiple interpolation algorithms to create complete velocity fields from sparse velocity picks, with an intuitive GUI for visualization and quality control.

VelRecover is part of the [REVSEIS](https://a-pertuz.github.io/REVSEIS/index.html) suite. A collection of open source tools to digitize and enhance vintage seismic sections. See [REVSEIS](https://a-pertuz.github.io/REVSEIS/index.html) for more information.

## Features

- **Multiple Interpolation Methods** - Linear, logarithmic, RBF, and two-step interpolation algorithms
- **User-friendly GUI** - Intuitive tabbed interface for the entire workflow
- **Velocity Editing** - Tools to add, modify, and delete velocity picks
- **Gaussian Smoothing** - Apply adjustable smoothing to interpolated velocity models
- **Real-time Visualization** - Interactive visualization of input data and interpolation results
- **Multiple Export Formats** - Save velocity models as text or binary files
- **Data Integration** - Direct overlay of velocity data on seismic SEGY sections
- **Velocity Distribution Analysis** - Analyze velocity trends and distributions

## Citation

If you use this software in your research, please cite it as:

```
Pertuz, A. (2025). VelRecover: A Python tool for interpolating sparse 2D seismic velocity data from vintage seismic sections. Zenodo. https://doi.org/10.5281/zenodo.15053268
```

Check the Zenodo repository: https://doi.org/10.5281/zenodo.15053268


## Installation

### For Windows Users

1. **Install Python** (if not already installed):
   - Download Python from [python.org](https://www.python.org/downloads/windows/)
   - During installation, make sure to check **"Add Python to PATH"**
   - Click "Install Now" and wait for installation to complete

2. **Install VelRecover**:
   - Open Command Prompt (search for "cmd" in Windows search)
   - Type the following command and press Enter:

   ```
   pip install velrecover
   ```

   Alternatively, install directly from GitHub:
   ```
   pip install git+https://github.com/a-pertuz/velrecover.git
   ```

3. **Launch the program**:
   After installation, simply type:
   ```
   velrecover
   ```

4. **First Run Setup**
   When you run VelRecover for the first time:

   - You'll be prompted to choose a data storage location
   - Example files will be copied to your selected location
   - The application will create the necessary folder structure


## File Structure

VelRecover uses the following folder structure:

```
velrecover/
├── SEGY/                 # Store seismic SEGY files
├── VELS/                 # Main velocity data directory
│   ├── RAW/              # Store input velocity data files
│   ├── CUSTOM/           # Store edited velocity picks
│   └── INTERPOLATED/     # Store interpolated velocity models
│       ├── TXT/          # Text format outputs
│       └── BIN/          # Binary format outputs
└── LOG/                  # Store log files
```

The application automatically creates these folders if they don't exist.

## Quick Start

1. Run `velrecover`
2. In the **Welcome** tab, click "Start New Project"
3. In the **Load Data** tab:
   - Click "Load Text File" to select a velocity file
   - Click "Load SEGY File" to load corresponding seismic data
   - Click "Next" to proceed
4. In the **Edit** tab:
   - Use the tools to add, edit, or delete velocity picks if needed
   - Apply time shifts if necessary
   - Click "Save Edits" to save your changes or "Continue Without Edits"
5. In the **Interpolate** tab:
   - Select an interpolation method (RBF, Linear, Logarithmic, etc.)
   - Configure any method-specific parameters
   - Optionally enable Gaussian blur for smoothing
   - Click "Run Interpolation"
   - Review the results
6. Save the interpolated velocity model:
   - Click "Save as Text" for text format output
   - Click "Save as Binary" for binary format output

### Interpolation Methods

VelRecover offers several interpolation methods:

- **RBF Interpolation** - Uses Radial Basis Function interpolation for a smooth model that honors all data points
- **Linear Best Fit** - Fits a best linear velocity model using least squares regression
- **Linear Custom** - Creates a linear velocity model with custom initial velocity and gradient parameters
- **Logarithmic Best Fit** - Fits a best logarithmic velocity model using non-linear regression
- **Logarithmic Custom** - Creates a logarithmic model with custom base velocity and coefficient parameters
- **Two-Step Method** - First interpolates each trace with velocity picks using RBF, then completes the model using nearest neighbor and smooths the results

### System Requirements
- Windows, Linux, or macOS
- At least 4GB RAM
- Python 3.8 or higher

### Common Issues
- **Program not found**: Ensure Python is added to your PATH
- **Missing dependencies**: Try running `pip install <package_name>`

### Creating a Desktop Shortcut
1. Right-click on your desktop
2. Select "New" → "Shortcut"
3. Type `python -m velrecover` or just `velrecover` (if installed via pip)
4. Click "Next" and give the shortcut a name (e.g., "VelRecover")
5. Click "Finish"


## License

This software is licensed under the GNU General Public License v3.0 (GPL-3.0).

You may copy, distribute and modify the software as long as you track changes/dates in source files. 
Any modifications to or software including (via compiler) GPL-licensed code must also be made available 
under the GPL along with build & installation instructions.

For the full license text, see [LICENSE](LICENSE) or visit https://www.gnu.org/licenses/gpl-3.0.en.html

---

*For questions, support, or feature requests, please contact Alejandro Pertuz at apertuz@ucm.es*
