from django.db import models

# Create your models here.
from django.db import models


class Assistant(models.Model):
    assistant_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()


class InteractionLog(models.Model):
    username = models.CharField(max_length=150)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)