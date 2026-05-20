from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path('login/',    views.login,    name='login'),
    path('Register/', views.register, name='Register'),
    path('logout/',   views.logout,   name='logout'),

    # ── OTP Endpoints (AJAX, POST only) ───────────────────────────────────
    path('send-otp/',   views.send_otp,   name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # ── Core Pages ────────────────────────────────────────────────────────
    path('',      views.dash, name='dash'),
    path('home/', views.home, name='home'),

    # ── Recipients ────────────────────────────────────────────────────────
    path('addrecepients/',         views.addrecepients,          name='addrecepients'),
    path('delete/<int:id>/',       views.deleterecepient,        name='deleterecepient'),
    path('delete-selected/',       views.delete_selected_recepients, name='delete_selected'),
    path('view/<int:id>/',         views.view,                   name='view'),
    path('edit/<int:id>/',         views.edit,                   name='edit'),
    path('uploadfile/',            views.uploadfile,             name='uploadfile'),

    # ── Bulk Mail ─────────────────────────────────────────────────────────
    path('send/', views.send_mail, name='send_bulk_mail'),

    # ── Profile ───────────────────────────────────────────────────────────
    path('profile/',      views.profile,       name='profile'),
    path('edit_profile/', views.edit_profile,  name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),

    # ── Password Reset ────────────────────────────────────────────────────
    path('forgot_password/',         views.forgot_password, name='forgot_password'),
    path('reset/<str:token>/',       views.reset_password,  name='reset_password'),

    # ── Info Pages ────────────────────────────────────────────────────────
    path('documentation/', views.documentation, name='documentation'),
    path('about/',         views.about,         name='about'),
    path('help/',          views.helps,          name='help'),

    # ── Third-party App URLs ──────────────────────────────────────────────
    path('templates/', include('template.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)