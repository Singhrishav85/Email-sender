# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.http import HttpResponse
# from django.template.loader import render_to_string
from . import views
from django.urls import path,include


urlpatterns = [
    path('Email/',views.home, name='home'),
    path('send/', views.send_mail, name='send_bulk_mail'),
    path('login/', views.login, name='login'),
    path('Register/',views.register,name='Register'),
    path('',views.dash , name="dash"),
    path('home/',views.home , name="home"),
    path('addrecepients/',views.addrecepients , name="addrecepients"),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('delete/<int:id>/', views.deleterecepient, name='deleterecepient'),
    path('documentation/', views.documentation, name='documentation'),
    path('about/', views.about, name='about'),
    path('help/', views.helps, name='help'),
    path('view/<int:id>/', views.view, name='view'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('templates/',include('template.urls')),
]