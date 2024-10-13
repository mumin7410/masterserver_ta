from django.contrib import admin
from .models import employee_info, transaction, camera_location, employee_image, transaction_image

# Admin for employee_image to handle bulk delete properly
class EmployeeImageAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'image', 'created_at')

    # Override the bulk delete action to call delete() on each object
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()  # This will call the model's custom delete method

class TransactionImageAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'image', 'created_at')

    # Override the bulk delete action to call delete() on each object
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()  # This will call the model's custom delete method

# Register your models
admin.site.register(employee_info)
admin.site.register(transaction)
admin.site.register(camera_location)
admin.site.register(employee_image, EmployeeImageAdmin)
admin.site.register(transaction_image, TransactionImageAdmin)
