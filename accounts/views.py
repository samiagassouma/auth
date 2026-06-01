# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.contrib.auth import login
# from django.http import Http404
# from django.shortcuts import redirect, render
# from django.views.decorators.csrf import csrf_exempt

# from .emails import send_verification_email
# from .forms import LoginForm, SignupForm
# from .models import EmailVerificationToken


# def home(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard')
#     return redirect('login')

# @csrf_exempt
# def signup_view(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard')

#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             send_verification_email(request, user)
#             return redirect('check_email')
#     else:
#         form = SignupForm()

#     return render(request, 'registration/signup.html', {'form': form})


# def check_email(request):
#     return render(request, 'registration/check_email.html')


# def verify_email(request, token):
#     try:
#         verification = EmailVerificationToken.objects.select_related('user').get(token=token)
#     except EmailVerificationToken.DoesNotExist as exc:
#         raise Http404('Verification link not found.') from exc

#     if verification.is_verified:
#         messages.info(request, 'Your email is already verified. You can log in.')
#         return redirect('login')

#     if verification.is_expired:
#         messages.error(request, 'This verification link has expired. Please sign up again.')
#         verification.user.delete()
#         return redirect('signup')

#     user = verification.user
#     user.is_active = True
#     user.save(update_fields=['is_active'])
#     verification.mark_verified()
#     login(request, user)
#     messages.success(request, 'Your email has been verified.')
#     return redirect('dashboard')


# @login_required
# def dashboard(request):
#     return render(request, 'accounts/dashboard.html')
