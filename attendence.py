import requests
import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
import dotenv
import json

dotenv.load_dotenv()

cred = credentials.Certificate("classlogger-api.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

students = db.collection("students")

for doc in students.stream():
    print(doc.id)
    print(doc.to_dict())