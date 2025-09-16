#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def add_test_appointments():
    tomorrow = datetime.now() + timedelta(days=1)
    
    appointments = [
        {
            "patient_id": 1,
            "provider_id": 1,
            "appointment_date": tomorrow.replace(hour=10, minute=0).isoformat(),
            "duration_minutes": 30,
            "appointment_type": "consultation",
            "status": "scheduled",
            "reason_for_visit": "Annual physical exam",
            "chief_complaint": "Routine checkup"
        },
        {
            "patient_id": 2,
            "provider_id": 1,
            "appointment_date": tomorrow.replace(hour=11, minute=0).isoformat(),
            "duration_minutes": 45,
            "appointment_type": "follow_up",
            "status": "confirmed",
            "reason_for_visit": "Blood pressure follow-up",
            "chief_complaint": "Hypertension management"
        },
        {
            "patient_id": 3,
            "provider_id": 1,
            "appointment_date": (tomorrow + timedelta(days=1)).replace(hour=9, minute=0).isoformat(),
            "duration_minutes": 60,
            "appointment_type": "physical_exam",
            "status": "scheduled",
            "reason_for_visit": "Preventive care visit",
            "chief_complaint": "Well visit"
        }
    ]
    
    for appointment_data in appointments:
        try:
            response = requests.post(f"{BASE_URL}/appointments/", json=appointment_data)
            if response.status_code == 201:
                appointment = response.json()
                print(f"✅ Added appointment: {appointment['appointment_date'][:16]} (ID: {appointment['id']})")
            else:
                print(f"❌ Failed to add appointment: {response.text}")
        except Exception as e:
            print(f"❌ Error adding appointment: {e}")

if __name__ == "__main__":
    add_test_appointments()