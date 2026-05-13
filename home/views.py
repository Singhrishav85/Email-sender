import uuid
import csv
from django.shortcuts import render, redirect, get_object_or_404
from .utils import send_bulk_mail
from django.contrib import messages
from .models import User, recepients, help
from template.models import emailtemplates
from django.core import mail
from django.conf import settings

def login(request):
    # if 'user_id' in request.session:
    #     del request.session['user_id']
    #     messages.info(request,"Previous message has been cleared")
    
    if request.method  == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=username)
        except Exception as e:
            messages.error(request, "Invalid creadential")
            return redirect('login')
        if user.password == password:
            messages.success(request,"Login Successfully! !")
            request.session['user_id']=user.id
            request.session.set_expiry(0)
            return redirect('home')
        else:
            messages.error(request, "Invalid creadential")
            return redirect('login')
    return render(request, 'act/login.html')

def register(request):
    if request.method=="POST":
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        email=request.POST['email']
        phone=request.POST['phone']
        organization=request.POST['organization']
        date_of_birth=request.POST['date']#//date jo hai wo form me name diya hua h
        email_host=request.POST['passwords']
        password=request.POST['password']   
        confirm_password=request.POST['confirm_password']

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            organization=organization,
            date_of_birth=date_of_birth,
            email_host=email_host,
            password=password
        )

        emailtemplates.objects.create(
            user = user,
            template_name = "Default template",
            subject = "BULK EMAIL SENDING SYSTEM",
            email_body = "Default Email Template Given by 'BULK EMAIL SENDING SYSTEM'.",
            is_primary = True
        )

        messages.success(request,"Account created successfully!, Please login now")
        return redirect('login')
    return render(request,'act/Register.html')

def dash(request):
    total_users = User.objects.count() 
    return render(request, 'act/dash.html',{'total_users': total_users} )

def home(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Please login first")
        return redirect('login')

    user = User.objects.get(id=user_id)
    recepient = recepients.objects.filter(sender=user)

    # 🧮 Profile Completion Logic
    total_fields = 5  # jitne fields count karne hain (adjust according to your User model)
    filled = 0

    if user.first_name:
        filled += 1
    if user.last_name:
        filled += 1
    if user.email:
        filled += 1
    if hasattr(user, 'phone') and user.phone:
        filled += 1
    if hasattr(user, 'organization') and user.organization:
        filled += 1

    profile_completion = int((filled / total_fields) * 100)

    context = {
        'user': user,
        'recepient': recepient,
        'profile_completion': profile_completion
    }

    return render(request, 'act/home.html', context)


def logout(request):
    request.session.flush() 
    messages.success(request,"Logout successfully!")
    return redirect('login')

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
    
    # 🟢 Profile Completion Logic
    total_fields = 5  # jitne fields count karne hain (adjust according to your User model)
    filled = 0

    if user.first_name:
        filled += 1
    if user.last_name:
        filled += 1
    if user.email:
        filled += 1
    if hasattr(user, 'phone') and user.phone:
        filled += 1
    if hasattr(user, 'organization') and user.organization:
        filled += 1

    profile_completion = int((filled / total_fields) * 100)

    # 🟢 Pass profile_completion to template
    return render(request, 'act/profile.html', {'user': user,'profile_completion': profile_completion})


def deleterecepient(request, id):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,"login first")
        return redirect('login')

    user=User.objects.get(id=user_id)
    recepient=recepients.objects.get(id=id)
    if recepient.sender==user:
        recepient.delete()
        messages.success(request,"Recepient deleted successfully!")
    else:
        messages.error(request,"You are not authorized to delete this recepient.")
    return redirect('home')

def documentation(request):
    return render(request, 'act/documentation.html')

def about(request):
    return render(request, 'act/about.html')

def addrecepients(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,"login first")
        return redirect('login')

    user=User.objects.get(id=user_id)
    if request.method=="POST":
        name=request.POST.get('name')
        category=request.POST.get('category')
        email=request.POST.get('email')
        comments=request.POST.get('comments')

        register_user=recepients(
            sender=user,
            name=name,
            category=category,
            email_address=email,
            comment=comments,
        )
        register_user.save()
        return redirect('home')
    return render(request,'act/recepients.html')

def helps(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,"login first")
        return redirect('login')
    user=User.objects.get(id=user_id)
    if request.method=="POST":
        name=request.POST.get('name')
        email=request.POST.get('email')
        subject=request.POST.get('subject')
        message=request.POST.get('message')

        help_entry=help(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )
        help_entry.save()
        messages.success(request,"Your message has been sent successfully!")
        return redirect('home')
    return render(request, 'act/help.html')

