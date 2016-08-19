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


class KeyField(wtforms.HiddenField):
	def populate_obj(self, obj, name):
		setattr(obj, name, Key(urlsafe=self.data))


class DistanceField(wtforms.StringField):
	pass


class RecordForm(Form):
	activity_key = KeyField('Activity', [wtforms.validators.required()])
	category_key = KeyField('Category', [wtforms.validators.required()])
	value = wtforms.StringField('Value', [wtforms.validators.required()])
	date = wtforms.DateField('Date', [wtforms.validators.optional()])
	notes = wtforms.TextAreaField('Notes', [wtforms.validators.optional()])

	def __init__(self, *args, **kwargs):
		super(RecordForm, self).__init__(*args, **kwargs)
		cats, _ = BaseCategory.get_dbs()

	def new(self, activity):
		self.activity_key.data = activity.key.urlsafe()
		self.category_key.data = activity.category_key.urlsafe()
		return self

	def edit(self, record):
		self.activity_key.data = record.activity.urlsafe()
		self.category_key.data = record.category.urlsafe()
		self.value.data = record.value
		self.date.data = record.date
		self.notes.data = record.notes
		return self


class TimeRecordForm(RecordForm):
	value = wtforms_components.TimeField('Time', [wtforms.validators.required()])


class DistanceRecordForm(RecordForm):
	value = DistanceField('Distance', [wtforms.validators.required()])


class Activities(Resource):
	@auth.login_required
	def get(self, category_key):
		user_key = auth.current_user_key()
		cat = Key(urlsafe=category_key).get()
		activities = BaseActivity.get_dbs(user_key=user_key, tracked=True, category_key=cat.key)[0]
		records = [BaseRecord.get_dbs(order='-created', user_key=user_key, activity_key=a.key)[0] for a in activities]
		return base_auth_response('records/records.html', category_key=category_key,
		                          activities=zip(activities, records))


class NewRecord(Resource):
	@auth.login_required
	def get(self, activity_key):
		a = Key(urlsafe=activity_key).get()
		if a.metric_key.get().name == 'Time':
			form = TimeRecordForm
		elif a.metric_key.get().name == 'Distance':
			form = DistanceRecordForm
		else:
			form = RecordForm

		return base_auth_response('records/new_record.html', form=form().new(a), activity=a)

	@auth.login_required
	def post(self, activity_key):
		activity = Key(urlsafe=activity_key).get()
		form = RecordForm()
		if form.validate_on_submit():
			entity = BaseRecord()
			form.populate_obj(entity)
			entity.user_key = auth.current_user_key()
			if entity.is_valid_entry(form):
				entity.put()
				flash('Toevoegen succesvol.', category='success')
				return redirect(api.url_for(Activities, category_key=activity.category_key.urlsafe()))
		flash('Toevoegen niet gelukt.', category='warning')
		return base_auth_response('records/new_record.html', form=form)

api.add_resource(Activities, '/activities/<string:category_key>')
api.add_resource(NewRecord, '/activity/record/new/<string:activity_key>')

