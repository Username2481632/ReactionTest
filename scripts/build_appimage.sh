#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
APP_NAME="ReactionTimer"
# Paths relative to project root
SCRIPT_NAME="src/reaction_timer.py"
ICON_NAME_PNG="assets/app_icon.png"
ICON_NAME_ICO="assets/app_icon.ico" # Icon for Windows
TROPHY_NAME="assets/trophy.svg"
APPIMAGETOOL_PATH="lib/appimagetool-x86_64.AppImage"
OUTPUT_DIR_NAME="dist" # Name of intermediate build dir
FINAL_OUT_DIR="out" # Name of final output dir

# --- Get Repo Root --- Must be run first!
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT" || exit 1

# --- Detect OS ---
OS_NAME="$(uname -s)"

# --- Clean Up Function ---
cleanup() {
    echo "--- Cleaning up previous build artifacts --- "
    rm -rf build/ "${OUTPUT_DIR_NAME}/" "${FINAL_OUT_DIR}/" "${APP_NAME}.desktop" "app_icon_256.png" "${APP_NAME}.spec" build/app_icon_temp.ico
}

# --- Build for Linux (AppImage) ---
build_linux() {
    echo "--- Building AppImage for Linux ---"
    ICON_NAME_RESIZED="app_icon_256.png" # Temporary resized icon in root

    # Check prerequisites
if [ ! -f "$APPIMAGETOOL_PATH" ]; then
        echo "Error: appimagetool not found at $APPIMAGETOOL_PATH" && exit 1
fi
if ! command -v pyinstaller &> /dev/null; then
        echo "Error: PyInstaller is not installed or not in PATH." && exit 1
fi
    if [ ! -f "$ICON_NAME_PNG" ]; then
        echo "Error: Original icon file '$ICON_NAME_PNG' not found." && exit 1
fi
if [ ! -f "$TROPHY_NAME" ]; then
        echo "Error: '$TROPHY_NAME' not found." && exit 1
fi

    # Create .desktop file
echo "--- Creating .desktop file ---"
cat > "${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Comment=Simple Reaction Test Game
Categories=Game;
EOF

    # Run PyInstaller (onedir for AppImage)
    echo "--- Running PyInstaller (onedir) ---"
pyinstaller \
    --noconfirm \
    --onedir \
    --distpath "${OUTPUT_DIR_NAME}" \
    --workpath build \
    --windowed \
    --add-data="${TROPHY_NAME}:assets/" \
        --add-data="${ICON_NAME_PNG}:assets/" \
        --icon="${ICON_NAME_PNG}" \
    --name "${APP_NAME}" \
    "${SCRIPT_NAME}"

    # Resize Icon
echo "--- Resizing icon to 256x256 ---"
    if ! command -v convert &> /dev/null; then
         echo "Warning: 'convert' command (ImageMagick) not found. Cannot resize icon."
    else
        /usr/bin/convert "${ICON_NAME_PNG}" -resize 256x256 "${ICON_NAME_RESIZED}"
if [ ! -f "$ICON_NAME_RESIZED" ]; then
            echo "Warning: Failed to resize icon using convert."
        fi
fi

    # Prepare AppDir Structure
echo "--- Preparing AppDir Structure ---"
    APPDIR="${OUTPUT_DIR_NAME}/${APP_NAME}"
    mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/lib" "${APPDIR}/usr/plugins/platforms" "${APPDIR}/usr/plugins/imageformats" "${APPDIR}/usr/plugins/iconengines"
rsync -a --remove-source-files "${APPDIR}/" "${APPDIR}/usr/bin/"
    if [ -f "$ICON_NAME_RESIZED" ]; then
cp "${ICON_NAME_RESIZED}" "${APPDIR}/${APP_NAME}.png"
    else
        cp "${ICON_NAME_PNG}" "${APPDIR}/${APP_NAME}.png" # Fallback to original
    fi
cp "${APP_NAME}.desktop" "${APPDIR}/"

    # Manually Copy Qt Plugins - REMOVED: PyInstaller handles this
    # echo "--- Manually copying required Qt plugins ---"
    # cp /usr/lib64/qt6/plugins/platforms/libqxcb.so "${APPDIR}/usr/plugins/platforms/" 2>/dev/null || echo "Warning: Could not copy libqxcb.so plugin."
    # cp /usr/lib64/qt6/plugins/imageformats/libqsvg.so "${APPDIR}/usr/plugins/imageformats/" 2>/dev/null || echo "Warning: Could not copy libqsvg.so plugin."
    # cp /usr/lib64/qt6/plugins/iconengines/libqsvgicon.so "${APPDIR}/usr/plugins/iconengines/" 2>/dev/null || echo "Warning: Could not copy libqsvgicon.so plugin."

    # Create AppRun
echo "--- Creating/Updating manual AppRun script ---"
cat > "${APPDIR}/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
export PATH="\${HERE}/usr/bin:\${PATH}"
export QT_PLUGIN_PATH="\${HERE}/usr/plugins"
exec "\${HERE}/usr/bin/${APP_NAME}" "\$@"
EOF
chmod +x "${APPDIR}/AppRun"

    # Run appimagetool
echo "--- Running appimagetool to package the AppDir ---"
mkdir -p "${FINAL_OUT_DIR}"
if [ -d "${APPDIR}" ]; then
    "${APPIMAGETOOL_PATH}" -n "${APPDIR}"
else
        echo "Error: AppDir ${APPDIR} not found." && exit 1
fi

    # Move AppImage
APPIMAGE_FILE="${APP_NAME}-x86_64.AppImage"
if [ -f "${APPIMAGE_FILE}" ]; then
     echo "AppImage created in current directory. Moving to ${FINAL_OUT_DIR}/ directory."
     mv "${APPIMAGE_FILE}" "${FINAL_OUT_DIR}/"
         echo "AppImage is located at: $(pwd)/${FINAL_OUT_DIR}/${APPIMAGE_FILE}"
else
     echo "Warning: AppImage file ${APPIMAGE_FILE} not found after appimagetool execution."
fi
}

