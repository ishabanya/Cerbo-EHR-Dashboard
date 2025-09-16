#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000/api/v1"

SAMPLE_PATIENTS = [
    {
        "first_name": "Alice",
        "last_name": "Johnson",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "email": "alice.johnson@email.com",
        "phone_primary": "5550001101",
        "address_line_1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "emergency_contact_name": "Bob Johnson",
        "emergency_contact_phone": "5550001102",
        "allergies": ["Penicillin", "Shellfish"],
        "medical_conditions": ["Hypertension", "Type 2 Diabetes"]
    },
    {
        "first_name": "Michael",
        "last_name": "Chen",
        "date_of_birth": "1978-07-22",
        "gender": "male",
        "email": "michael.chen@email.com",
        "phone_primary": "5550002201",
        "address_line_1": "456 Oak Ave",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90210",
        "emergency_contact_name": "Sarah Chen",
        "emergency_contact_phone": "5550002202",
        "allergies": ["Sulfa drugs"],
        "medical_conditions": ["Asthma"]
    },
    {
        "first_name": "Sarah",
        "last_name": "Williams",
        "date_of_birth": "1992-12-08",
        "gender": "female",
        "email": "sarah.williams@email.com",
        "phone_primary": "5550003301",
        "address_line_1": "789 Pine Rd",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "emergency_contact_name": "David Williams",
        "emergency_contact_phone": "5550003302",
        "allergies": [],
        "medical_conditions": []
    },
    {
        "first_name": "Robert",
        "last_name": "Davis",
        "date_of_birth": "1965-09-30",
        "gender": "male",
        "email": "robert.davis@email.com",
        "phone_primary": "5550004401",
        "address_line_1": "321 Elm St",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77001",
        "emergency_contact_name": "Linda Davis",
        "emergency_contact_phone": "5550004402",
        "allergies": ["Latex", "Peanuts"],
        "medical_conditions": ["High Cholesterol", "Arthritis"]
    },
    {
        "first_name": "Emma",
        "last_name": "Martinez",
        "date_of_birth": "2000-04-18",
        "gender": "female",
        "email": "emma.martinez@email.com",
        "phone_primary": "5550005501",
        "address_line_1": "654 Maple Dr",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85001",
        "emergency_contact_name": "Carlos Martinez",
        "emergency_contact_phone": "5550005502",
        "allergies": ["Codeine"],
        "medical_conditions": ["Migraine"]
    }
]

def add_patients():
    print("Adding sample patients...")
    patient_ids = []
    
    for patient_data in SAMPLE_PATIENTS:
        try:
            response = requests.post(f"{BASE_URL}/patients/", json=patient_data)
            if response.status_code == 201:
                patient = response.json()
                patient_ids.append(patient['id'])
                print(f"✅ Added patient: {patient['first_name']} {patient['last_name']} (ID: {patient['id']})")
            else:
                print(f"❌ Failed to add patient {patient_data['first_name']} {patient_data['last_name']}: {response.text}")
        except Exception as e:
            print(f"❌ Error adding patient {patient_data['first_name']} {patient_data['last_name']}: {e}")
    
    return patient_ids

def add_appointments(patient_ids, provider_id=1):
    print(f"\nAdding sample appointments...")
    
    base_date = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    appointments = []
    for i in range(10):  # 10 appointments
        days_ahead = i % 7
        hour = 9 + (i % 8)  # 9 AM to 4 PM
        appointment_date = base_date + timedelta(days=days_ahead, hours=(hour - 9))
        
        patient_id = patient_ids[i % len(patient_ids)]
        
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_date": appointment_date.isoformat(),
            "duration_minutes": random.choice([30, 45, 60]),
            "appointment_type": random.choice(["consultation", "follow_up", "physical_exam", "procedure"]),
            "status": random.choice(["scheduled", "confirmed", "completed"]),
            "reason_for_visit": random.choice([
                "Annual physical exam",
                "Follow-up visit",
                "Blood pressure check",
                "Medication review",
                "Lab results review",
                "Preventive care",
                "Sick visit"
            ]),
            "chief_complaint": random.choice([
                "Routine checkup",
                "Hypertension management",
                "Diabetes follow-up",
                "Cold symptoms",
                "Joint pain",
                "Headache",
                "Medication refill"
            ])
        }
        appointments.append(appointment_data)
    
    appointment_ids = []
    for appointment_data in appointments:
        try:
            response = requests.post(f"{BASE_URL}/appointments/", json=appointment_data)
            if response.status_code == 201:
                appointment = response.json()
                appointment_ids.append(appointment['id'])
                print(f"✅ Added appointment: {appointment['appointment_date'][:16]} (ID: {appointment['id']})")
            else:
                print(f"❌ Failed to add appointment: {response.text}")
        except Exception as e:
            print(f"❌ Error adding appointment: {e}")
    
    return appointment_ids

