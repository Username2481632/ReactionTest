#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
APP_NAME="ReactionTest"
# Paths relative to project root
SCRIPT_NAME="src/reaction_test.py"
ICON_NAME="assets/app_icon.png"
TROPHY_NAME="assets/trophy.svg"
ICON_NAME_RESIZED="app_icon_256.png" # Temporary resized icon in root
APPIMAGETOOL_PATH="lib/appimagetool-x86_64.AppImage"
OUTPUT_DIR_NAME="dist" # Name of intermediate build dir
FINAL_OUT_DIR="out" # Name of final output dir

# --- Get Repo Root --- Must be run first!
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT" || exit 1

# --- Check Prerequisites ---
if [ ! -f "$APPIMAGETOOL_PATH" ]; then
    echo "Error: appimagetool not found at $APPIMAGETOOL_PATH"
    echo "Please download it from https://github.com/AppImage/appimagetool/releases"
    echo "and place it in the lib/ directory and make it executable (chmod +x appimagetool-x86_64.AppImage)."
    exit 1
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller is not installed or not in PATH."
    echo "Please install it using: pip install pyinstaller"
    exit 1
fi

if [ ! -f "$ICON_NAME" ]; then
    echo "Error: Original icon file '$ICON_NAME' not found."
    exit 1
fi

if [ ! -f "$TROPHY_NAME" ]; then
    echo "Error: '$TROPHY_NAME' not found."
    exit 1
fi


# --- Clean Up ---
echo "--- Cleaning up previous build artifacts --- "
# Clean artifacts relative to REPO_ROOT
rm -rf build/ "${OUTPUT_DIR_NAME}/" "${FINAL_OUT_DIR}/" "${APP_NAME}.desktop" "${ICON_NAME_RESIZED}" "${APP_NAME}.spec"


# --- Create .desktop file --- (in REPO_ROOT)
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
# Note: linuxdeploy expects the icon name without extension in Exec and Icon fields if using resources


# --- Run PyInstaller --- (Run from REPO_ROOT)
echo "--- Running PyInstaller ---"
pyinstaller \
    --noconfirm \
    --onedir \
    --distpath "${OUTPUT_DIR_NAME}" \
    --workpath build \
    --windowed \
    --add-data="${TROPHY_NAME}:assets/" \
    --add-data="${ICON_NAME}:assets/" \
    --icon="${ICON_NAME}" \
    --name "${APP_NAME}" \
    "${SCRIPT_NAME}"


# --- Resize Icon --- (Using paths relative to REPO_ROOT)
echo "--- Resizing icon to 256x256 ---"
/usr/bin/convert "${ICON_NAME}" -resize 256x256 "${ICON_NAME_RESIZED}"
if [ ! -f "$ICON_NAME_RESIZED" ]; then
    echo "Error: Failed to resize icon using convert."
    exit 1
fi


# --- Prepare AppDir Structure --- (Paths relative to REPO_ROOT)
echo "--- Preparing AppDir Structure ---"
APPDIR="${OUTPUT_DIR_NAME}/${APP_NAME}" # Path to the actual AppDir
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib"
mkdir -p "${APPDIR}/usr/plugins"

# Move PyInstaller output into usr/bin
# Source needs trailing slash, dest doesn't if it exists
rsync -a --remove-source-files "${APPDIR}/" "${APPDIR}/usr/bin/"
# Copy essential data files (trophy) - PyInstaller's add-data should handle this now
# cp "${TROPHY_NAME}" "${APPDIR}/usr/bin/"
# Copy resized icon and desktop file to AppDir root
cp "${ICON_NAME_RESIZED}" "${APPDIR}/${APP_NAME}.png"
cp "${APP_NAME}.desktop" "${APPDIR}/"

# --- Manually Copy Qt Plugins --- (Using absolute paths for source)
echo "--- Manually copying required Qt plugins ---"
# Ensure target plugin directories exist
mkdir -p "${APPDIR}/usr/plugins/platforms"
mkdir -p "${APPDIR}/usr/plugins/imageformats"
mkdir -p "${APPDIR}/usr/plugins/iconengines"
# Copy the plugins
cp /usr/lib64/qt6/plugins/platforms/libqxcb.so "${APPDIR}/usr/plugins/platforms/"
cp /usr/lib64/qt6/plugins/imageformats/libqsvg.so "${APPDIR}/usr/plugins/imageformats/"
cp /usr/lib64/qt6/plugins/iconengines/libqsvgicon.so "${APPDIR}/usr/plugins/iconengines/"
# We might need dependencies of these plugins too, but start with these.

# --- Manually Create AppRun --- 
echo "--- Creating/Updating manual AppRun script ---"
cat > "${APPDIR}/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
export PATH="\${HERE}/usr/bin:\${PATH}"
# Set QT_PLUGIN_PATH to find plugins copied above
export QT_PLUGIN_PATH="\${HERE}/usr/plugins"

# Execute the main binary
exec "\${HERE}/usr/bin/${APP_NAME}" "\$@"

EOF
# Make AppRun executable
chmod +x "${APPDIR}/AppRun"


# --- Run appimagetool to package the AppDir ---
echo "--- Running appimagetool to package the AppDir ---"
# Create output directory for the final AppImage
mkdir -p "${FINAL_OUT_DIR}"

if [ -d "${APPDIR}" ]; then
    # The output filename will be based on the desktop file name + architecture
    # Add -v for verbose output from appimagetool if needed
    "${APPIMAGETOOL_PATH}" -n "${APPDIR}"
    # Optionally, rename the output if needed:
    # mv "${APP_NAME}-x86_64.AppImage" ./${APP_NAME}.AppImage
else
    echo "Error: AppDir ${APPDIR} not found after manual AppDir creation."
    exit 1
fi

# Move the created AppImage into the final output dir
APPIMAGE_FILE="${APP_NAME}-x86_64.AppImage"
if [ -f "${APPIMAGE_FILE}" ]; then
     echo "AppImage created in current directory. Moving to ${FINAL_OUT_DIR}/ directory."
     mv "${APPIMAGE_FILE}" "${FINAL_OUT_DIR}/"
else
     echo "Warning: AppImage file ${APPIMAGE_FILE} not found after appimagetool execution."
fi

# --- Final Clean Up --- (Relative to REPO_ROOT)
echo "--- Cleaning up intermediate files ---"
rm -rf build/ "${OUTPUT_DIR_NAME}/" "${APP_NAME}.desktop" "${ICON_NAME_RESIZED}" "${APP_NAME}.spec"

echo "--- Build Complete --- Optionally clean up dist/ directory manually ---"
echo "AppImage is located at: $(pwd)/${FINAL_OUT_DIR}/${APPIMAGE_FILE}"

exit 0 