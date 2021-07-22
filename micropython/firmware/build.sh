#!/bin/sh
if which nproc > /dev/null; then
    MAKEOPTS="-j$(nproc)"
else
    MAKEOPTS="-j$(sysctl -n hw.ncpu)"
fi

if [ ! -d 'esp-idf' ]; then
git clone -b v4.2 https://github.com/espressif/esp-idf.git -j4
git -C esp-idf checkout $1
git -C esp-idf submodule update --init \
    components/bt/controller/lib \
    components/bt/host/nimble/nimble \
    components/esp_wifi \
    components/esptool_py/esptool \
    components/lwip/lwip \
    components/mbedtls/mbedtls
./esp-idf/install.sh
fi
export IDF_PATH=$PWD/esp-idf
. ./esp-idf/export.sh

[ -d 'micropython' ] && rm -rf micropython
git clone -b v1.15 https://github.com/micropython/micropython.git
[ ! -d 'micropython-lib' ] && git clone https://github.com/micropython/micropython-lib.git

sed -i 's/esp_wifi/esp_wifi\n    wpa_supplicant/' micropython/ports/esp32/main/CMakeLists.txt
mkdir micropython/ports/esp32/boards/C01N_SHOKUDOU
cp manifest.py micropython/ports/esp32/boards
cp modnetwork.c micropython/ports/esp32
cp mpconfigboard.cmake micropython/ports/esp32/boards/C01N_SHOKUDOU
cp mpconfigboard.h micropython/ports/esp32/boards/C01N_SHOKUDOU
cp sdkconfig.coin micropython/ports/esp32/boards

cd micropython
make -C mpy-cross
cd ports/esp32
make submodules
make ${MAKEOPTS} BOARD=C01N_SHOKUDOU