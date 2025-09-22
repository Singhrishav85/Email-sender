from django.db import models
from home.models import User
# Create your models here.

class emailtemplates(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    template_name=models.CharField(max_length=50)
    subject=models.CharField(max_length=100)
    email_body=models.TextField()
    is_primary=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateField(auto_now=True)

    def __str__(self):
        return self.template_name