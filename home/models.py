from django.db import models
import hashlib
from django.utils import timezone


class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(null=True, max_length=150)
    phone = models.CharField(max_length=15, default='0000000000')
    organization = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(default='2000-01-01')
    password = models.CharField(max_length=100, default='defaultpassword')
    email_pass = models.CharField(max_length=50, null=True)
    email_host = models.CharField(max_length=50, default="smtp.gmail.com")
    email_port = models.IntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True, default=None)
    reset_token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.first_name


class recepients(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now=True)
    # TextField: no length limit — prevents DataError on long CSV comments
    comment = models.TextField(blank=True, default='')
    email_address = models.CharField(max_length=254, null=True, unique=False)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return self.name


class help(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# OTP Verification Model
# ─────────────────────────────────────────────────────────────────────────────
class OTPVerification(models.Model):
    """
    Stores a hashed OTP for email verification during registration.

    Security design:
      - OTP is NEVER stored as plain text; only its SHA-256 digest is persisted.
      - expires_at = created_at + 5 minutes (enforced in the view).
      - otp_count tracks how many OTPs were requested today (rate limiting).
      - Records are deleted after successful registration or can be cleaned up
        by a periodic management command.
    """
    email        = models.EmailField(max_length=254)
    otp_hash     = models.CharField(max_length=64)      # SHA-256 hex digest (64 chars)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()               # set to now + 5 min on save
    is_verified  = models.BooleanField(default=False)
    otp_count    = models.IntegerField(default=1)       # OTPs sent today for this email
    last_sent_at = models.DateTimeField(auto_now=True)  # updated on every resend

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'

    def __str__(self):
        return f"{self.email} – verified={self.is_verified}"

    # ── Helper: hash a raw OTP string ────────────────────────────────────────
    @staticmethod
    def hash_otp(otp: str) -> str:
        """Return the SHA-256 hex digest of a raw OTP string."""
        return hashlib.sha256(otp.encode('utf-8')).hexdigest()

    # ── Expiry check ─────────────────────────────────────────────────────────
    def is_expired(self) -> bool:
        """Returns True if the OTP window (5 min) has elapsed."""
        return timezone.now() > self.expires_at

    # ── Constant-time comparison ──────────────────────────────────────────────
    def verify(self, raw_otp: str) -> bool:
        """
        Validates a raw OTP against the stored hash.
        Returns True only when:
          1. The OTP has NOT expired.
          2. The SHA-256 hash of raw_otp matches otp_hash.
        """
        if self.is_expired():
            return False
        import hmac  # hmac.compare_digest prevents timing attacks
        return hmac.compare_digest(
            self.otp_hash,
            OTPVerification.hash_otp(raw_otp)
        )