from functools import cache
from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from core import settings
from .models import ContactUs, Service, Blog, Gallery, Testimonial
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Booking, Payment, Package
import razorpay
import json
import hmac
import hashlib


                        
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            if 'remove_profile_pic' in request.POST:
                if request.user.profile_pic:
                    request.user.profile_pic.delete()
                    request.user.profile_pic = None
                    request.user.save()
                messages.success(request, 'Profile picture removed successfully!')
                return redirect('edit_profile')

            # Get form data
            username = request.POST.get('username')
            phone_number = request.POST.get('phone_number')
            
            # Update user fields
            request.user.username = username
            request.user.phone_number = phone_number
            
            # Handle profile picture
            if 'profile_pic' in request.FILES:
                if request.user.profile_pic:
                    request.user.profile_pic.delete()
                request.user.profile_pic = request.FILES['profile_pic']
            
            request.user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            
    return render(request, 'edit_profile.html')

@login_required
def process_booking(request):
    if request.method == "POST":
        try:
            # Get form data
            package_id = request.POST.get('package')
            booking_date = request.POST.get('booking_date')
            booking_time = request.POST.get('booking_time')
            phone = request.POST.get('phone')
            
            # Get the package
            package = Package.objects.get(id=package_id)
            
            # Get CustomUser instance
            try:
                custom_user = CustomUser.objects.get(id=request.user.id)
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User not found'
                })
            
            # Create booking
            booking = Booking.objects.create(
                customer=custom_user,
                customer_name=request.user.username,
                customer_email=request.user.email,
                customer_phone=phone,
                package=package,
                booking_date=booking_date,
                booking_time=booking_time,
                total_amount=package.price,
                status='pending'
            )

            # Store booking ID in session
            request.session['booking_id'] = booking.id

            # Create Razorpay order
            amount_in_paise = int(float(package.price) * 100)  # Convert to paise
            order_currency = 'INR'
            order_receipt = f'order_rcptid_{booking.id}'
            
            razorpay_order = razorpay_client.order.create({
                'amount': amount_in_paise,
                'currency': order_currency,
                'receipt': order_receipt,
                'payment_capture': 1
            })

            # Create payment record
            payment = Payment.objects.create(
                booking=booking,
                amount=package.price,
                payment_method='online',
                payment_status='pending',
                razorpay_order_id=razorpay_order['id']
            )

            # Return data needed for Razorpay checkout
            return JsonResponse({
                'status': 'success',
                'order_id': razorpay_order['id'],
                'amount': amount_in_paise,
                'currency': order_currency,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'customer_name': booking.customer_name,
                'customer_email': booking.customer_email,
                'customer_phone': booking.customer_phone
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

def booking(request):
    if not request.user.is_authenticated:
        return redirect('login')
    packages = Package.objects.all()
    context = {
        'packages': packages
    }
    return render(request, 'booking.html', context)


@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_signature = data.get('razorpay_signature')

            params_dict = {
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)

                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                booking = payment.booking

                payment.payment_status = 'completed'
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save()

                booking.status = 'confirmed'
                booking.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment successful',
                    'redirect_url': '/booking-confirmation/'
                })

            except razorpay.errors.SignatureVerificationError:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.payment_status = 'failed'
                payment.save()

                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment verification failed'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

def generate_otp():
    return str(random.randint(100000, 999999))

