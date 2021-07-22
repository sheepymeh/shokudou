# Shokudou

Shokudou is a website that provides real-time crowd information using Bluetooth signals. This solution requires ESP32s with WiFi and Bluetooth to be deployed around the area. The BlueTrace Lite protocol is used to prevent double-counting of devices.

## Applications
* Know before you go - Shokudou allows users to know what queues to expect before going
* Crowd management - Shokudou helps site operators to find out how best to minimize crowds
* Data collection - Shokoudou enables more nuanced data to be collected and analyzed

## Repository

This repository is split into three folders:
* ``api`` - backend API to process the data
* ``docs`` - frontend website, to be hosted by GitHub Pages
* ``micropython`` - micropython firmware to be run on the ESP32s

## Future Work

Work needs to be done to locate each device, most probably using the RSSI values returned from the ESP32s.

Additionally, a different method to identify each device needs to be found, in order to provide accurate results after the TraceTogether program ends.