def add_clinical_records(patient_ids, appointment_ids, provider_id=1):
    print(f"\nAdding sample clinical records...")
    
    clinical_records = []
    
    for i, (patient_id, appointment_id) in enumerate(zip(patient_ids[:5], appointment_ids[:5])):
        record_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "appointment_id": appointment_id,
            "record_date": datetime.now().isoformat(),
            "record_type": random.choice(["visit_note", "lab_result", "vital_signs"]),
            "chief_complaint": "Routine follow-up",
            "history_of_present_illness": "Patient reports feeling well overall",
            "vital_signs": {
                "temperature": round(random.uniform(97.0, 99.5), 1),
                "blood_pressure_systolic": random.randint(110, 140),
                "blood_pressure_diastolic": random.randint(70, 90),
                "heart_rate": random.randint(60, 100),
                "respiratory_rate": random.randint(12, 20),
                "weight": round(random.uniform(120, 200), 1),
                "height": round(random.uniform(60, 75), 1)
            },
            "assessment_and_plan": "Continue current medications. Follow up in 3 months.",
            "medications_prescribed": ["Lisinopril 10mg daily", "Metformin 500mg twice daily"],
            "diagnoses": [
                {
                    "icd_10_code": "I10",
                    "diagnosis": "Essential hypertension"
                },
                {
                    "icd_10_code": "E11.9", 
                    "diagnosis": "Type 2 diabetes mellitus without complications"
                }
            ],
            "lab_results": {
                "glucose": random.randint(80, 120),
                "cholesterol": random.randint(150, 220),
                "hba1c": round(random.uniform(5.5, 7.5), 1)
            }
        }
        clinical_records.append(record_data)
    
    for record_data in clinical_records:
        try:
            response = requests.post(f"{BASE_URL}/clinical-records/", json=record_data)
            if response.status_code == 201:
                record = response.json()
                print(f"✅ Added clinical record: {record['record_type']} (ID: {record['id']})")
            else:
                print(f"❌ Failed to add clinical record: {response.text}")
        except Exception as e:
            print(f"❌ Error adding clinical record: {e}")

def add_insurance_records(patient_ids):
    print(f"\nAdding sample insurance records...")
    
    insurance_companies = ["Blue Cross Blue Shield", "Aetna", "Cigna", "UnitedHealth", "Kaiser Permanente"]
    
    for patient_id in patient_ids[:3]:  # Add insurance for first 3 patients
        insurance_data = {
            "patient_id": patient_id,
            "insurance_company": random.choice(insurance_companies),
            "policy_number": f"POL{random.randint(100000, 999999)}",
            "member_id": f"MEM{random.randint(100000, 999999)}",
            "group_number": f"GRP{random.randint(1000, 9999)}",
            "insurance_type": random.choice(["primary", "secondary"]),
            "effective_date": (datetime.now() - timedelta(days=365)).date().isoformat(),
            "expiration_date": (datetime.now() + timedelta(days=365)).date().isoformat(),
            "copay_amount": random.choice([10.00, 15.00, 20.00, 25.00]),
            "deductible_amount": random.choice([500.00, 1000.00, 2500.00, 5000.00]),
            "out_of_pocket_max": random.choice([2000.00, 5000.00, 7500.00, 10000.00])
        }
        
        try:
            response = requests.post(f"{BASE_URL}/insurance/", json=insurance_data)
            if response.status_code == 201:
                insurance = response.json()
                print(f"✅ Added insurance: {insurance['insurance_company']} (ID: {insurance['id']})")
            else:
                print(f"❌ Failed to add insurance: {response.text}")
        except Exception as e:
            print(f"❌ Error adding insurance: {e}")

def main():
    print("🏥 Adding sample data to EHR Dashboard...\n")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code != 200:
            print("❌ Backend server not accessible. Make sure it's running on port 8000.")
            return
        
        patient_ids = add_patients()
        if not patient_ids:
            print("❌ No patients were added. Cannot proceed.")
            return
            
        appointment_ids = add_appointments(patient_ids)
        
        if appointment_ids:
            add_clinical_records(patient_ids, appointment_ids)
        
        add_insurance_records(patient_ids)
        
        print(f"\n🎉 Sample data added successfully!")
        print(f"📊 Summary:")
        print(f"   - Patients: {len(patient_ids)}")
        print(f"   - Appointments: {len(appointment_ids)}")
        print(f"   - Clinical records: {min(5, len(patient_ids))}")
        print(f"   - Insurance records: {min(3, len(patient_ids))}")
        
        print(f"\n🌐 You can now test the features at:")
        print(f"   - Frontend: http://localhost:3000")
        print(f"   - API Docs: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend server.")
        print("   Make sure the backend is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()