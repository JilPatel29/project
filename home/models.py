from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class CustomUser(AbstractUser):
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_active = models.BooleanField(default=False)  # Default to inactive until email verified

    groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, 
        related_name="customuser_permissions_set", 
        blank=True
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=100, default='General')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['name']

class Blog(models.Model):
    title = models.CharField(max_length=200, default="Untitled Blog")
    content = models.TextField(default="")
    image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    short_description = models.TextField(max_length=200, blank=True)
    read_time = models.IntegerField(default=5)
    category = models.CharField(max_length=50, default='General')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Gallery(models.Model):
    CATEGORY_CHOICES = [
        ('wedding', 'Wedding'),
        ('prewedding', 'Pre-Wedding'),
        ('birthday', 'Birthday'),
        ('outdoor', 'Outdoor'),
        ('maternity', 'Maternity')
    ]

    image = models.ImageField(upload_to='gallery/', blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='wedding')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Galleries'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.category.capitalize()} - {self.uploaded_at.strftime('%Y-%m-%d')}"


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

class Package(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    )

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking for {self.customer_name} on {self.booking_date}"

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.package.price
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    )
    
    PAYMENT_METHOD = (
        ('cash', 'Cash on Visit'),
        ('online', 'Online Payment')
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment', default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Booking #{self.booking.id} - {self.get_payment_status_display()}"

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.booking.total_amount
        super().save(*args, **kwargs)

class Testimonial(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=False, blank=False)
    message = models.TextField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    date_submitted = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=False)

    def __str__(self):
        if self.booking:
            return f"Testimonial by {self.booking.customer_name}"
        return "Testimonial (No Booking Linked)"


    class Meta:
        ordering = ['-date_submitted']