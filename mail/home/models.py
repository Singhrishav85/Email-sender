from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(null=True, max_length=150)
    phone = models.CharField(max_length=15, default='0000000000')
    organization = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(default='2000-01-01')  # lowercase field name
    password = models.CharField(max_length=100, default='defaultpassword')
    email_pass=models.CharField(max_length=50,null=True)
    email_host=models.CharField(max_length=50,default="smtp.gmail.com")
    email_port=models.IntegerField(default=587)
    use_tls=models.BooleanField(default=True)


    def __str__(self):
        return self.first_name
    

class recepients(models.Model):
    sender=models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    name=models.CharField(max_length=100)
    category=models.CharField(max_length=100)
    date_added=models.DateTimeField(auto_now=True)
    comment=models.CharField(max_length=100)
    email_address=models.CharField(max_length=100,null=True,unique=False)

    def __str__(self):
        return self.name
    

class help(models.Model):
    name=models.CharField(max_length=100)
    email=models.EmailField(max_length=100)
    subject=models.CharField(max_length=200)
    message=models.TextField()

    def __str__(self):
        return self.name