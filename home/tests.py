from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Service, Gallery, Booking, Package, Payment, CustomUser
import json

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
            price=1000
        )

    def test_signup_valid(self):
        """TC001: Verify user can register with valid details"""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'phone_number': '1234567890'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to email verification

    def test_login_valid(self):
        """TC002: Verify login with valid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after login

    def test_login_invalid(self):
        """TC003: Verify login fails with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'wrong@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stays on login page
        self.assertContains(response, 'Invalid username or password')

    def test_services_listing(self):
        """TC004: Verify all services load correctly"""
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services.html')

    def test_gallery_detail(self):
        """TC005: Verify gallery details show correctly"""
        response = self.client.get(reverse('gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gallery.html')

    def test_booking_requires_login(self):
        """TC008: Verify booking requires login"""
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_booking_with_login(self):
        """TC009: Verify booking with valid details"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.post(reverse('process_booking'), {
            'package': self.package.id,
            'booking_date': '2025-05-01',
            'booking_time': '10:00',
            'payment_method': 'cash',
            'phone': '1234567890'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_unauthorized_admin_access(self):
        """TC015: Verify unauthorized admin access is blocked"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirects to admin login

    def test_logout(self):
        """TC016: Verify logout functionality"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirects after logout
