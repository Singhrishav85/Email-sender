from django.contrib import admin
from .models import User    , recepients , help
# Register your models here.

admin.site.register(User)
admin.site.register(recepients)
admin.site.register(help)

