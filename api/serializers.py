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
    class Meta:
        model = transaction
        fields = '__all__'

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = employee_image
        fields = '__all__'