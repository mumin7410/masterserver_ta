from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import employee_info, camera_location, transaction, employee_image, transaction_image
from .serializers import EmployeeInfoSerializer, CameraLocationSerializer, TransactionSerializer, ImagesSerializer
import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import datetime
from masterserver.celery import produce_vector
import logging
import environ

env = environ.Env()
logger = logging.getLogger(__name__)

# Function zone
def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Employee Info API View
@api_view(['GET', 'POST'])
def employee_info_api(request):
    if request.method == 'GET':
        employees = employee_info.objects.all()
        serializer = EmployeeInfoSerializer(employees, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EmployeeInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Camera Location API View
@api_view(['GET', 'POST'])
def camera_location_api(request):
    if request.method == 'GET':
        locations = camera_location.objects.all()
        serializer = CameraLocationSerializer(locations, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CameraLocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Transaction API View
@api_view(['GET', 'POST'])
def transaction_api(request):
    if request.method == 'GET':
        transactions = transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Image API View
@api_view(['GET', 'POST'])
def image_api(request):
    if request.method == 'GET':
        images = employee_image.objects.all()
        serializer = ImagesSerializer(images, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ImagesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#upload_emp_image API
@api_view(['POST'])
def upload_emp_image(request):
    """
    View to handle image upload, save it to media folder, and generate a URL.
    """
    if 'image' not in request.FILES:
        return Response({'error': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    image_file = request.FILES['image']
    
    # Retrieve employee_info instance by emp_id from request
    emp_id = request.data.get('emp_id')
    name = request.data.get('name')
    employee = get_object_or_404(employee_info, emp_id=emp_id)

    # Change the file name and create a directory if it doesn't exist
    filename = f"emp_image/{emp_id}_{name}/{emp_id}_{name}_{timestamp()}.jpg"  # Save to emp_image directory
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the image file
    with open(file_path, 'wb+') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)

    # Generate the URL for the saved image
    image_url = os.path.join(env("DOMAIN"),settings.MEDIA_URL, filename)

    # Use image.objects.create() to create and save the instance with employee_info foreign key
    try:
        image_instance = employee_image.objects.create(
            emp_id=employee,  # Pass the employee_info instance here
            image=image_url
        )
        
        # Trigger the Celery task
        produce_vector.delay()

        return Response({
            'emp_id': image_instance.emp_id.emp_id,  # Return the emp_id as a string
            'image': image_instance.image,  # Return the image URL
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#upload_transaction_image API
@api_view(['POST'])
def upload_transaction_image(request):
    print("==== upload_transaction_image API is triggered ====")
    print(f"Request path: {request.path}")
    print(f"Request EmpID: {request.data.get('emp_id')}")
    """
    View to handle image upload, save it to media folder, and generate a URL.
    """
    if 'image' not in request.FILES:
        return Response({'error': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    image_file = request.FILES['image']
    
    # Retrieve employee_info instance by emp_id from request
    emp_id = request.data.get('emp_id')
    name = request.data.get('name')

    # Validate that the employee exists in the database
    try:
        employee = employee_info.objects.get(emp_id=emp_id)
    except employee_info.DoesNotExist:
        return Response({'error': f'Employee with emp_id {emp_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Change the file name and create a directory if it doesn't exist
    filename = f"transaction_image/{emp_id}_{name}/{emp_id}_{name}_{timestamp()}.jpg"  # Save to emp_image directory
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the image file
    with open(file_path, 'wb+') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)

    # Generate the URL for the saved image
    image_url = os.path.join(env("DOMAIN"),settings.MEDIA_URL, filename)

    # Use image.objects.create() to create and save the instance with employee_info foreign key
    try:
        image_instance = transaction_image.objects.create(
            emp_id=employee,  # Pass the employee_info instance here
            image=image_url
        )
        
        # Trigger the Celery task
        produce_vector.delay()

        return Response({
            'emp_id': image_instance.emp_id.emp_id,  # Return the emp_id as a string
            'image': image_instance.image,  # Return the image URL
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)