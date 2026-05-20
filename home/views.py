import uuid
import csv
import secrets
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.core import mail

from .utils import send_bulk_mail
from .models import User, recepients, help, OTPVerification
from template.models import emailtemplates


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: generate a secure 6-digit OTP
# ─────────────────────────────────────────────────────────────────────────────
def _generate_otp() -> str:
    """Return a cryptographically-secure 6-digit numeric OTP string."""
    return str(secrets.randbelow(900000) + 100000)   # 100000 – 999999


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: send OTP email
# ─────────────────────────────────────────────────────────────────────────────
def _send_otp_email(email: str, otp: str) -> None:
    """Send the OTP to the user's email address via Gmail SMTP."""
    subject = "🔐 Your Email Verification OTP – BulkMail Pro"
    body = (
        f"Hello,\n\n"
        f"Your One-Time Password (OTP) for registering on BulkMail Pro is:\n\n"
        f"    {otp}\n\n"
        f"This OTP is valid for {getattr(settings, 'OTP_EXPIRY_MINUTES', 5)} minutes.\n"
        f"Do NOT share it with anyone.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— BulkMail Pro Team"
    )
    mail.send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AJAX VIEW: Send OTP
# POST /send-otp/
# ─────────────────────────────────────────────────────────────────────────────
@require_POST
def send_otp(request):
    """
    AJAX endpoint.
    1. Validates the email field.
    2. Enforces rate limiting (max OTP_MAX_PER_HOUR sends per email per hour).
    3. Generates a secure 6-digit OTP.
    4. Stores its SHA-256 hash with a 5-minute expiry in OTPVerification.
    5. Emails the raw OTP to the user.
    Returns JSON { success, message }.
    """
    email = request.POST.get('email', '').strip().lower()

    # ── Validate email format ──────────────────────────────────────────────
    if not email:
        return JsonResponse({'success': False, 'message': 'Email address is required.'})

    # ── Check if email is already registered ──────────────────────────────
    if User.objects.filter(email=email).exists():
        return JsonResponse({
            'success': False,
            'message': 'This email is already registered. Please login instead.'
        })

    # ── Rate limiting: max OTP_MAX_PER_HOUR OTPs per email per hour ───────
    max_per_hour = getattr(settings, 'OTP_MAX_PER_HOUR', 5)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_count = OTPVerification.objects.filter(
        email=email,
        last_sent_at__gte=one_hour_ago
    ).count()

    if recent_count >= max_per_hour:
        return JsonResponse({
            'success': False,
            'message': f'Too many OTP requests. Please wait an hour before trying again.'
        })

    # ── Generate OTP & hash ────────────────────────────────────────────────
    raw_otp   = _generate_otp()
    otp_hash  = OTPVerification.hash_otp(raw_otp)
    expiry_min = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    expires_at = timezone.now() + timedelta(minutes=expiry_min)

    # ── Delete any previous unverified OTPs for this email ────────────────
    OTPVerification.objects.filter(email=email, is_verified=False).delete()

    # ── Persist the new hashed OTP ─────────────────────────────────────────
    OTPVerification.objects.create(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
    )

    # ── Send the email ─────────────────────────────────────────────────────
    try:
        _send_otp_email(email, raw_otp)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Could not send OTP email: {e}'
        })

    return JsonResponse({
        'success': True,
        'message': f'OTP sent successfully to {email}. Valid for {expiry_min} minutes.'
    })


