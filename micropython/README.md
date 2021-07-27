# MicroPython Firmware for ESP32

The Shokudou network is based on multiple battery-operated ESP32s (ESP32-WROVER-B on [STACK the Flags C01Ns](https://github.com/c01nrepo)) placed in the area around the location to be tracked. Each ESP32 collects the IDs of as many TraceTogether devices as possible (based on the [BlueTrace Lite](https://www.developer.tech.gov.sg/assets/files/TT_Token_Technical_Writeup.pdf) protocol). They then upload the tokens found to the server, along with RSSI data and metadata about the identity and status of the ESP32 (battery level, MAC address, and timestamp). This runs every minute during the peak hours, which are 9:30 to 13:30 every day.

A ``config.py`` file must be uploaded to the ESP32 in the same directory as ``main.py`` with the following variables:
```python
DEBUG = True
WIFI_SSID = '<WiFi SSID>'
WIFI_USER = '<WPA2 Enterprise Username> (if not using WPA/WPA2 Personal)'
WIFI_PASS = '<WiFi Password>'
API_URL = '<API Hostname/IP>'
SECRET = '<API Secret>'
TZ = '<Timezone like +8>'
WAKE = '<Seconds into day>'
SLEEP = '<Seconds into day>'
```

``urequests`` is installed using ``upip`` on first boot automatically.

Additional files included are [``ble_advertising.py``](https://github.com/micropython/micropython/blob/master/examples/bluetooth/ble_advertising.py) and [``ssd1306.py``](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).

## Debugging

When ``DEBUG`` is set to ``True`` in ``config.py``, additional debugging information is given. They are usually not provided to save power.

Logs are printed to the serial console. Additionally, same logs are shown on the OLED display.

NeoPixels flash and change color to provide additional information:
* Solid green: before or after scanning
* Dim blue: scanning
* Flashing blue: scanning, BlueTrace Lite device found

## Firmware

Custom MicroPython firmware was built to enable additional features. The provided script and binary are based on MicroPython 1.15 and ESP-IDF 4.2. You can build the firmware by running ``firmware/build.sh``. The build does not include SPIRAM support although the C01N does support it.

Additional features:
* WPA2 Enterprise authentication (based on [this post](https://forum.micropython.org/viewtopic.php?f=18&t=7219#p41036)), to allow for use in enterprise settings.
  ```python
  WLAN.seteap('username', 'password')
  ```
* WiFi channel selection (based on [this post](https://forum.micropython.org/viewtopic.php?f=16&t=7964&p=45347#p45370)), to (hopefully) resolve a problem with WiFi connections not being established
  ```python
  WLAN.connect('ssid', 'wpa2_personal_password', bssid=b'bssid', channel=int)
  ```
* Disabled multi-core mode to save power as our code doesn't benefit from the second core (based on [this commit]()https://github.com/micropython/micropython/commit/92149c8a7954169285b2909012dc601c6e7cb0aa)
* Set SoC frequency to 80MHz to save power
* Disabled ULP co-processor
* Removed unnecessary packages and install urequests by default to make the package a little smaller

