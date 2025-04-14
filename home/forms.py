from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile
from django.core.validators import RegexValidator

class CustomUserCreationForm(UserCreationForm):
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be 10 digits."
    )
    
    username = forms.CharField(
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message="Username can only contain letters, numbers, and underscores."
            )
        ],
        error_messages={
            'required': 'Username is required.',
            'min_length': 'Username must be at least 3 characters long.',
        }
    )
    
    email = forms.EmailField(
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    phone_number = forms.CharField(
        validators=[phone_regex],
        error_messages={
            'required': 'Phone number is required.',
        }
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={
            'required': 'Password is required.',
            'min_length': 'Password must be at least 8 characters long.',
        }
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Password confirmation is required.',
        }
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_pic', 'phone', 'address']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number']