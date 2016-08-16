from google.appengine.ext.ndb.key import Key

import wtforms
import wtforms_components
import datetime

from control import base_auth_response
from flask import make_response, render_template, Response, flash, redirect
from flask_wtf import Form

from flask_restful import Resource

from auth import auth
from main import api, app
from model import BaseCategory, BaseMetric, BaseActivity, BaseRecord


class RecordForm(Form):
	activity = wtforms.HiddenField('Activity', [wtforms.validators.required()])
	category = wtforms.HiddenField('Category', [wtforms.validators.required()])
	value = wtforms.StringField('Value', [wtforms.validators.required()])
	date = wtforms.DateField('Date', [wtforms.validators.optional()])
	notes = wtforms.TextAreaField('Notes', [wtforms.validators.optional()])

	def __init__(self, *args, **kwargs):
		super(RecordForm, self).__init__(*args, **kwargs)
		cats, _ = BaseCategory.get_dbs()
		self.category.choices = [(cat.key.urlsafe(), cat.name) for cat in cats]

	def new(self, activity):
		self.activity.data = activity.key.urlsafe()
		self.category.data = activity.category_key.urlsafe()
		return self

	def edit(self, record):
		self.activity.data = record.activity.urlsafe()
		self.category.data = record.category.urlsafe()
		self.value.data = record.value
		self.date.data = record.date
		self.notes.data = record.notes
		return self


class TimeRecordForm(RecordForm):
	value = wtforms_components.TimeField('Time', [wtforms.validators.required()])


class Activities(Resource):
	@auth.login_required
	def get(self, category_key):
		user_key = auth.current_user_key()
		cat = Key(urlsafe=category_key).get()
		activities = BaseActivity.get_dbs(user_key=user_key, tracked=True, category_key=cat.key)[0]
		records = [BaseRecord.get_dbs(user_key=user_key, activity_key=a.key)[0] for a in activities]
		return base_auth_response('records/records.html', activities=zip(activities, records))


class NewRecord(Resource):
	@auth.login_required
	def get(self, activity_key):
		a = Key(urlsafe=activity_key).get()
		form = RecordForm().new(a)
		return base_auth_response('records/new_record.html', form=form, activity=a)

	@auth.login_required
	def post(self, activity_key):
		record = Key(urlsafe=activity_key).get()
		form = RecordForm()
		if form.validate_on_submit():
			entity = BaseRecord()
			form.populate_obj(entity)
			entity.user_key = auth.current_user_key()
			if entity.is_valid_entry(form):
				entity.put()
				flash('Toevoegen succesvol.', category='success')
				return redirect(api.url_for(Activities, category_key=record.category_key))
		flash('Toevoegen niet gelukt.', category='warning')
		return base_auth_response('records/new_record.html', form=form)


