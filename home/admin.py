from django.contrib import admin
from .models import User, recepients, help, OTPVerification


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """
    Admin panel for OTP records.
    Useful for debugging and monitoring OTP requests.
    OTP hash is shown (not the raw OTP — it is never stored).
    """
    list_display  = ('email', 'is_verified', 'created_at', 'expires_at', 'otp_count')
    list_filter   = ('is_verified',)
    search_fields = ('email',)
    readonly_fields = ('email', 'otp_hash', 'created_at', 'expires_at', 'otp_count', 'last_sent_at', 'is_verified')
    ordering      = ('-created_at',)

    def has_add_permission(self, request):
        # OTPs should only be created via the send_otp view, not manually
        return False


admin.site.register(User)
admin.site.register(recepients)
admin.site.register(help)