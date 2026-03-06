#!/bin/bash
# build-fritzing.sh
# Builds Fritzing 1.0.6 natively on Raspberry Pi 5 (Raspberry Pi OS Trixie ARM64)
# See https://backtobasic.dev for the full write-up
#
# Usage: bash build-fritzing.sh
# Estimated time: 20-40 minutes

set -e

echo "=== Fritzing Native Build for Raspberry Pi 5 (Trixie) ==="
echo ""

# --- Install dependencies ---
echo "[1/5] Installing build dependencies..."
sudo apt update -qq
sudo apt install -y \
  git \
  qt6-base-dev \
  qt6-base-dev-tools \
  qt6-serialport-dev \
  qt6-5compat-dev \
  qt6-svg-dev \
  libgit2-dev \
  libssl-dev \
  zlib1g-dev \
  libboost-dev \
  libsqlite3-dev \
  build-essential \
  libngspice0-dev \
  libquazip1-qt6-dev \
  libsvgpp-dev \
  libpolyclipping-dev

# --- Clone source ---
echo "[2/5] Cloning Fritzing source repositories..."
mkdir -p ~/git-repos
cd ~/git-repos

if [ -d "fritzing-app" ]; then
  echo "  fritzing-app already exists, pulling latest..."
  cd fritzing-app && git pull && cd ..
else
  git clone https://github.com/fritzing/fritzing-app.git
fi

if [ -d "fritzing-parts" ]; then
  echo "  fritzing-parts already exists, pulling latest..."
  cd fritzing-parts && git pull && cd ..
else
  git clone https://github.com/fritzing/fritzing-parts.git
fi

cd ~/git-repos/fritzing-app

# --- Patch build scripts ---
echo "[3/5] Patching build scripts for Trixie system libraries..."

# Raise Qt version ceiling from 6.5.10 to 6.8.99
sed -i 's/QT_MOST=6.5.10/QT_MOST=6.8.99/' phoenix.pro
echo "  patched phoenix.pro (Qt version ceiling)"

# Redirect ngspice
sed -i 's|NGSPICEPATH = ../../ngspice-42|NGSPICEPATH = /usr|' \
  pri/spicedetect.pri
echo "  patched spicedetect.pri"

# Redirect quazip
sed -i 's|QUAZIP_PATH=$$absolute_path($$PWD/../../quazip-$$QT_VERSION-$$QUAZIP_VERSION)intuisphere|QUAZIP_PATH=/usr|' \
  pri/quazipdetect.pri
sed -i 's|QUAZIP_INCLUDE_PATH=$$QUAZIP_PATH/include/QuaZip-Qt6-$$QUAZIP_VERSION|QUAZIP_INCLUDE_PATH=/usr/include/QuaZip-Qt6-1.4|' \
  pri/quazipdetect.pri
sed -i 's|QUAZIP_LIB_PATH=$$QUAZIP_PATH/lib|QUAZIP_LIB_PATH=/usr/lib/aarch64-linux-gnu|' \
  pri/quazipdetect.pri
echo "  patched quazipdetect.pri"

# Redirect svgpp
cat > pri/svgppdetect.pri << 'EOF'
# Copyright (c) 2021 Fritzing GmbH
message("Using fritzing svgpp detect script.")
SVGPPPATH=/usr
message("including $${SVGPPPATH}/include")
INCLUDEPATH += $${SVGPPPATH}/include
EOF
echo "  patched svgppdetect.pri"

# Redirect Clipper
sed -i 's|exists($$absolute_path($$PWD/../../Clipper1)) {|CLIPPER1=/usr|' \
  pri/clipper1detect.pri
sed -i 's|	            CLIPPER1 = $$absolute_path($$PWD/../../Clipper1/6.4.2)||' \
  pri/clipper1detect.pri
sed -i 's|				message("found Clipper1 in $${CLIPPER1}")||' \
  pri/clipper1detect.pri
sed -i 's|			}||' \
  pri/clipper1detect.pri
sed -i 's|INCLUDEPATH += $$absolute_path($${CLIPPER1}/include/polyclipping)|INCLUDEPATH += /usr/include/polyclipping|' \
  pri/clipper1detect.pri
sed -i 's|LIBS += -L$$absolute_path($${CLIPPER1}/lib) -lpolyclipping|LIBS += -L/usr/lib/aarch64-linux-gnu -lpolyclipping|' \
  pri/clipper1detect.pri
sed -i 's|QMAKE_RPATHDIR += $$absolute_path($${CLIPPER1}/lib)|QMAKE_RPATHDIR += /usr/lib/aarch64-linux-gnu|' \
  pri/clipper1detect.pri
echo "  patched clipper1detect.pri"

# Redirect libgit2
sed -i 's|LIBGITPATH = $$absolute_path($$_PRO_FILE_PWD_/../libgit2-$$LIBGIT_VERSION)|LIBGITPATH = /usr\nLIBGIT2LIB = /usr/lib/aarch64-linux-gnu|' \
  pri/libgit2detect.pri
sed -i 's|INCLUDEPATH += $$LIBGITPATH/include|INCLUDEPATH += /usr/include|' \
  pri/libgit2detect.pri
sed -i '64s|LIBGIT2LIB = $$LIBGITPATH/lib|LIBGIT2LIB = /usr/lib/aarch64-linux-gnu|' \
  pri/libgit2detect.pri
echo "  patched libgit2detect.pri"

# --- Configure ---
echo "[4/5] Configuring with qmake6..."
mkdir -p build
cd build
qmake6 ../phoenix.pro

# --- Compile ---
echo "[5/5] Compiling (this will take 20-40 minutes)..."
CORES=$(nproc)
echo "  using $CORES cores"
make -j${CORES}

# --- Create launcher ---
echo ""
echo "=== Build complete ==="
BINARY=~/git-repos/fritzing-app/build/Fritzing
if [ -f "$BINARY" ]; then
  echo "Binary: $BINARY ($(du -h $BINARY | cut -f1))"

  mkdir -p ~/.local/bin
  cat > ~/.local/bin/fritzing << 'LAUNCHEOF'
#!/bin/bash
~/git-repos/fritzing-app/build/Fritzing -parts ~/git-repos/fritzing-parts "$@"
LAUNCHEOF
  chmod +x ~/.local/bin/fritzing
  echo "Launcher created at ~/.local/bin/fritzing"

  # Desktop shortcut
  mkdir -p ~/.local/share/applications
  ICON=~/git-repos/fritzing-app/resources/system_icons/linux/fritzing_icon.png
  cat > ~/.local/share/applications/fritzing.desktop << DESKTOPEOF
[Desktop Entry]
Type=Application
Name=Fritzing
Comment=Electronic Design Automation
Exec=$(echo ~/.local/bin/fritzing)
Icon=$(echo $ICON)
Categories=Development;
Terminal=false
DESKTOPEOF
  echo "Desktop shortcut created"

  echo ""
  echo "Launch with:  fritzing"
  echo "           or ~/git-repos/fritzing-app/build/Fritzing -parts ~/git-repos/fritzing-parts"
else
  echo "ERROR: Binary not found — build may have failed. Check output above."
  exit 1
fi
