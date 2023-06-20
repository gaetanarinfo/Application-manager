from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.models import UsersCards
from django.contrib.auth.models import Salarys
from django.contrib.auth.models import usersStatements
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

class UpdateUserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True, max_length=150)
    username = forms.CharField(max_length=150, required=True)
    bio = forms.CharField(max_length=255)
    banner = forms.CharField(max_length=255)
    facebook = forms.CharField(max_length=255)
    twitter = forms.CharField(max_length=255)
    linkedin = forms.CharField(max_length=255)
    github = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "bio", "facebook", "twitter", "linkedin", "github", "banner"]


class CreateCardForm(forms.ModelForm):
    user_id = forms.CharField(max_length=255, required=True)
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    card_number = forms.CharField(max_length=255, required=True)
    exp_date = forms.CharField(max_length=100, required=True)
    cvv = forms.IntegerField(required=True)
    type = forms.CharField(max_length=255, required=True)
    card_name = forms.CharField(max_length=255, required=True)
    active = forms.IntegerField(required=True)
    
    class Meta:
        model = UsersCards
        fields = ["user_id", "first_name", "last_name", "card_number", "exp_date", "cvv", "type", "card_name", "active"]

class UpdateCardForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    card_number = forms.CharField(max_length=255, required=True)
    exp_date = forms.CharField(max_length=100, required=True)
    cvv = forms.IntegerField(required=True)
    type = forms.CharField(max_length=255, required=True)
    card_name = forms.CharField(max_length=255, required=True)
    
    class Meta:
        model = UsersCards
        fields = ["first_name", "last_name", "card_number", "exp_date", "cvv", "type", "card_name"]

class CreateDocForm(forms.ModelForm):
    user_id = forms.CharField(max_length=255, required=True)
    releves = forms.CharField(max_length=255, required=True)
    date = forms.CharField(max_length=255, required=True)
    compte = forms.CharField(max_length=255, required=True)
    total = forms.DecimalField()
    doc = forms.FileField()
    
    class Meta:
        model = usersStatements
        fields = ["user_id", "releves", "date", "total", "compte", "doc"]
        
class CreateDocSalarysForm(forms.ModelForm):
    user_id = forms.IntegerField(required=True)
    entreprise = forms.CharField(max_length=255, required=True)
    date = forms.CharField(max_length=255, required=True)
    net = forms.IntegerField(required=True)
    brut = forms.IntegerField(required=True)
    hours = forms.CharField(max_length=255, required=True)
    total_hours = forms.CharField(max_length=255, required=True)
    file = forms.FileField()
    
    class Meta:
        model = Salarys
        fields = ["user_id", "entreprise", "file", "net", "brut", "hours", "total_hours", "date"]        