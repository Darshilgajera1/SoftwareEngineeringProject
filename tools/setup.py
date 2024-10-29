import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()

# Load the service account key path from environment variable
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not service_account_path:
    raise ValueError("Service account key not found in environment variables.")

try:
    firebase_app = firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate(service_account_path)
    firebase_app = firebase_admin.initialize_app(cred)

# Initialize Firestore DB and Firebase Authentication
db = firestore.client()
