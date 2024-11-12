from django.urls import path
from .views import employee_info_api, camera_location_api, transaction_api, image_api, upload_emp_image, upload_transaction_image

urlpatterns = [
    path('employees', employee_info_api, name='employee_info_api'),
    path('employees/<str:emp_id>/', employee_info_api, name='employee-info-detail'),  # For PUT/PATCH
    path('camera_locations', camera_location_api, name='camera_location_api'),
    path('transactions', transaction_api, name='transaction_api'),
    path('images', image_api, name='image_api'),
    path('upload_emp_image', upload_emp_image, name='upload_emp_image_api'),
    path('upload_transaction_image', upload_transaction_image, name='upload_transaction_image_api'),
]