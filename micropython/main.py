# pylint: disable=import-error

import machine
import micropython
import config
import ubluetooth
import gc
from network import WLAN, STA_IF
from ujson import dumps
from urequests import get, post
from ubinascii import hexlify
from utime import time, gmtime, sleep_ms
from ble_advertising import decode_services

_IRQ_SCAN_RESULT = micropython.const(5)
_IRQ_SCAN_DONE = micropython.const(6)

_BLE_SCAN_TIME = micropython.const(10000)
_BLE_SCAN_INTERVAL = micropython.const(250)
_BLE_SCAN_WINDOW = micropython.const(250)

_TT_UUID = ubluetooth.UUID(0xffff)

if config.DEBUG:
	import ssd1306
	i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), freq=10000000)
	oled = ssd1306.SSD1306_I2C(128, 64, i2c)

	from neopixel import NeoPixel
	np = NeoPixel(machine.Pin(13), 1)
	np[0] = (0, 3, 0)
	np.write()

class Battery:
	def __init__(self, vadc=35):
		self.VBAT = machine.ADC(machine.Pin(vadc))
		self.VBAT.width(machine.ADC.WIDTH_12BIT)
		self.VBAT.atten(machine.ADC.ATTN_11DB)
		self.CALIB = micropython.const(3.6 * 2)
		self.VMIN = micropython.const(round(3.4 / self.CALIB * 4096))
		self.VMAX = micropython.const(round(4.3 / self.CALIB * 4096))
	def voltage(self): return self.VBAT.read() / 4096 * self.CALIB
	def percentage(self): return (self.VBAT.read() - self.VMIN) / (self.VMAX - self.VMIN)

def log(msg):
	if not config.DEBUG: return
	print('[LOG] {}'.format(msg))
	if type(msg) == str:
		oled.fill(0)
		msg = msg.split()
		offset = 0
		line = ''
		for word in msg:
			if len(line + word) < 16:
				line += word
			else:
				oled.text(line, 0, offset)
				offset += 10
				line = word
			line += ' '
			oled.text(line, 0, offset)
		oled.show()

wdt = machine.WDT(timeout=_BLE_SCAN_TIME+500)
wdt.feed()

BAT = Battery()
devices = {}
wlan = WLAN(STA_IF)

def connect_wlan(set_time=False, clear_rtc_ram=False):
	global wlan
	rtc = machine.RTC()
	# Cache data about WLAN network
	saved_info = False if clear_rtc_ram else rtc.memory()
	# Renew connection if killed by WDT
	rtc.memory(b'')
	first_conn = False

	wlan.active(True)
	if not saved_info:
		log('Scanning for WLAN network')
		first_conn = True
		ap_list = wlan.scan()
		# APs are sorted by RSSI by default
		for ap in ap_list:
			if ap[0].decode('utf-8') == config.WIFI_SSID:
				saved_info = (ap[1], ap[2].to_bytes(1, 'big'))
				break
		if not saved_info:
			log('WLAN network not found')
			machine.reset()
	else:
		saved_info = saved_info.split(b'|')
		wlan.ifconfig((saved_info[2], saved_info[3], saved_info[4], '1.1.1.1'))

	if config.WIFI_USER:
		wlan.seteap(config.WIFI_USER, config.WIFI_PASS)
		wlan.connect(config.WIFI_SSID, bssid=saved_info[0], channel=int.from_bytes(saved_info[1], 'big'))
	else:
		wlan.connect(config.WIFI_SSID, config.WIFI_PASS, bssid=saved_info[0], channel=int.from_bytes(saved_info[1], 'big'))

	log('Connecting to WLAN network')
	while not wlan.isconnected(): machine.idle()
	wdt.feed()
	if first_conn:
		ifconfig = wlan.ifconfig()
		saved_info = (ap[1], ap[2].to_bytes(1, 'big'), bytes(ifconfig[0], 'ascii'), bytes(ifconfig[1], 'ascii'), bytes(ifconfig[2], 'ascii'))
	rtc.memory(b'|'.join(saved_info))

	# Set time on boot and after every half hour
	if time() % 1800 < 85 or set_time:
		epoch = int(get('http://{}/time'.format(config.API_URL)).text)
		tm = gmtime(epoch - 946684800)
		rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
		wdt.feed()
	if config.DEBUG:
		t = rtc.datetime()
		log('Time is {}/{}/{} {}:{}:{}'.format(t[0], t[1], t[2], t[4], t[5], t[6]))

	return wlan

