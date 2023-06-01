from django import forms

from django.contrib.auth.models import User


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
