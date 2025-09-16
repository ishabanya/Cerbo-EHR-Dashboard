#!/usr/bin/env python3
"""
Test script to demonstrate EHR Dashboard functionality
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_feature(title, func):
    """Test a feature and display results"""
    print(f"\n🔧 {title}")
    print("=" * (len(title) + 4))
    try:
        func()
    except Exception as e:
        print(f"❌ Error: {e}")

def patient_management():
    """Test Patient Management features"""
    
    # Search patients
    response = requests.get(f"{BASE_URL}/patients/", params={'search': 'Alice', 'search_type': 'name'})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search by name: Found {data['total']} patients")
        if data['items']:
            patient = data['items'][0]
            print(f"   - {patient['first_name']} {patient['last_name']} (ID: {patient['id']})")
    
    # Get patient details
    response = requests.get(f"{BASE_URL}/patients/1")
    if response.status_code == 200:
        patient = response.json()
        print(f"✅ Patient Details:")
        print(f"   - Name: {patient['full_name']}")
        print(f"   - Age: {patient['age']}")
        print(f"   - Email: {patient['email']}")
        print(f"   - Phone: {patient['phone_primary']}")
        print(f"   - Address: {patient['address_line_1']}, {patient['city']}, {patient['state']}")
        print(f"   - Emergency Contact: {patient['emergency_contact_name']} ({patient['emergency_contact_phone']})")
    
    # Search by phone
    response = requests.get(f"{BASE_URL}/patients/", params={'search': '5550001101', 'search_type': 'phone'})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search by phone: Found {data['total']} patients")
    
    # Get all patients
    response = requests.get(f"{BASE_URL}/patients/", params={'per_page': 10})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ All patients: Total {data['total']} patients in system")

def appointment_scheduling():
    """Test Appointment Scheduling features"""
    
    # View today's appointments
    response = requests.get(f"{BASE_URL}/appointments/today/overview")
    if response.status_code == 200:
        overview = response.json()
        print(f"✅ Today's Overview:")
        print(f"   - Total appointments: {overview['total']}")
        print(f"   - Scheduled: {overview['scheduled']}")
        print(f"   - Confirmed: {overview['confirmed']}")
        print(f"   - In Progress: {overview['in_progress']}")
        print(f"   - Completed: {overview['completed']}")
    
    # Get appointments by date range
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    response = requests.get(f"{BASE_URL}/appointments/", params={
        'start_date': tomorrow.strftime('%Y-%m-%d'),
        'end_date': day_after.strftime('%Y-%m-%d')
    })
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Appointments by date range: Found {data['total']} appointments")
        for apt in data['items'][:3]:  # Show first 3
            print(f"   - {apt['appointment_date'][:16]} - Patient {apt['patient_id']} with Dr. (ID: {apt['provider_id']})")
    
    # Book new appointment
    new_appointment = {
        "patient_id": 3,
        "provider_id": 1,
        "appointment_date": (datetime.now() + timedelta(days=2)).replace(hour=14, minute=30).isoformat(),
        "duration_minutes": 45,
        "appointment_type": "follow_up",
        "status": "scheduled",
        "reason_for_visit": "Follow-up consultation",
        "chief_complaint": "Progress check"
    }
    response = requests.post(f"{BASE_URL}/appointments/", json=new_appointment)
    if response.status_code == 201:
        appointment = response.json()
        print(f"✅ New appointment booked: ID {appointment['id']} for {appointment['appointment_date'][:16]}")
    
    # Get provider schedules
    response = requests.get(f"{BASE_URL}/providers/", params={'per_page': 5})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Provider availability: {data['total']} providers available")
        for provider in data['items']:
            print(f"   - {provider['full_name']} ({provider['specialties'][0] if provider['specialties'] else 'General'})")

def clinical_operations():
    """Test Clinical Operations features"""
    
    # Get clinical records (if any)
    response = requests.get(f"{BASE_URL}/clinical-records/", params={'patient_id': 1})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Clinical records: Found {data['total']} records")
    else:
        print(f"ℹ️ Clinical records endpoint: {response.status_code}")
    
    # Create a simple clinical record
    clinical_record = {
        "patient_id": 1,
        "provider_id": 1,
        "record_date": datetime.now().isoformat(),
        "record_type": "visit_note",
        "chief_complaint": "Routine checkup",
        "vital_signs": {
            "temperature": 98.6,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "weight": 150.0
        },
        "assessment_and_plan": "Patient appears healthy. Continue regular monitoring."
    }
    response = requests.post(f"{BASE_URL}/clinical-records/", json=clinical_record)
    if response.status_code == 201:
        record = response.json()
        print(f"✅ Clinical record created: ID {record['id']} ({record['record_type']})")
    else:
        print(f"ℹ️ Clinical record creation: {response.status_code} - {response.text[:100]}")

def billing_administrative():
    """Test Billing & Administrative features"""
    
    # Get insurance records
    response = requests.get(f"{BASE_URL}/insurance/", params={'patient_id': 1})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Insurance records: Found {data['total']} insurance policies")
        for insurance in data['items'][:2]:
            print(f"   - {insurance['insurance_company']} (Policy: {insurance['policy_number']})")
    else:
        print(f"ℹ️ Insurance records: {response.status_code}")
    
    # Get billing information (if any)
    response = requests.get(f"{BASE_URL}/billing/", params={'patient_id': 1})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Billing records: Found {data['total']} billing entries")
    else:
        print(f"ℹ️ Billing records endpoint: {response.status_code}")

def api_overview():
    """Show API endpoints overview"""
    print("📋 Available API Endpoints:")
    print("   - GET  /patients/ - Search and list patients")
    print("   - GET  /patients/{id} - Get patient details") 
    print("   - POST /patients/ - Create new patient")
    print("   - GET  /appointments/ - List appointments with filters")
    print("   - POST /appointments/ - Book new appointment")
    print("   - GET  /appointments/today/overview - Today's overview")
    print("   - GET  /providers/ - List healthcare providers")
    print("   - GET  /clinical-records/ - Patient clinical records")
    print("   - POST /clinical-records/ - Add clinical notes")
    print("   - GET  /insurance/ - Insurance information")
    print("   - GET  /billing/ - Billing and payment data")
    print("\n   📖 Full API Documentation: http://localhost:8000/docs")

def main():
    """Run all feature tests"""
    print("🏥 EHR Dashboard - Feature Testing")
    print("=" * 40)
    
    # Check API connectivity
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            print("✅ Backend API is running and accessible")
        else:
            print("❌ Backend API is not responding correctly")
            return
    except:
        print("❌ Cannot connect to backend API. Make sure it's running on port 8000")
        return
    
    # Test each feature category
    test_feature("Patient Management", patient_management)
    test_feature("Appointment Scheduling", appointment_scheduling)  
    test_feature("Clinical Operations", clinical_operations)
    test_feature("Billing & Administrative", billing_administrative)
    test_feature("API Overview", api_overview)
    
    print(f"\n🎉 Feature testing completed!")
    print(f"🌐 Access the application:")
    print(f"   - Frontend: http://localhost:3000")
    print(f"   - API Docs: http://localhost:8000/docs")
    print(f"   - Backend: http://localhost:8000")

if __name__ == "__main__":
    main()