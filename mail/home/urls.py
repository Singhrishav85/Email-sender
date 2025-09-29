# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.http import HttpResponse
# from django.template.loader import render_to_string
from . import views
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static


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
    path('change_password/', views.change_password, name='change_password'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset/<str:token>/', views.reset_password, name='reset_password')


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)