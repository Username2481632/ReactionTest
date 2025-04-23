# ReactionTimer

[![Build Status](https://github.com/Username2481632/ReactionTimer/actions/workflows/build.yml/badge.svg)](https://github.com/Username2481632/ReactionTimer/actions/workflows/build.yml)

A simple application built with Python and PySide6 to test user reaction times.

## Requirements

- Python 3.12
- Pip (Python package installer)
- (Optional) ImageMagick (`convert` command) - For building the Windows `.exe` with an icon locally.

## Setup and Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/Username2481632/ReactionTimer.git
    cd ReactionTimer
    ```

2.  **Create and activate a Python 3.12 virtual environment:**
    ```bash
    # Ensure you have Python 3.12 installed
    python3.12 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install runtime dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Install development dependencies (needed for type checking, pre-commit hooks):**
    ```bash
    pip install -r requirements-dev.txt
    ```

5.  **(Optional) Setup pre-commit hooks (for automatic type checking on commit):**
    ```bash
    pre-commit install
    ```

## How to Run

1.  Ensure your Python 3.12 virtual environment is activated.
2.  Run the main application script:
    ```bash
    python src/reaction_timer.py
    ```

## Type Checking (pytype)

This project uses `pytype` for static type checking.

- **Automatic:** It runs automatically as a pre-commit hook if installed (Setup step 5).
- **Manual:** You can run it manually using:
    ```bash
    ./scripts/run_pytype.sh
    ```

## Builds (AppImage & EXE)

Builds for Linux (AppImage) and Windows (.exe) are handled automatically via **GitHub Actions** whenever changes are pushed to the `master` branch.

- **Download:** You can download the latest builds from the [Actions tab](https://github.com/Username2481632/ReactionTimer/actions) of the repository. Look for the "Build Application" workflow and download the artifacts named `ReactionTimer-AppImage` or `ReactionTimer-Windows`.
- **Local Build (Optional):** If you need to build locally, ensure development dependencies are installed and run the build script:
    ```bash
    ./scripts/build_appimage.sh
    ```
    *(Note: Building the `.exe` locally requires running this script on Windows. Icon conversion requires ImageMagick.)*

## Features

- Measures reaction time to a visual cue (color change).
- Displays reaction time in seconds (e.g., 0.XXX s).
- Tracks and displays the user's best reaction time.
- Provides visual feedback for pressing too early.
- Uses the SPACE bar for interaction.
- Features a visually responsive interface that adapts to window size.
- Includes animations for feedback (error shake, best time trophy).
- Simple gameplay loop: Press SPACE to start/retry.

## License

This project is licensed under the GNU Lesser General Public License v3.0 - see the [LICENSE](LICENSE) file for details. 