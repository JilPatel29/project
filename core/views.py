from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
# from .forms import CustomUserCreationForm
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home page after login
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user to the database
            return redirect('login')  # Redirect to the login page after successful signup
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Basic validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'signup.html')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        # Log the user in and redirect to the home page
        login(request, user)
        return redirect('home')  # Replace 'home' with the correct URL name for your home page

    return render(request, 'signup.html')

def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

def gallery(request):
    return render(request, 'gallery.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    return render(request, 'services.html')

def booking(request):
    return render(request, 'booking.html')

def process_booking(request):
    # Implement booking processing logic here
    return render(request, 'booking_success.html')

# def blog(request):
#     return render(request, 'core/home/templates/blog.html')  # Ensure blog.html exists in your templates

def blog(request):
    return render(request, 'blog.html')