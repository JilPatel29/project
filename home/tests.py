# home/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Service, Gallery, Booking, Package, Payment, CustomUser
import json
from decimal import Decimal

class StudioTestCases(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='1234567890'
        )
        self.package = Package.objects.create(
            name='Test Package',
            price=Decimal('1000.00')
        )

    def test_signup_valid(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'phone_number': '1234567890'
        })
        self.assertEqual(response.status_code, 302)

    def test_booking_process(self):
        self.client.login(username='test@example.com', password='testpass123')
        
        # Test booking creation
        booking_data = {
            'package': self.package.id,
            'booking_date': '2025-05-01',
            'booking_time': '10:00',
            'payment_method': 'cash',
            'phone': '1234567890'
        }
        
        response = self.client.post(reverse('process_booking'), booking_data)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Verify booking was created
        booking = Booking.objects.filter(customer=self.user).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.package, self.package)
        self.assertEqual(booking.status, 'pending')

    def test_large_amount_payment(self):
        self.client.login(username='test@example.com', password='testpass123')
        
        # Create package with large amount
        large_package = Package.objects.create(
            name='Premium Package',
            price=Decimal('15000.00')
        )
        
        booking_data = {
            'package': large_package.id,
            'booking_date': '2025-05-01',
            'booking_time': '10:00',
            'payment_method': 'online',
            'phone': '1234567890'
        }
        
        response = self.client.post(reverse('process_booking'), booking_data)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('order_id', data)
        self.assertIn('amount', data)

    def test_payment_callback(self):
        self.client.login(username='test@example.com', password='testpass123')
        
        # Create a booking and payment
        booking = Booking.objects.create(
            customer=self.user,
            customer_name=self.user.username,
            customer_email=self.user.email,
            customer_phone='1234567890',
            package=self.package,
            booking_date='2025-05-01',
            booking_time='10:00',
            total_amount=self.package.price,
            status='pending'
        )
        
        payment = Payment.objects.create(
            booking=booking,
            amount=self.package.price,
            payment_method='online',
            payment_status='pending',
            razorpay_order_id='order_test123'
        )
        
        callback_data = {
            'razorpay_payment_id': 'pay_test123',
            'razorpay_order_id': 'order_test123',
            'razorpay_signature': 'test_signature'
        }
        
        response = self.client.post(
            reverse('payment_callback'),
            data=json.dumps(callback_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
