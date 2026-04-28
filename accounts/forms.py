from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_('A user with that email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        try:
            username = self.cleaned_data.get('username')
            if username and '@' in username:
                user = User.objects.filter(email__iexact=username.strip()).first()
                if user:
                    self.cleaned_data['username'] = user.username
            return super().clean()
        except ValidationError as error:
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = User.objects.filter(username=username, is_active=False).first()
            if not user and username:
                user = User.objects.filter(email__iexact=username, is_active=False).first()
            if user and user.check_password(password):
                raise ValidationError(
                    _('Please verify your email address before logging in.'),
                    code='inactive',
                ) from error
            raise

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                _('Please verify your email address before logging in.'),
                code='inactive',
            )
        super().confirm_login_allowed(user)