# ─────────────────────────────────────────────────────────────────────────────
# AJAX VIEW: Verify OTP
# POST /verify-otp/
# ─────────────────────────────────────────────────────────────────────────────
@require_POST
def verify_otp(request):
    """
    AJAX endpoint.
    1. Fetches the latest unverified OTP record for the email.
    2. Calls record.verify(raw_otp) — constant-time SHA-256 comparison.
    3. On success: marks record as verified and writes email_verified flag to
       session so the register view can gate registration.
    Returns JSON { success, message }.
    """
    email   = request.POST.get('email', '').strip().lower()
    raw_otp = request.POST.get('otp', '').strip()

    if not email or not raw_otp:
        return JsonResponse({'success': False, 'message': 'Email and OTP are required.'})

    # Fetch the most-recent OTP record for this email
    try:
        record = OTPVerification.objects.filter(
            email=email,
            is_verified=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No OTP found for this email. Please click "Send OTP" first.'
        })

    # Check expiry
    if record.is_expired():
        return JsonResponse({
            'success': False,
            'message': 'OTP has expired. Please request a new one.'
        })

    # Verify OTP (constant-time comparison)
    if record.verify(raw_otp):
        record.is_verified = True
        record.save(update_fields=['is_verified'])

        # Store verified flag in session (used by register view)
        request.session['otp_verified_email'] = email

        return JsonResponse({
            'success': True,
            'message': '✅ Email Verified Successfully!'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': '❌ Invalid OTP. Please try again.'
        })


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER VIEW (updated with OTP gate)
# ─────────────────────────────────────────────────────────────────────────────
def register(request):
    """
    Registration view.
    - GET  → renders the registration form (Register.html).
    - POST → creates the user ONLY if OTP has been verified for the submitted email.
    """
    if request.method == "POST":
        first_name       = request.POST.get('first_name', '').strip()
        last_name        = request.POST.get('last_name', '').strip()
        email            = request.POST.get('email', '').strip().lower()
        phone            = request.POST.get('phone', '').strip()
        organization     = request.POST.get('organization', '').strip()
        date_of_birth    = request.POST.get('date', '').strip()
        email_host       = request.POST.get('passwords', '').strip()
        password         = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        username         = request.POST.get('username', '').strip()

        # ── Password match check ──────────────────────────────────────────
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('Register')

        # ── Duplicate email check ────────────────────────────────────────
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('Register')

        # ── OTP gate: email must be verified in this session ─────────────
        verified_email = request.session.get('otp_verified_email', '')
        if verified_email != email:
            messages.error(request, "Please verify your email first.")
            return redirect('Register')

        # ── Double-check the OTP record in DB ────────────────────────────
        otp_verified = OTPVerification.objects.filter(
            email=email,
            is_verified=True
        ).exists()
        if not otp_verified:
            messages.error(request, "Please verify your email first.")
            return redirect('Register')

        # ── Create user ───────────────────────────────────────────────────
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            organization=organization,
            date_of_birth=date_of_birth if date_of_birth else '2000-01-01',
            email_host=email_host if email_host else 'smtp.gmail.com',
            password=password,
        )

        # ── Create default email template for the new user ───────────────
        emailtemplates.objects.create(
            user=user,
            template_name="Default template",
            subject="BULK EMAIL SENDING SYSTEM",
            email_body="Default Email Template Given by 'BULK EMAIL SENDING SYSTEM'.",
            is_primary=True,
        )

        # ── Clean up OTP records & session flag ───────────────────────────
        OTPVerification.objects.filter(email=email).delete()
        try:
            del request.session['otp_verified_email']
        except KeyError:
            pass

        messages.success(request, "Account created successfully! Please login now.")
        return redirect('login')

    return render(request, 'act/Register.html')


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN VIEW
# ─────────────────────────────────────────────────────────────────────────────
def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

        if user.password == password:
            messages.success(request, "Login Successful!")
            request.session['user_id'] = user.id
            request.session.set_expiry(0)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

    return render(request, 'act/login.html')


# ─────────────────────────────────────────────────────────────────────────────
# DASH VIEW
# ─────────────────────────────────────────────────────────────────────────────
def dash(request):
    total_users = User.objects.count()
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass
    return render(request, 'act/dash.html', {'total_users': total_users, 'user': user})


