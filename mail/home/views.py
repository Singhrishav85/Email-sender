from django.shortcuts import render, redirect, get_object_or_404
from .utils import send_bulk_mail
from django.contrib import messages
from .models import User, recepients , help
from template.models import emailtemplates


# Create your views here.
# def send_email(request):
    # send_email_to_client()
    # return redirect('/')

# def home(request):
    # return render(request, 'act/index.html')

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
            # print(e)
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
    return render(request, 'act/dash.html',{'total_users': total_users})

def home(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,"login first")
        return redirect('login')

    user=User.objects.get(id=user_id)
    recepient=recepients.objects.filter(sender=user)
        
    return render(request,'act/home.html',{'user':user,'recepient':recepient})

def logout(request):
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

    return render(request, 'act/profile.html', {'user': user})

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