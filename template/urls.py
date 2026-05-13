from . import views
from django.urls import path


urlpatterns = [
    path('', views.configure, name='configure'),
    path('createtemplate/',views.createtemplate, name='createtemplate'),
    path('viewstatus/<int:id>/', views.viewstatus , name='viewstatus'),
    path('editprofile/<int:id>/',views.editTemplate, name='editprofile'),
    path('deletetemplate/<int:id>/',views.deletetemplate , name='deletetemplate')
]