class InitActivities(Resource):
	@staticmethod
	def get():
		x, _ = BaseCategory.get_dbs()
		for y in x:
			y.key.delete()
		x, _ = BaseMetric.get_dbs()
		for y in x:
			y.key.delete()
		x, _ = BaseActivity.get_dbs()
		for y in x:
			y.key.delete()
		x, _ = BaseRecord.get_dbs()
		for y in x:
			y.key.delete()

		crossfit = BaseCategory(name="Crossfit").put()
		running = BaseCategory(name="Running").put()
		lifting = BaseCategory(name="Lifting").put()

		dist = BaseMetric(name="Distance").put()
		time = BaseMetric(name="Time").put()
		amrap = BaseMetric(name="AMRAP").put()
		rep = BaseMetric(name="One-Rep Max").put()

		user = auth.current_user_key()
		fourm = BaseActivity(user_key=user, category_key=running, metric_key=time, name="400m", tracked=True,
		                     description="Example description").put()
		BaseActivity(user_key=user, category_key=running, metric_key=time, name="1k", tracked=True).put()
		BaseActivity(user_key=user, category_key=running, metric_key=time, name="1mi").put()
		fivek = BaseActivity(user_key=user, category_key=running, metric_key=time, name="5k", tracked=True).put()
		BaseActivity(user_key=user, category_key=running, metric_key=time, name="10k").put()
		BaseActivity(user_key=user, category_key=running, metric_key=time, name="Half Marathon").put()
		BaseActivity(user_key=user, category_key=running, metric_key=time, name="Marathon").put()
		BaseActivity(user_key=user, category_key=running, metric_key=dist, name="Longest Run", tracked=True).put()

		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Deadlift", tracked=True).put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Squat", tracked=True).put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Bench Press").put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Shoulder Press").put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Push Jerk", tracked=True).put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Power Clean").put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Squat Clean").put()
		BaseActivity(user_key=user, category_key=lifting, metric_key=rep, name="Power Snatch").put()

		BaseActivity(user_key=user, category_key=crossfit, metric_key=time, name="Grace", description=grace).put()
		BaseActivity(user_key=user, category_key=crossfit, metric_key=time, name="Fran", description=fran,
		             tracked=True).put()
		BaseActivity(user_key=user, category_key=crossfit, metric_key=time, name="Helen", description=helen).put()
		BaseActivity(user_key=user, category_key=crossfit, metric_key=time, name="Filthy 50", description=filthy).put()
		BaseActivity(user_key=user, category_key=crossfit, metric_key=amrap, name="Fight Gone Bad",
		             description=fgb, tracked=True).put()
		BaseActivity(user_key=user, category_key=crossfit, metric_key=time, name="DT", description=dt,
		             tracked=True).put()

		BaseRecord(user_key=user, category_key=running, activity_key=fourm, value="2:04",
		           date=datetime.date.today()).put()
		BaseRecord(user_key=user, category_key=running, activity_key=fivek, value="23:53",
		           date=datetime.date.today()).put()
		BaseRecord(user_key=user, category_key=running, activity_key=fivek, value="25:04",
		           date=datetime.date.today()).put()
		return Response(status=204)


api.add_resource(InitActivities, '/init')
api.add_resource(Activities, '/activities/<string:category_key>')
api.add_resource(NewRecord, '/activity/record/new/<string:activity_key>')

grace = """
30 power clean and push jerks
"""

fran = """
21-15-9 reps of:<br>
95lbs/43kg Thrusters<br>
Pull-ups
"""

dt = """
Five rounds of:<br>
155lbs/70kg Deadlift, 12 reps<br>
155lbs/70kg  Hang power clean, 9 reps<br>
155lbs/70kg Push jerk, 6 reps
"""

helen = """
Three rounds of:<br>
Run 400 meters<br>
1.5pood/55lbs/25kg Kettlebell X 21 swings<br>
12 Pull-ups
"""

filthy = """
50 Box jump, 24"/61cm box<br>
50 Jumping pull-ups<br>
50 Kettlebell swings, 1 pood/36lbs/16kg<br>
Walking Lunges, 50 steps<br>
50 Knees to elbows<br>
50 Push press, 45lbs/21kg<br>
50 Back extensions<br>
50 Wall ball shots, 20lbs/9kg ball<br>
50 Burpees<br>
50 Double unders
"""

fgb = """
Three rounds of:<br>
Wall-ball, 20lbs/9kg ball, 10ft/3m target (Reps)<br>
Sumo deadlift high-pull, 75lbs/34kg (Reps)<br>
Box Jump, 20"/51cm box (Reps)<br>
Push-press, 75lbs/34kg (Reps)<br>
Row (Calories)<br>
<br>
In this workout you move from each of five stations after a minute.The clock does not reset or stop between exercises. This is a five-minute round from which a one-minute break is allowed before repeating. On call of "rotate", the athletes must move to next station immediately for best score. One point is given for each rep, except on the rower where each calorie is one point.
"""
