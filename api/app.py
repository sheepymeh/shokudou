from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor

# remember to set the server timezone
from datetime import datetime

import config
from model import model

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config.DB_NAME}.db'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
db = SQLAlchemy(app)
executor = Executor(app)

buffer = {}
current = {}
graph_data = []
current_tick = 0

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
	setattr(QueueStatus, col, db.Column(db.Integer, nullable=False))

def update_tick():
	global current_tick
	current_tick = round(datetime.now().timestamp())
	current_tick = current_tick - current_tick % 60 + 15
update_tick()

@executor.job
def update_db(buffer):
	global current, graph_data

	# do our machine learning magics here with df
	preds = model(buffer)
	current = {f'stall{str(i)}': preds[i - 1] for i in range(1, config.NUM_STALLS + 1)}
	current['total'] = sum(preds)

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
	# db.session.delete(QueueStatus.query.filter(
	# 	QueueStatus.dow == dt_object.weekday(),
	# 	QueueStatus.hour == dt_object.hour,
	# 	QueueStatus.minute == dt_object.minute
	# ).first())
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
	update_tick()
	return True

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

	# scans were not complete in the previous minute
	if content['timestamp'] - 60 > current_tick:
		buffer = {}
		update_tick()

	buffer[content['mac']] = content['devices']

	if len(buffer) == config.NUM_DETECTORS:
		update_db.submit(buffer)
		buffer = {}

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

@app.route('/time', methods=['GET'])
def gettime():
	return str(round(datetime.now().timestamp()))
