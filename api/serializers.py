from rest_framework import serializers
from .models import employee_info, camera_location, transaction, employee_image

class EmployeeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = employee_info
        fields = '__all__'

class CameraLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = camera_location
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    employee_info = EmployeeInfoSerializer(read_only=True, source='emp_id')  # Assumes `emp_id` is the ForeignKey
    camera_location = CameraLocationSerializer(read_only=True, source='location_id')
    class Meta:
        model = transaction
        fields = '__all__'

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = employee_image
        fields = '__all__'