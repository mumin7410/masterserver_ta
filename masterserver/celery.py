import os
from django.conf import settings
from datetime import datetime, timezone, timedelta
from celery import Celery

import pandas as pd
import redis
import json
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise
import environ
env = environ.Env()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "masterserver.settings")
app = Celery("masterserver")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def produce_vector(self):
    # Connect to Redis
    r = redis.Redis(host='sony-redis', port=6379, password='2vBuMI9QeQ9tMGeG', db=0)
    json_data = r.get('employee_data')
    if json_data:
        json_str = json_data.decode('utf-8')
        try:
            #======> case if the value alredy had
            df_existing = pd.read_json(json_str, dtype={'emp_id': str})
            if not df_existing.empty:
                existing_file_name_arr = df_existing['file_name']
                # Configure face analysis
                faceapp = FaceAnalysis(providers=['CPUExecutionProvider'])
                faceapp.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)

                # Prepare DataFrame
                listDir = os.listdir('/app/media/emp_image')
                for res in listDir:
                    img_files = os.listdir(path=f'/app/media/emp_image/{res}')
                    for img_file in img_files:
                        if img_file in existing_file_name_arr.values and json_str != '[]':
                            continue
                        img = cv2.imread(f'/app/media/emp_image/{res}/{img_file}')
                        emp_id = res.split('_')[0]
                        name = res.split('_')[1]
                        faces = faceapp.get(img)
                        for face in faces:
                            new_row = pd.DataFrame({
                                'emp_id': [emp_id],
                                'name': [name],
                                'embedding': [face['embedding'].tolist()],  # Convert embedding to list
                                'file_name': [img_file]
                            })
                            df_existing = pd.concat([df_existing, new_row], ignore_index=True)  # Use pd.concat
                # Convert DataFrame to JSON without index
                json_data = df_existing.to_json(orient='records')
                # Store in Redis
                r.set('employee_data', json_data)
            else: #======> case the value is empty
                # Configure face analysis
                faceapp = FaceAnalysis(providers=['CPUExecutionProvider'])
                faceapp.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)

                # Configure DataFrame
                df = pd.DataFrame(columns=['emp_id', 'name', 'embedding', 'file_name'])

                # Prepare DataFrame
                listDir = os.listdir('/app/media/emp_image')
                for res in listDir:
                    img_files = os.listdir(path=f'/app/media/emp_image/{res}')
                    for img_file in img_files:
                        img = cv2.imread(f'/app/media/emp_image/{res}/{img_file}')
                        emp_id = res.split('_')[0]
                        name = res.split('_')[1]
                        faces = faceapp.get(img)
                        for face in faces:
                            new_row = pd.DataFrame({
                                'emp_id': [emp_id],
                                'name': [name],
                                'embedding': [face['embedding'].tolist()],  # Convert embedding to list
                                'file_name': [img_file]
                            })
                            df = pd.concat([df, new_row], ignore_index=True)  # Use pd.concat
                # Convert DataFrame to JSON without index
                json_data = df.to_json(orient='records')
                # Store in Redis
                r.set('employee_data', json_data)
        except ValueError as e:
            print(f"Error reading JSON: {e}")
    else: #======> case initial key
        faceapp = FaceAnalysis(providers=['CPUExecutionProvider'])
        faceapp.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)
        # Configure DataFrame
        df = pd.DataFrame(columns=['emp_id', 'name', 'embedding', 'file_name'])

        # Prepare DataFrame
        listDir = os.listdir('/app/media/emp_image')
        for res in listDir:
            img_files = os.listdir(path=f'/app/media/emp_image/{res}')
            for img_file in img_files:
                img = cv2.imread(f'/app/media/emp_image/{res}/{img_file}')
                emp_id = res.split('_')[0]
                name = res.split('_')[1]
                faces = faceapp.get(img)
                for face in faces:
                    new_row = pd.DataFrame({
                        'emp_id': [emp_id],
                        'name': [name],
                        'embedding': [face['embedding'].tolist()],  # Convert embedding to list
                        'file_name': [img_file]
                    })
                    df = pd.concat([df, new_row], ignore_index=True)  # Use pd.concat

        # Convert DataFrame to JSON without index
        json_data = df.to_json(orient='records')
        # Store in Redis
        r.set('employee_data', json_data)