# ─────────────────────────────────────────────────────────────────────────────
# HOME VIEW
# ─────────────────────────────────────────────────────────────────────────────
def home(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login first")
        return redirect('login')

    user      = User.objects.get(id=user_id)
    recepient = recepients.objects.filter(sender=user)

    # Profile completion logic
    total_fields = 5
    filled = sum([
        bool(user.first_name),
        bool(user.last_name),
        bool(user.email),
        bool(getattr(user, 'phone', '')),
        bool(getattr(user, 'organization', '')),
    ])
    profile_completion = int((filled / total_fields) * 100)

    context = {
        'user': user,
        'recepient': recepient,
        'profile_completion': profile_completion,
    }
    return render(request, 'act/home.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT VIEW
# ─────────────────────────────────────────────────────────────────────────────
def logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully!")
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE VIEW
# ─────────────────────────────────────────────────────────────────────────────
def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login to view your profile.")
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    total_fields = 5
    filled = sum([
        bool(user.first_name), bool(user.last_name), bool(user.email),
        bool(getattr(user, 'phone', '')), bool(getattr(user, 'organization', '')),
    ])
    profile_completion = int((filled / total_fields) * 100)

    return render(request, 'act/profile.html', {
        'user': user,
        'profile_completion': profile_completion,
    })


# ─────────────────────────────────────────────────────────────────────────────
# DELETE RECIPIENT VIEW
# ─────────────────────────────────────────────────────────────────────────────
def deleterecepient(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('login')

    user      = User.objects.get(id=user_id)
    recepient = recepients.objects.get(id=id)
    if recepient.sender == user:
        recepient.delete()
        messages.success(request, "Recipient deleted successfully!")
    else:
        messages.error(request, "You are not authorized to delete this recipient.")
    return redirect('home')


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTATION & ABOUT VIEWS
# ─────────────────────────────────────────────────────────────────────────────
def documentation(request):
    return render(request, 'act/documentation.html')


def about(request):
    return render(request, 'act/about.html')


# ─────────────────────────────────────────────────────────────────────────────
# ADD RECIPIENT VIEW
# ─────────────────────────────────────────────────────────────────────────────
def addrecepients(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('login')

    user = User.objects.get(id=user_id)
    if request.method == "POST":
        register_user = recepients(
            sender=user,
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            email_address=request.POST.get('email'),
            comment=request.POST.get('comments'),
        )
        register_user.save()
        return redirect('home')
    return render(request, 'act/recepients.html')


# ─────────────────────────────────────────────────────────────────────────────
# HELP VIEW
# ─────────────────────────────────────────────────────────────────────────────
def helps(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        help_entry = help(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
        )
        help_entry.save()
        messages.success(request, "Your message has been sent successfully!")
        return redirect('home')
    return render(request, 'act/help.html')


# ─────────────────────────────────────────────────────────────────────────────
# VIEW / EDIT RECIPIENT VIEWS
# ─────────────────────────────────────────────────────────────────────────────
def view(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('login')
    user = User.objects.get(id=user_id)
    rec  = recepients.objects.get(id=id)
    if rec.sender != user:
        messages.error(request, "You are not authorized to view this recipient.")
        return redirect('home')
    return render(request, 'act/view.html', {'rec': rec})


def edit(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')

    user  = User.objects.get(id=user_id)
    recep = recepients.objects.get(id=id)

    if recep.sender != user:
        messages.error(request, "You are not authorized to edit this recipient.")
        return redirect('home')

    if request.method == 'POST':
        recep.name          = request.POST.get('name')
        recep.email_address = request.POST.get('email')
        recep.category      = request.POST.get('category')
        recep.comment       = request.POST.get('comments')
        recep.save()
        messages.success(request, "Recipient updated successfully.")
        return redirect('home')
    return render(request, 'act/edit.html', {'recep': recep})


# ─────────────────────────────────────────────────────────────────────────────
# SEND BULK MAIL VIEW
# ─────────────────────────────────────────────────────────────────────────────
def send_mail(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        if not selected_ids:
            messages.error(request, "No recipients selected!")
            return redirect('home')
        success = send_bulk_mail(user_id, selected_ids)
        if success:
            messages.success(request, "Emails sent successfully!")
        else:
            messages.error(request, "Failed to send emails. Please check your email settings.")
        return redirect('home')
    return redirect('home')


# ─────────────────────────────────────────────────────────────────────────────
# BULK DELETE RECIPIENTS VIEW
# ─────────────────────────────────────────────────────────────────────────────
def delete_selected_recepients(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')

    if request.method == 'POST':
        user         = User.objects.get(id=user_id)
        selected_ids = request.POST.getlist('selected_ids')

        if not selected_ids:
            messages.error(request, "No recipients selected for deletion.")
            return redirect('home')

        deleted_count, _ = recepients.objects.filter(
            id__in=selected_ids,
            sender=user
        ).delete()

        if deleted_count:
            messages.success(request, f"{deleted_count} recipient(s) deleted successfully.")
        else:
            messages.error(request, "No matching recipients found to delete.")

    return redirect('home')


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE PASSWORD VIEW
# ─────────────────────────────────────────────────────────────────────────────
def change_password(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        current_password  = request.POST.get('current_password')
        new_password      = request.POST.get('new_password')
        confirm_password  = request.POST.get('confirm_password')
        if current_password != user.password:
            messages.error(request, 'Current password is incorrect')
            return redirect('change_password')
        if new_password != confirm_password:
            messages.error(request, 'New password and confirm password do not match')
            return redirect('change_password')
        user.password = new_password
        user.save()
        messages.success(request, 'Password changed successfully')
        return redirect('profile')
    return render(request, 'act/change_password.html')


# ─────────────────────────────────────────────────────────────────────────────
# EDIT PROFILE VIEW
# ─────────────────────────────────────────────────────────────────────────────
def edit_profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        user.first_name   = request.POST.get('first_name')
        user.last_name    = request.POST.get('last_name')
        user.email        = request.POST.get('email')
        user.phone        = request.POST.get('phone')
        user.organization = request.POST.get('organization')
        user.email_pass   = request.POST.get('email_pass')
        profile_image     = request.FILES.get('profile_image')
        if profile_image:
            user.profile_image = profile_image
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'act/edit_profile.html', {'user': user})


# ─────────────────────────────────────────────────────────────────────────────
# FORGOT PASSWORD VIEW
# ─────────────────────────────────────────────────────────────────────────────
def forgot_password(request):
    if request.method == "POST":
        entered_email = request.POST.get('email')
        if not entered_email:
            messages.error(request, "Please enter your email address.")
            return redirect('forgot_password')

        try:
            user = User.objects.get(email=entered_email)
            token = str(uuid.uuid4())
            user.reset_token = token
            user.save()

            reset_link = request.build_absolute_uri(f'/reset/{token}/')
            try:
                mail.send_mail(
                    'Password Reset Request – Bulk Email Sender',
                    f'Hi {user.first_name},\n\nClick the link below to reset your password:\n\n{reset_link}\n\nThis link is valid for one-time use only.\n\nIf you did not request this, ignore this email.',
                    settings.DEFAULT_FROM_EMAIL,
                    [entered_email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Could not send reset email: {e}")
                return redirect('forgot_password')

            messages.success(request, "✅ Reset link has been sent to your email!")
            return redirect('forgot_password')

        except User.DoesNotExist:
            messages.error(request, "❌ No account found with that email address.")
            return redirect('forgot_password')

    return render(request, 'act/forgot_password.html')


# ─────────────────────────────────────────────────────────────────────────────
# RESET PASSWORD VIEW
# ─────────────────────────────────────────────────────────────────────────────
def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired reset link. Please request a new one.")
        return redirect('forgot_password')

    if request.method == "POST":
        password         = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'act/reset_password.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'act/reset_password.html')

        user.password    = password
        user.reset_token = ''   # invalidate the token after use
        user.save()
        messages.success(request, "✅ Password reset successfully! You can now login.")
        return redirect('login')

    return render(request, 'act/reset_password.html')


# ─────────────────────────────────────────────────────────────────────────────
# CSV UPLOAD VIEW
# ─────────────────────────────────────────────────────────────────────────────
def uploadfile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login first")
        return redirect('login')

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, "Please select a CSV file")
            return redirect('uploadfile')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Only CSV files are allowed (.csv)")
            return redirect('uploadfile')

        try:
            data   = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(data)
            header = next(reader)

            required_header = ['Name', 'Email', 'Category', 'Comments']
            if header != required_header:
                messages.error(
                    request,
                    f"Invalid CSV format. First row must be exactly: {', '.join(required_header)}"
                )
                return redirect('uploadfile')

            imported_count = 0
            skipped_count  = 0

            for row in reader:
                if len(row) < 4:
                    continue

                name     = row[0].strip()
                email    = row[1].strip()
                category = row[2].strip()
                comment  = row[3].strip()

                if not email:
                    skipped_count += 1
                    continue

                obj, created = recepients.objects.get_or_create(
                    sender=user,
                    email_address=email,
                    defaults={'name': name, 'category': category, 'comment': comment},
                )

                if created:
                    imported_count += 1
                else:
                    skipped_count += 1

            parts = [f"{imported_count} recipient(s) imported successfully!"]
            if skipped_count:
                parts.append(f"{skipped_count} row(s) skipped (duplicate or blank email).")
            messages.success(request, " ".join(parts))
            return redirect('home')

        except Exception as e:
            messages.error(request, f"Import failed: {e}")
            return redirect('uploadfile')

    return render(request, 'act/uploadfile.html')