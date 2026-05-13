from django.contrib import admin
from .models import User, recepients, help

admin.site.register(User)
admin.site.register(recepients)
admin.site.register(help)