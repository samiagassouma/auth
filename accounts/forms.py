# from django import forms
# from django.contrib.auth import authenticate
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _

# from .validators import (
#     EMAIL_MAX_LENGTH,
#     EMAIL_RULE_MESSAGE,
#     FULL_NAME_MAX_LENGTH,
#     FULL_NAME_MIN_LENGTH,
#     FULL_NAME_RULE_MESSAGE,
#     PASSWORD_PATTERN,
#     PASSWORD_RULE_MESSAGE,
#     validate_signup_email,
#     validate_signup_full_name,
#     validate_signup_password,
# )
# from .user_utils import build_unique_username


# class SignupForm(UserCreationForm):
#     full_name = forms.CharField(
#         label=_('Full name'),
#         min_length=FULL_NAME_MIN_LENGTH,
#         max_length=FULL_NAME_MAX_LENGTH,
#         error_messages={
#             'min_length': FULL_NAME_RULE_MESSAGE,
#             'max_length': FULL_NAME_RULE_MESSAGE,
#         },
#         required=True,
#     )
#     email = forms.EmailField(required=True, max_length=EMAIL_MAX_LENGTH)

#     class Meta(UserCreationForm.Meta):
#         model = User
#         fields = ('full_name', 'email', 'password1', 'password2')

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['full_name'].widget.attrs.update({
#             'autocomplete': 'name',
#             'minlength': str(FULL_NAME_MIN_LENGTH),
#             'maxlength': str(FULL_NAME_MAX_LENGTH),
#             'required': True,
#             'title': FULL_NAME_RULE_MESSAGE,
#         })
#         self.fields['email'].widget.attrs.update({
#             'autocomplete': 'email',
#             'maxlength': str(EMAIL_MAX_LENGTH),
#             'required': True,
#             'title': EMAIL_RULE_MESSAGE,
#         })
#         self.fields['password1'].help_text = PASSWORD_RULE_MESSAGE
#         for field_name in ('password1', 'password2'):
#             self.fields[field_name].widget.attrs.update({
#                 'autocomplete': 'new-password',
#                 'minlength': '8',
#                 'pattern': PASSWORD_PATTERN,
#                 'title': PASSWORD_RULE_MESSAGE,
#                 'required': True,
#             })

#     def clean_full_name(self):
#         return validate_signup_full_name(self.cleaned_data['full_name'])

#     def clean_email(self):
#         email = validate_signup_email(self.cleaned_data['email'])
#         if User.objects.filter(email__iexact=email).exists():
#             raise ValidationError(_('A user with that email already exists.'))
#         return email

#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#         if password1 and password2 and password1 != password2:
#             raise ValidationError(_("The two password fields didn't match."))
#         if password2:
#             validate_signup_password(password2)
#         return password2

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         full_name = self.cleaned_data['full_name']
#         user.username = build_unique_username(
#             self.cleaned_data['email'],
#             self.cleaned_data['full_name'],
#         )
#         user.first_name = self.cleaned_data['full_name']
#         user.last_name = ''
#         user.email = self.cleaned_data['email']
#         user.is_active = False
#         if commit:
#             user.save()
#         return user


# class LoginForm(forms.Form):
#     email = forms.EmailField(
#         label=_('Email'),
#         max_length=EMAIL_MAX_LENGTH,
#         widget=forms.EmailInput(attrs={
#             'autocomplete': 'email',
#         }),
#     )
#     password = forms.CharField(
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'autocomplete': 'current-password',
#         }),
#     )

#     def __init__(self, request=None, *args, **kwargs):
#         self.request = request
#         self.user_cache = None
#         super().__init__(*args, **kwargs)

#     def clean(self):
#         cleaned_data = super().clean()
#         email = cleaned_data.get('email')
#         password = cleaned_data.get('password')
#         if not email or not password:
#             return cleaned_data

#         user = User.objects.filter(email__iexact=email.strip()).first()
#         if user:
#             self.user_cache = authenticate(
#                 self.request,
#                 username=user.get_username(),
#                 password=password,
#             )
#             if self.user_cache is None and user.check_password(password) and not user.is_active:
#                 raise ValidationError(
#                     _('Please verify your email address before logging in.'),
#                     code='inactive',
#                 )

#         if self.user_cache is None:
#             raise ValidationError(_('Invalid credentials.'), code='invalid_login')

#         self.confirm_login_allowed(self.user_cache)
#         return cleaned_data

#     def confirm_login_allowed(self, user):
#         if not user.is_active:
#             raise ValidationError(
#                 _('Please verify your email address before logging in.'),
#                 code='inactive',
#             )

#     def get_user(self):
#         return self.user_cache
