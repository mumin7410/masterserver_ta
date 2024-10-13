from django.db import models
import os
from django.conf import settings
import redis
import pandas as pd
# Create your models here.
class employee_info(models.Model):
    emp_id = models.CharField(max_length=20, primary_key=True)  # Field for employee ID, adjusted to IntegerField
    name = models.CharField(max_length=100)  # Field for name
    last_name = models.CharField(max_length=100)  # Field for name
    email = models.EmailField()  # Field for employee email
    phone = models.CharField(max_length=10)  # Field for employee phone
    role = models.CharField(max_length=100)  # Field for employee role
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the record is created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for when the record is updated
    
    def __str__(self):
        return f'{self.emp_id}'

class camera_location(models.Model):
    id = models.AutoField(primary_key=True)
    location_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"location-id: {self.id} __ location-name: {self.location_name}"

class transaction(models.Model):
    id = models.AutoField(primary_key=True)
    emp_id = models.ForeignKey(employee_info, on_delete=models.CASCADE)
    location_id = models.ForeignKey(camera_location, on_delete=models.CASCADE)
    image = models.URLField(max_length=200)  # Field to store the image file
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'emp-id: {self.emp_id} __ location-id: {self.id}'
    
class employee_image(models.Model):
    id = models.AutoField(primary_key=True)
    emp_id = models.ForeignKey(employee_info, on_delete=models.CASCADE)
    image = models.URLField(max_length=200)  # Field to store the image file
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # Parse the image URL to extract the file name
        if self.image:
            image_name = self.image.split("/")[-1]  # Get the actual file name from the URL
            image_directory = f"{self.emp_id}_{image_name.split('_')[1]}"
            print(f'image_directory ====> {image_directory}')
            image_path = os.path.join(settings.MEDIA_ROOT, "emp_image", image_directory, image_name)

            # Delete the image from the filesystem if it exists
            if os.path.exists(image_path):
                os.remove(image_path)

        # Call the parent class's delete method to delete the model instance from the database
        super().delete(*args, **kwargs)

        #update redis after deleted
        update_redis_data()
    
    def __str__(self):
        return f'{self.emp_id}_{self.image}'

class transaction_image(models.Model):
    id = models.AutoField(primary_key=True)
    emp_id = models.ForeignKey(employee_info, on_delete=models.CASCADE)
    image = models.URLField(max_length=200)  # Field to store the image file
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        # Parse the image URL to extract the file name
        if self.image:
            image_name = self.image.split("/")[-1]  # Get the actual file name from the URL
            image_directory = f"{self.emp_id}_{image_name.split('_')[1]}"
            print(f'image_directory ====> {image_directory}')
            image_path = os.path.join(settings.MEDIA_ROOT, "transaction_image", image_directory, image_name)

            # Delete the image from the filesystem if it exists
            if os.path.exists(image_path):
                os.remove(image_path)

        # Call the parent class's delete method to delete the model instance from the database
        super().delete(*args, **kwargs)

        #update redis after deleted
        update_redis_data()
    
    def __str__(self):
        return f'{self.emp_id}_{self.image}'

def update_redis_data():
    # Connect to Redis
    r = redis.Redis(host='sony-redis', port=6379, password='2vBuMI9QeQ9tMGeG', db=0)
    json_data = r.get('employee_data')

    if json_data:
        json_str = json_data.decode('utf-8')
        df_existing = pd.read_json(json_str, dtype={'emp_id': str})

        # Prepare a list of files currently in the media directory
        all_files_in_directory = []
        listDir = os.listdir('/app/media/emp_image')
        
        for res in listDir:
            img_files = os.listdir(path=f'/app/media/emp_image/{res}')
            all_files_in_directory.extend(img_files)

        # Remove entries for deleted images
        df_existing = df_existing[df_existing['file_name'].isin(all_files_in_directory)]

        # Convert DataFrame to JSON without index and store in Redis
        json_data = df_existing.to_json(orient='records')
        r.set('employee_data', json_data)