def upload(mac):
	battery = round(BAT.percentage(), 3)
	post(
		'http://{}/update'.format(config.API_URL),
		headers={
			'content-type': 'application/json'
		},
		data=dumps({
			'devices': {hexlify(key).decode('utf-8')[22:]: data[0] // data[1] for (key, data) in devices.items()},
			'mac': mac,
			'battery': battery,
			'timestamp': time() + 946684800,
			'secret': config.SECRET
		})
	)
	return battery < 0.3

@micropython.native
def bt_irq(event, data):
	global bt, devices
	if event == _IRQ_SCAN_RESULT:
		if config.DEBUG:
			global np
			np[0] = (0, 0, 7)
			np.write()
		_, _, adv_type, rssi, adv_data = data
		if (adv_type not in (0x00, 0x03) or
			_TT_UUID not in decode_services(adv_data) or
			rssi < -95): return
		# if adv_data[6:22] == '0303ffff1716ffff' and len(adv_data) == 62:
		adv_data = bytes(adv_data)
		if adv_data not in devices:
			devices[adv_data] = [rssi, 1]
		else:
			devices[adv_data][0] += rssi
			devices[adv_data][1] += 1
		if config.DEBUG:
			np[0] = (0, 0, 3)
			np.write()
	elif event == _IRQ_SCAN_DONE:
		global wlan
		wdt.feed()
		bt.active(False)
		del bt

		if config.DEBUG:
			global np
			np[0] = (0, 3, 0)
			np.write()
			log('Scan finished')
			log('{} devices'.format(str(len(devices))))
		gc.collect()

		# Consider hashing TT UUIDs using uhashlib
		connect_wlan()
		wdt.feed()

		low_battery = upload(hexlify(wlan.config('mac')).decode())
		wlan.active(False)
		wdt.feed()
		log('Uploaded to API')

		if config.DEBUG:
			np[0] = (0, 0, 0)
			np.write()
			oled.poweroff()
		elif low_battery:
			from neopixel import NeoPixel
			np = NeoPixel(machine.Pin(13), 1)
			np[0] = (7, 0, 0)
			np.write()
			machine.deepsleep()
		elif time() % 86400 >= (config.SLEEP - int(config.TZ) * 3600) and not config.DEBUG:
			machine.deepsleep(((86400 + (config.WAKE - (1 + int(config.TZ)) * 3600)) - time() % 86400) * 1000)
		machine.deepsleep(round(((70 - round(time())) % 60) * 1000))
	machine.idle()

if time() < 631152000:
	connect_wlan(True)
if time() % 86400 <= (config.WAKE - int(config.TZ) * 3600) and not config.DEBUG:
	print('Condition 1')
	connect_wlan(True, True)
	machine.deepsleep(((config.WAKE - int(config.TZ) * 3600) - time() % 86400) * 1000)
wlan.active(False)

bt = ubluetooth.BLE()
bt.active(True)
bt.config(gap_name='Shokudou')
bt.config(addr_mode=0x01)
bt.irq(bt_irq)
gc.collect()
bt.gap_scan(_BLE_SCAN_TIME, _BLE_SCAN_INTERVAL, _BLE_SCAN_WINDOW)
if config.DEBUG:
	np[0] = (0, 0, 3)
	np.write()
log('Scanning')
wdt.feed()
