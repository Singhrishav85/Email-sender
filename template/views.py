from django.shortcuts import render,redirect
from home.models import User
from .models import emailtemplates
from django.contrib import messages

# Create your views here.
def configure(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    username=user.first_name
    user=User.objects.get(id=user_id)
    primary_template = emailtemplates.objects.get(user = user, is_primary=True)
    other_template = emailtemplates.objects.filter(user = user, is_primary=False)


    primary = {
        'id':primary_template.id,
        'template_name':primary_template.template_name,
        'subject':primary_template.subject,
        'created_at':primary_template.created_at,
        'updated_at':primary_template.updated_at,
    }
    ot_list = []
    for ot in other_template:
        ot_list.append({
            'id':ot.id,
            'template_name':ot.template_name,
            'subject':ot.subject,
            'created_at':ot.created_at,
            'updated_at':ot.updated_at,
        })
    templates = {
        
    }

    return render(request,'t/configure.html', {
            'username':username,
            'primary':primary,
            'others':ot_list
        })

def createtemplate(request):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    if request.method=="POST":
        name=request.POST.get('name')
        subject=request.POST.get('subject')
        body=request.POST.get('body')
        # primary=request.POST.get('primary')
        is_primary = True if request.POST.get('primary') == 'on' else False

        createuser=emailtemplates(
            template_name=name,
            subject=subject,
            email_body=body,
            is_primary=is_primary
        )
        createuser.save()
        messages.success(request,'Create templates successfully!' )
        return redirect('configure')
    return render(request,'t/createtemplate.html')

def viewstatus(request,id):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    emailtemp=emailtemplates.objects.get(id=id)
    return render(request,'t/viewtemp.html',{'emailtemp':emailtemp})




def editTemplate(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login first')
        return redirect('login')
    user = User.objects.get(id=user_id)
    emailtemplate = emailtemplates.objects.get(id=id)
    if request.method == "POST":
        emailtemplate.template_name = request.POST.get('template_name')
        emailtemplate.subject = request.POST.get('subject')
        emailtemplate.email_body = request.POST.get('body')

        status = request.POST.get('status')
        if status == 'Primary':
            user_templates=emailtemplates.objects.filter(user=user)
            emailtemplate.is_primary = True
            for u in user_templates:
                if u.id != id:
                    u.is_primary = False
                u.save()
        emailtemplate.save()
        messages.success(request, 'Updated Successfully!')
        return redirect('configure')
    return render(request, 't/editprofile.html', {'emailtemplate': emailtemplate})

def deletetemplate(request,id):
    user_id=request.session.get('user_id')
    if not user_id:
        messages.warning(request,'Login first')
        return redirect('login')
    user=User.objects.get(id=user_id)
    delete_template=emailtemplates.objects.get(id=id)
    delete_template.delete()
    messages.success(request,'Template deleted successfully!')
    return redirect('configure') 