from django.db import models
from django.contrib.auth.models import User

class Render_state(models.Model):
	state = models.CharField(max_length=50)
	code  = models.IntegerField(max_length=1)

class Render(models.Model):
	code = models.CharField(max_length=200)
	render_type = models.CharField(max_length=200)
	media_url = models.CharField(max_length=200)
	media_data = models.CharField(max_length=2000)
	date = models.DateField(auto_now=True)
	task_id = models.CharField(max_length=200)
	render_state = models.ForeignKey(Render_state)