def view(request,id):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,"login first")
        return redirect('login')
    user=User.objects.get(id=user_id)
    rec=recepients.objects.get(id=id)
    if rec.sender!=user:
        messages.error(request,"You are not authorized to view this recepient.")
        return redirect('home')
    return render(request, 'act/view.html', {'rec': rec})

def edit(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')

    user = User.objects.get(id=user_id) 
    recep = recepients.objects.get(id=id) 

    if recep.sender != user:
        messages.error(request, "You are not authorized to edit this recipient.")
        return redirect('home')

    if request.method == 'POST':  
        recep.name = request.POST.get('name')
        recep.email_address = request.POST.get('email')
        recep.category = request.POST.get('category')
        recep.comment = request.POST.get('comments')
        recep.save() 
        messages.success(request, "Recipient updated successfully.")
        return redirect('home')
    return render(request, 'act/edit.html', {'recep': recep})

def send_mail(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')
    if request.method == 'POST':
        selected_ids=request.POST.getlist('selected_ids')
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


def delete_selected_recepients(request):
    """Bulk-delete recipients that belong to the logged-in user."""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')

    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        selected_ids = request.POST.getlist('selected_ids')

        if not selected_ids:
            messages.error(request, "No recipients selected for deletion.")
            return redirect('home')

        # Only delete recipients that belong to this user (security guard)
        deleted_count, _ = recepients.objects.filter(
            id__in=selected_ids,
            sender=user
        ).delete()

        if deleted_count:
            messages.success(request, f"{deleted_count} recipient(s) deleted successfully.")
        else:
            messages.error(request, "No matching recipients found to delete.")

    return redirect('home')

def change_password(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    if user_id:
        if request.method=="POST":
            current_password=request.POST.get('current_password')
            new_password=request.POST.get('new_password')
            confirm_poassword=request.POST.get('confirm_password')
            if current_password !=user.password:
                messages.error(request,'current password is incorrect')
                return redirect('change_password')

            if new_password != confirm_poassword:
                messages.error(request,'new password and confirm password does not match')
                return redirect('change_password')
            user.password=new_password
            user.save()
            messages.success(request,'password changed successfully')
            return redirect('profile')
    return render(request, 'act/change_password.html')

def edit_profile(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    if request.method=="POST":
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        organisation=request.POST.get('organization')
        # date_of_birth=request.POST.get('date_of_birth')
        email_pass=request.POST.get('email_pass')
        profile_image=request.FILES.get('profile_image')

        user.first_name=first_name
        user.last_name=last_name
        user.email=email
        user.phone=phone
        user.organization=organisation
        # user.date_of_birth=date_of_birth
        user.email_pass=email_pass
        if profile_image:
            user.profile_image=profile_image
        user.save()
        messages.success(request,'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'act/edit_profile.html',{'user':user})

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

            # Build absolute reset URL (works for both dev and prod)
            reset_link = request.build_absolute_uri(f'/reset/{token}/')

            from_email = settings.DEFAULT_FROM_EMAIL

            try:
                mail.send_mail(
                    'Password Reset Request – Bulk Email Sender',
                    f'Hi {user.first_name},\n\nClick the link below to reset your password:\n\n{reset_link}\n\nThis link is valid for one-time use only.\n\nIf you did not request this, ignore this email.',
                    from_email,
                    [entered_email],
                    fail_silently=False,
                )
            except Exception as e:
                print("Error sending reset email:", e)
                messages.error(request, f"Could not send reset email: {e}")
                return redirect('forgot_password')

            messages.success(request, "✅ Reset link has been sent to your email!")
            return redirect('forgot_password')

        except User.DoesNotExist:
            messages.error(request, "❌ No account found with that email address.")
            return redirect('forgot_password')

    return render(request, 'act/forgot_password.html')

def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired reset link. Please request a new one.")
        return redirect('forgot_password')

    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'act/reset_password.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'act/reset_password.html')

        # Plain User model — store password directly (no AbstractUser.set_password)
        user.password = password
        user.reset_token = ''   # invalidate the token after use
        user.save()

        messages.success(request, "✅ Password reset successfully! You can now login.")
        return redirect('login')

    return render(request, 'act/reset_password.html')


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
            data = csv_file.read().decode('utf-8').splitlines()
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
            skipped_count = 0

            for row in reader:
                # Skip short / blank rows
                if len(row) < 4:
                    continue

                name     = row[0].strip()
                email    = row[1].strip()
                category = row[2].strip()
                comment  = row[3].strip()

                if not email:          # skip rows with no email
                    skipped_count += 1
                    continue

                # get_or_create prevents duplicate (sender + email) pairs
                obj, created = recepients.objects.get_or_create(
                    sender=user,
                    email_address=email,
                    defaults={
                        'name': name,
                        'category': category,
                        'comment': comment,
                    }
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