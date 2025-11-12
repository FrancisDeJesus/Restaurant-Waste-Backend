import os
import firebase_admin
from firebase_admin import credentials, auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(BASE_DIR, "restaurant-waste-app-75ce6-firebase-adminsdk-fbsvc-ac4725dca3.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
