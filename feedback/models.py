from django.db import models
from passenger.models import User

class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    stars = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    