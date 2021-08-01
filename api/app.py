from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# remember to set the server timezone
from datetime import datetime
from copy import deepcopy

import config
from model import model

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config.DB_NAME}.db'
db = SQLAlchemy(app)

s = BackgroundScheduler()

buffer = {}
current = {}
graph_data = []
online_data = []
battery_data = {}

class QueueStatus(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	day = db.Column(db.Integer, nullable=False)
	month = db.Column(db.Integer, nullable=False)
	year = db.Column(db.Integer, nullable=False)
	dow = db.Column(db.Integer, nullable=False)
	hour = db.Column(db.Integer, nullable=False)
	minute = db.Column(db.Integer, nullable=False)
	total = db.Column(db.Integer, nullable=False)

	def __repr__(self):
		return '<QueueStatus %r>' % self.id
for col in [f'stall{str(i)}' for i in range(1, config.NUM_STALLS + 1)]:
	setattr(QueueStatus, col, db.Column(db.Integer))

def update_db():
	global buffer, current, graph_data, online_data
	if not buffer:
		return

	buffer_copy = deepcopy(buffer)
	buffer = {}
	online_data = list(buffer_copy.keys())

	# do our machine learning magics here with df
	preds = model(buffer_copy)
	current = {f'stall{str(i)}': preds[i - 1] for i in range(1, len(preds)+1)}
	current['total'] = sum(preds) if len(preds) == config.NUM_DETECTORS else round(config.NUM_DETECTORS / len(preds) * sum(preds))

	dt_object = datetime.now()
	db.session.add(QueueStatus(
		day=dt_object.day,
		month=dt_object.month,
		year=dt_object.year,
		dow=dt_object.weekday(),
		hour=dt_object.hour,
		minute=dt_object.minute,
		**current
	))
	db.session.commit()

	if dt_object.minute % 5 == 0:
		graph_data = []
		tmp = []
		for hour in range(9, 14):
			for minute in range(0, 60, 5):
				if hour == 9 and minute < 30: continue
				if hour == 13 and minute > 30: continue

				data = QueueStatus.query.with_entities(db.func.avg(QueueStatus.total).label('total')).filter(
					QueueStatus.dow == dt_object.weekday(),
					QueueStatus.hour == hour,
					QueueStatus.minute == minute,
				).first()

				tmp.append(data[0])
		graph_data = tmp

@app.route('/update', methods=['POST'])
def index():
	global buffer
	content = request.json
	if content == None:
		return jsonify({
			'success': False,
			'error': 'No POST body'
		}), 400
	if 'secret' not in content:
		return jsonify({
			'success': False,
			'error': 'Malformed POST body'
		}), 400
	if content['secret'] != config.SECRET:
		return jsonify({
			'success': False,
			'error': 'Invalid secret'
		}), 403

	buffer[content['mac']] = content['devices']
	battery_data[content['mac']] = content['battery']

	return jsonify({'success': True})

@app.route('/current', methods=['GET'])
def get_current():
	return jsonify({
		'success': True,
		'data': current,
	})

@app.route('/graph', methods=['GET'])
def graph():
	return jsonify({
		'success': True,
		'data': graph_data
	})

@app.route('/status', methods=['GET'])
def status():
	return jsonify({
		'success': True,
		'battery': battery_data,
		'online': online_data
	})

@app.route('/time', methods=['GET'])
def gettime():
	return str(int(time.time()))

s.add_job(func=update_db, trigger="cron", second=10)
s.start()