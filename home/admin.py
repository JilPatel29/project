from django.contrib import admin
from .models import Service
from .models import Payment
from .models import Blog
from .models import Gallery
from .models import ContactUs
from .models import Package
from .models import Booking
from .models import Testimonial



# Register your model here
admin.site.register(Service)
admin.site.register(Payment)
admin.site.register(Blog)
admin.site.register(Gallery)
admin.site.register(ContactUs)
admin.site.register(Package)
admin.site.register(Booking)
admin.site.register(Testimonial)

# class ServiceAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'category')
#     search_fields = ('name',)
#     list_filter = ('category',)

#     def get_category(self, obj):
#         return getattr(obj, 'category', None)
#     get_category.short_description = 'Category'

# admin.site.register(Service, ServiceAdmin) 
