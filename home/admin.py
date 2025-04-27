from django.contrib import admin
from .models import Service
from .models import Payment
from .models import Blog
from .models import Gallery
from .models import ContactUs
from .models import Package
from .models import Booking
from .models import Testimonial

class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'booking_date', 'booking_time', 'status', 'total_amount', 'get_selected_packages')
    list_filter = ('status', 'booking_date')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')

    def get_selected_packages(self, obj):
        return ", ".join([package.name for package in obj.packages.all()])
    get_selected_packages.short_description = 'Selected Packages'

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('payment_method', 'payment_status')
    search_fields = ('booking__customer_name', 'booking__customer_email')
    readonly_fields = ('payment_status',)

# Register your models
admin.site.register(Service)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Blog)
admin.site.register(Gallery)
admin.site.register(ContactUs)
admin.site.register(Package)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Testimonial)