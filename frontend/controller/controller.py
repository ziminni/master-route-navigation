import requests

API_BASE_URL = "http://127.0.0.1:8000/api/appointment/"

def plot_schedule(faculty_id, time_slots):
    url = f"{API_BASE_URL}plot_schedule/"
    payload = {
        "faculty_id": faculty_id,
        "time_slots": time_slots
    }
    response = requests.post(url, json=payload)
    print(response.json())

# Example usage
# plot_schedule(1, [
#     {"start": "08:00", "end": "10:00", "day": "Monday"},
#     {"start": "13:00", "end": "15:00", "day": "Wednesday"}
# ])


def get_faculty_block(faculty_id):
    url = f"{API_BASE_URL}retrieve_block/{faculty_id}/"
    response = requests.get(url)
    print(response.json())

# Example
# get_faculty_block(1)

def get_block_entries(block_id):
    url = f"{API_BASE_URL}entries/{block_id}/"
    response = requests.get(url)
    print(response.json())

# Example
# get_block_entries(2)

def check_availability(schedule_entry_id, date):
    url = f"{API_BASE_URL}check_availability/{schedule_entry_id}/{date}/"
    response = requests.get(url)
    print(response.json())

# Example
# check_availability(5, "2025-10-06")


def get_student_appointments(student_id):
    url = f"{API_BASE_URL}student_appointments/{student_id}/"
    response = requests.get(url)
    print(response.json())

# Example
# get_student_appointments(10)

def get_faculty_appointments(faculty_id):
    url = f"{API_BASE_URL}faculty_appointments/{faculty_id}/"
    response = requests.get(url)
    print(response.json())

# Example
# get_faculty_appointments(3)

def update_appointment(appointment_id, data):
    url = f"{API_BASE_URL}update_appointment/{appointment_id}/"
    response = requests.put(url, json=data)
    print(response.json())

# Example: Faculty accepts
# update_appointment(15, {"status": "Accepted"})

# # Example: Student cancels
# update_appointment(15, {"status": "Canceled"})

# # Example: Reschedule
# update_appointment(15, {
#     "status": "Rescheduled",
#     "appointment_date": "2025-10-07"
# })


def create_appointment(student_id, schedule_entry_id, date, reason):
    url = f"{API_BASE_URL}create_appointment/"
    payload = {
        "student_id": student_id,
        "appointment_schedule_entry": schedule_entry_id,
        "appointment_date": date,
        "reason": reason
    }
    response = requests.post(url, json=payload)
    print(response.json())

# Example
# create_appointment(10, 4, "2025-10-08", "Consultation about thesis")