# --- Build for Windows (.exe) ---
build_windows() {
    echo "--- Building EXE for Windows ---"
    TEMP_ICO_PATH="build/app_icon_temp.ico"
    ICON_ARG=""

    # Check prerequisites
    if ! command -v pyinstaller &> /dev/null; then
        echo "Error: PyInstaller is not installed or not in PATH." && exit 1
    fi
    if [ ! -f "$ICON_NAME_PNG" ]; then
        echo "Error: Source icon file '$ICON_NAME_PNG' not found." && exit 1
    fi
     if [ ! -f "$TROPHY_NAME" ]; then
        echo "Error: '$TROPHY_NAME' not found." && exit 1
    fi

    # Attempt to convert PNG to ICO automatically
    echo "--- Attempting to convert PNG to ICO ---"
    if ! command -v convert &> /dev/null; then
        echo "Warning: 'convert' command (ImageMagick) not found. Cannot create .ico file. Building without icon."
    else
        mkdir -p build # Ensure build directory exists for temp icon
        # Use explicit relative paths ./ for Windows compatibility
        echo "Running: magick convert \"${ICON_NAME_PNG}\" -define icon:auto-resize=256,128,64,48,32,16 \"${TEMP_ICO_PATH}\""
        if magick convert "${ICON_NAME_PNG}" -define icon:auto-resize=256,128,64,48,32,16 "${TEMP_ICO_PATH}"; then
            # Explicitly check if the file was created
            if [ -f "${TEMP_ICO_PATH}" ]; then
                echo "ICO file created successfully at ${TEMP_ICO_PATH}"
                ICON_ARG="--icon=${TEMP_ICO_PATH}" # Simplified argument without extra quotes
            else
                echo "Warning: magick convert seemed to succeed, but '${TEMP_ICO_PATH}' was not found. Building without icon."
                ICON_ARG=""
            fi
        else
            echo "Warning: Failed to convert PNG to ICO using magick convert. Building without icon."
            rm -f "${TEMP_ICO_PATH}" # Clean up potentially incomplete ico
            ICON_ARG=""
        fi
    fi

    # Create output directory
    mkdir -p "${FINAL_OUT_DIR}"

    # Run PyInstaller (onefile)
    echo "--- Running PyInstaller (onefile) ---"
    pyinstaller \
        --noconfirm \
        --onefile \
        --distpath "${FINAL_OUT_DIR}" \
        --workpath build \
        --windowed \
        --add-data="${TROPHY_NAME};assets/" \
        --add-data="${ICON_NAME_PNG};assets/" \
        ${ICON_ARG} \
        --name "${APP_NAME}" \
        "${SCRIPT_NAME}"

    echo "EXE build complete. Located in ${FINAL_OUT_DIR}/ directory."
}

# --- Main Build Logic ---
cleanup # Clean first

if [[ "$OS_NAME" == "Linux"* ]]; then
    build_linux
elif [[ "$OS_NAME" == "MINGW"* || "$OS_NAME" == "CYGWIN"* || "$OS_NAME" == "MSYS"* ]]; then
    build_windows
else
    echo "Unsupported OS: $OS_NAME. Skipping build."
fi

# --- Final Clean Up --- (Shared artifacts)
echo "--- Final cleanup of spec file and temp icon ---"
rm -f "${APP_NAME}.spec" build/app_icon_temp.ico

exit 0 