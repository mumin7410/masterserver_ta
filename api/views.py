from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
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
@api_view(['GET', 'POST', 'PUT', 'PATCH'])
def employee_info_api(request, emp_id=None):
    if request.method == 'GET':
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('pageSize', 10))  # Default to 10 if pageSize not provided
        paginator.page = int(request.GET.get('page', 1))  # Default to page 1 if page not provided

        employees = employee_info.objects.all()
        result_page = paginator.paginate_queryset(employees, request)
        serializer = EmployeeInfoSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = EmployeeInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT' or request.method == 'PATCH':
        # Check if the employee exists
        try:
            employee = employee_info.objects.get(emp_id=emp_id)
        except employee_info.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Partial update or full update based on the method (PATCH or PUT)
        serializer = EmployeeInfoSerializer(employee, data=request.data, partial=(request.method == 'PATCH'))
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Camera Location API View
@api_view(['GET', 'POST', 'PUT'])
def camera_location_api(request):
    if request.method == 'GET':
        # Get the 'id' parameter from the query string (if provided)
        location_id = request.GET.get('id', None)

        # Apply filtering based on the provided 'id', if any
        if location_id:
            try:
                location_id = int(location_id)  # Ensure it's an integer
                locations = camera_location.objects.filter(id=location_id)
            except ValueError:
                return Response({"error": "Invalid ID format. ID should be an integer."}, status=400)
        else:
            locations = camera_location.objects.all()

        # Pagination logic
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('pageSize', 10))  # Default to 10 if pageSize not provided
        paginator.page = int(request.GET.get('page', 1))  # Default to page 1 if page not provided

        result_page = paginator.paginate_queryset(locations, request)
        serializer = CameraLocationSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = CameraLocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        # Get the 'id' parameter from the request to update the camera location
        location_id = request.data.get('location_id', None)

        if not location_id:
            return Response({"error": "ID is required to update the camera location."}, status=400)

        try:
            location = camera_location.objects.get(id=location_id)  # Find the location by ID
        except camera_location.DoesNotExist:
            return Response({"error": "Location not found."}, status=404)

        # Check if 'status' is provided in the request data to update
        status_camera = request.data.get('status', None)
        if status_camera not in ['active', 'inactive']:
            return Response({"error": "Invalid status. Valid values are 'active' or 'inactive'."}, status=400)

        # Update the status
        location.status = status_camera
        location.save()

        # Return the updated camera location data
        serializer = CameraLocationSerializer(location)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Transaction API View
@api_view(['GET', 'POST'])
def transaction_api(request):
    if request.method == 'GET':
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('pageSize', 10))  # Default to 10 if pageSize not provided
        paginator.page = int(request.GET.get('page', 1))  # Default to page 1 if page not provided
        
        transactions = transaction.objects.all()
        result_page = paginator.paginate_queryset(transactions, request)
        serializer = TransactionSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)

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
        emp_id = request.GET.get('emp_id', None)
        if emp_id:
            # If emp_id is provided, filter the images by emp_id
            images = employee_image.objects.filter(emp_id=emp_id)
        else:
            # If no emp_id is provided, return all images
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
        # produce_vector.delay()

        return Response({
            'emp_id': image_instance.emp_id.emp_id,  # Return the emp_id as a string
            'image': image_instance.image,  # Return the image URL
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)