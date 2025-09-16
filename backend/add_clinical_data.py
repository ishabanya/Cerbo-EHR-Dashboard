#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000/api/v1"

def add_sample_clinical_data():
    
    vital_signs = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": datetime.now().isoformat(),
        "record_type": "vital_signs",
        "title": "Vital Signs - Routine Check",
        "temperature": 98.6,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "heart_rate": 72,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "weight": 150.0,
        "height": 68.0,
        "pain_scale": 0,
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/clinical-records/", json=vital_signs)
    if response.status_code == 201:
        print("✅ Added vital signs record")
    else:
        print(f"❌ Failed to add vital signs: {response.text[:200]}")
    
    allergy1 = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "record_type": "allergy",
        "title": "Allergy: Penicillin",
        "allergen": "Penicillin",
        "allergy_reaction": "Hives, shortness of breath",
        "allergy_severity": "moderate",
        "status": "active"
    }
    
    allergy2 = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": (datetime.now() - timedelta(days=45)).isoformat(),
        "record_type": "allergy",
        "title": "Allergy: Shellfish",
        "allergen": "Shellfish",
        "allergy_reaction": "Swelling, nausea",
        "allergy_severity": "high",
        "status": "active"
    }
    
    for allergy in [allergy1, allergy2]:
        response = requests.post(f"{BASE_URL}/clinical-records/", json=allergy)
        if response.status_code == 201:
            print(f"✅ Added allergy record: {allergy['allergen']}")
        else:
            print(f"❌ Failed to add allergy: {response.text[:200]}")
    
    med1 = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "record_type": "prescription",
        "title": "Prescription: Lisinopril",
        "medication_name": "Lisinopril",
        "dosage": "10mg",
        "frequency": "Once daily",
        "duration": "30 days",
        "prescribing_instructions": "Take with food. Monitor blood pressure.",
        "status": "active"
    }
    
    med2 = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": (datetime.now() - timedelta(days=14)).isoformat(),
        "record_type": "prescription", 
        "title": "Prescription: Metformin",
        "medication_name": "Metformin",
        "dosage": "500mg",
        "frequency": "Twice daily with meals",
        "duration": "90 days",
        "prescribing_instructions": "Monitor blood glucose levels.",
        "status": "active"
    }
    
    for med in [med1, med2]:
        response = requests.post(f"{BASE_URL}/clinical-records/", json=med)
        if response.status_code == 201:
            print(f"✅ Added medication: {med['medication_name']}")
        else:
            print(f"❌ Failed to add medication: {response.text[:200]}")
    
    diagnosis = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": (datetime.now() - timedelta(days=20)).isoformat(),
        "record_type": "diagnosis",
        "title": "Diagnosis: Hypertension",
        "icd_10_code": "I10",
        "diagnosis_description": "Essential hypertension",
        "diagnosis_status": "active",
        "diagnosis_severity": "moderate",
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/clinical-records/", json=diagnosis)
    if response.status_code == 201:
        print("✅ Added diagnosis record")
    else:
        print(f"❌ Failed to add diagnosis: {response.text[:200]}")

if __name__ == "__main__":
    print("🏥 Adding sample clinical data...")
    add_sample_clinical_data()
    print("✅ Clinical data creation completed!")