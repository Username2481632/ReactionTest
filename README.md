# ReactionTimer

A simple application built with Python and PySide6 to test user reaction times.

## Requirements

- Python 3.x (Developed with 3.13)
- Pip (Python package installer)

## Setup and Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/Username2481632/ReactionTimer.git
    cd ReactionTimer
    python -m venv venv
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install runtime dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Install development dependencies (needed for building/packaging):**
    ```bash
    pip install -r requirements-dev.txt
    ```

5.  **(Optional) Setup pre-commit hooks (for automatic AppImage build on commit):**
    ```bash
    pre-commit install
    ```

## How to Run

1.  Ensure your virtual environment is activated.
2.  Run the main application script:
    ```bash
    python src/reaction_test.py
    ```

## How to Build (AppImage for Linux)

1.  Ensure development dependencies are installed (see Setup step 4).
2.  Ensure pre-commit hooks are installed (see Setup step 5).
3.  The AppImage is built automatically via the pre-commit hook whenever you commit changes.
4.  The built AppImage can be found in the `out/` directory.

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