def send_verification_email(email, otp):
    subject = 'Email Verification OTP'
    message = f'Your OTP for email verification is: {otp}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list)

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Validation
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(request, 'signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, 'signup.html')

        # Create inactive user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.is_active = False
        user.save()

        # Generate and store OTP
        otp = generate_otp()
        request.session['email_otp'] = otp
        request.session['user_id'] = user.id

        # Send verification email
        send_verification_email(email, otp)
        
        messages.success(request, "Please check your email for verification code")
        return redirect('verify_email')

    return render(request, 'signup.html')

def verify_email(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_otp = request.session.get('email_otp')
        user_id = request.session.get('user_id')

        if user_otp == stored_otp:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            # Clear session
            del request.session['email_otp']
            del request.session['user_id']

            messages.success(request, "Email verified successfully! Please login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'verify_email.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, "Successfully logged in!")
                return redirect('home')
            else:
                messages.error(request, "Please verify your email first")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect('home')

def index(request):
    # Get latest approved testimonials
    testimonials = Testimonial.objects.filter(is_displayed=True).order_by('-date_submitted')[:3]
    
    # Get gallery items
    gallery_items = Gallery.objects.all().order_by('-uploaded_at')[:6]
    
    # Get services
    services = Service.objects.all()
    
    context = {
        'testimonials': testimonials,
        'gallery_items': gallery_items,
        'services': services,
    }
    
    return render(request, 'index.html', context)

def home(request):
    # Similar to index view
    testimonials = Testimonial.objects.filter(is_displayed=True).order_by('-date_submitted')[:6]
    gallery_items = Gallery.objects.all().order_by('-uploaded_at')[:12]
    services = Service.objects.all()
    
    context = {
        'testimonials': testimonials,
        'gallery_items': gallery_items,
        'services': services,
    }
    
    return render(request, 'home.html', context)

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def admin_view(request):
    return redirect('/admin/')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'profile.html', context)


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'forgot_password.html')

        try:
            # Try to find user by email (case-insensitive)
            user = User.objects.get(email__iexact=email)
            
            # Store email in session to verify in reset_password view
            request.session['reset_password_email'] = email
            
            messages.success(request, "You can now reset your password.")
            return redirect('reset_password', email=email)
            
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
            return render(request, 'forgot_password.html', {'email': email})

    return render(request, 'forgot_password.html')


def reset_password(request, email):
    stored_email = request.session.get('reset_password_email')

    if stored_email != email:
        messages.error(request, "Invalid or expired reset link.")
        return redirect('login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'reset_password.html')

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'reset_password.html')

        try:
            user = User.objects.get(email__iexact=email)
            user.set_password(new_password)
            user.save()

            # Clear session data
            request.session.pop('reset_password_email', None)

            messages.success(request, "Password has been reset successfully. Please login with your new password.")
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('login')

    return render(request, 'reset_password.html')



@login_required
def add_testimonial(request, booking_id):
    # Get the booking or return 404 if not found
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if testimonial already exists for this booking
    existing_testimonial = Testimonial.objects.filter(booking=booking).first()
    if existing_testimonial:
        messages.error(request, 'You have already submitted a review for this booking.')
        return redirect('booking_confirmation')

    if request.method == 'POST':
        message = request.POST.get('message')
        rating = request.POST.get('rating')
        
        if message and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:  # Validate rating range
                    testimonial = Testimonial.objects.create(
                        booking=booking,
                        message=message,
                        rating=rating,
                        is_displayed=True  # Requires admin approval if false
                    )
                    messages.success(request, 'Thank you for your review! It will be displayed after approval.')
                    return redirect('booking_confirmation')
                else:
                    messages.error(request, 'Please provide a valid rating between 1 and 5.')
            except ValueError:
                messages.error(request, 'Invalid rating value.')
        else:
            messages.error(request, 'Please provide both a message and rating.')
    
    return render(request, 'add_testimonial.html', {'booking': booking})

def booking_confirmation(request):
    booking_id = request.session.get('booking_id')
    if not booking_id:
        return redirect('booking')
        
    booking = get_object_or_404(Booking, id=booking_id)
    has_testimonial = Testimonial.objects.filter(booking=booking).exists()
    
    context = {
        'booking': booking,
        'has_testimonial': has_testimonial
    }
    
    return render(request, 'booking_confirmation.html', context)

def services(request):
    active_services = Service.objects.filter(is_active=True).order_by('name')
    return render(request, "services.html", {'services': active_services})

def gallery(request):
    categories = {
        'wedding': Gallery.objects.filter(category='wedding'),
        'prewedding': Gallery.objects.filter(category='prewedding'),
        'birthday': Gallery.objects.filter(category='birthday'),
        'outdoor': Gallery.objects.filter(category='outdoor'),
        'maternity': Gallery.objects.filter(category='maternity'),
    }
    return render(request, 'gallery.html', {'categories': categories})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        contact = ContactUs(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        contact.save()
        
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
        
    return render(request, "contact.html")

def blog(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, "blog.html", {'blogs': blogs})

def blog_detail(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    return render(request, "blog_detail.html", {'blog': blog})

