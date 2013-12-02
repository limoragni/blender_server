from django.db import models
from django.contrib.auth.models import User

class Render(models.Model):
	code = models.CharField(max_length=200)
	#user = models.ForeignKey(User)
	media_url = models.CharField(max_length=200)
	media_data = models.CharField(max_length=2000)
	date = models.DateField(auto_now=True)
