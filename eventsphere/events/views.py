from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import SignupForm
from django.contrib.auth.models import User
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from django.contrib.auth.decorators import login_required
# from .models import Event
# from django.shortcuts import get_object_or_404
# import json

class CustomLoginView(LoginView):
    template_name = 'events/login.html'

    def get_success_url(self):
        # Redirect to the URL with the username
        return reverse_lazy('user_profile', kwargs={'username': self.request.user.username})



def user_profile_view(request, username):
    user = User.objects.get(username=username)
    return render(request, 'events/profile.html', {'profile_user': user})

# User Signup
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(user)
            login(request, user)  # Log in the user immediately after signup
            return redirect(f'/events/{user.username}')  # Redirect to the home page after signup
    else:
        form = SignupForm()
    return render(request, 'events/signup.html', {'form': form})

# User login
# @csrf_exempt
# def login_view(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         username = data.get("username")
#         password = data.get("password")
        
#         if not username or not password:
#             return JsonResponse({"status": "error", "message": "Username and password are required"}, status=400)

#         user = authenticate(username=username, password=password)

#         if user is not None:
#             auth_login(request, user)
#             return JsonResponse({"status": "success", "message": "Login successful"}, status=200)
#         else:
#             return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=400)

#     return JsonResponse({"status": "error", "message": "Only POST requests are allowed"}, status=400)

