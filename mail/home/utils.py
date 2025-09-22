from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings
from .models import User, recepients
from template.models import emailtemplates

def get_filtered_recepients(user_id,selected_ids):
    Recepients=recepients.objects.filter(sender__id=user_id,id__in=selected_ids)
    return [r.email_address for r in Recepients]



def send_bulk_mail(user_id,selected_ids):
    account=User.objects.get(id=user_id)
    try:
        connection = get_connection(
            host = account.email_host,
            port=account.email_port,
            username=account.email,
            password=account.email_pass,
            use_tls=account.use_tls,
        )
        template = emailtemplates.objects.get(user=account,is_primary=True)
        email = EmailMessage(
            subject=template.subject,
            body=template.email_body,
            from_email=account.email,
            to=get_filtered_recepients(user_id,selected_ids),
            connection=connection
        )
        email.send()
    except Exception as e:
        print('\n\n-------------------')
        print("Error:",e)
        print("----------------\n\n")
        return False
    return True