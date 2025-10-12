from datetime import datetime
from .crud import JSONCRUD 

class appointment_crud:
    def __init__(self):
        self.faculty_db = JSONCRUD('faculty.json')
        self.student_db = JSONCRUD('student.json')
        self.blocks_db = JSONCRUD('appointment_blocks.json')
        self.entries_db = JSONCRUD('appointment_entries.json')
        self.appointments_db = JSONCRUD('appointments.json')

    # ===========================
    # FACULTY MANAGEMENT
    # ===========================
    def create_faculty(self, name, email, department):
        """Add a new faculty member."""
        faculty_num = len(self.list_faculty())
        return self.faculty_db.create({
            "id": faculty_num + 1,
            "name": name,
            "email": email,
            "department": department
        })

    def list_faculty(self):
        """Return all faculty records."""
        return self.faculty_db.read_all()

    # ===========================
    # STUDENT MANAGEMENT
    # ===========================
    def create_student(self, name, email, course, year_level):
        """Add a new student."""
        student_num = len(self.list_students())
        return self.student_db.create({
            "id": student_num + 1,
            "name": name,
            "email": email,
            "course": course,
            "year_level": year_level
        })

    def list_students(self):
        """Return all student records."""
        return self.student_db.read_all()

    # ===========================
    # SCHEDULE BLOCK AND ENTRIES
    # ===========================
    def plot_schedule(self, faculty_id, time_slots):
        """
        Simulates PlottingScheduleAPIView (POST)
        Faculty creates a new block of available schedule + entries.
        """
        # Step 1: Mark previous blocks as unavailable
        all_blocks = self.blocks_db.read_all()
        for block in all_blocks:
            if block["faculty_id"] == faculty_id and block["is_available"]:
                block["is_available"] = False
        self.blocks_db._write_data(all_blocks)

        # Step 2: Create new available block
        block = self.blocks_db.create({
            "faculty_id": faculty_id,
            "is_available": True
        })

        # Step 3: Add time slot entries
        created_entries = []
        for slot in time_slots:
            entry = self.entries_db.create({
                "schedule_block_entry_id": block["id"],
                "start_time": slot["start"],
                "end_time": slot["end"],
                "day_of_week": slot["day"]
            })
            created_entries.append(entry)

        return {
            "message": "Schedule created successfully",
            "block": block,
            "entries": created_entries
        }

    # ===========================
    # RETRIEVE ACTIVE BLOCK
    # ===========================
    def get_active_block(self, faculty_id):
        """Get the active (available) schedule block for a specific faculty."""
        blocks = self.blocks_db.read_all()
        for block in blocks:
            if block["faculty_id"] == faculty_id and block["is_available"]:
                return block
        return {"error": "No available schedule block found for this faculty"}

    # ===========================
    # RETRIEVE BLOCK ENTRIES
    # ===========================
    def get_block_entries(self, block_id):
        """List all time slot entries in a specific block."""
        return self.entries_db.read_by_field("schedule_block_entry_id", block_id)
    
    # ===========================
    # APPOINTMENTS BY ENTRY AND DATE
    # ===========================
    def get_appointments_by_entry_and_date(self, schedule_entry_id, date_str):
        """Get all appointments matching entry and date."""
        appointments = self.appointments_db.read_all()
        # print(f"{schedule_entry_id} {date_str}")
        return [
            a for a in appointments
            if a["appointment_schedule_entry_id"] == schedule_entry_id
            and a["appointment_date"] == date_str
            and a["status"] in ["completed", "approved"]
        ]

    # ===========================
    # STUDENT APPOINTMENTS
    # ===========================
    def get_student_appointments(self, student_id):
        """List all appointments of a specific student."""
        return self.appointments_db.read_by_field("student_id", student_id)

    # ===========================
    # FACULTY APPOINTMENTS
    # ===========================
    def get_faculty_appointments(self, faculty_id):
        """List all appointments of a specific faculty."""
        appointments = self.appointments_db.read_all()
        entries = self.entries_db.read_all()
        blocks = self.blocks_db.read_all()

        faculty_entries = [
            e["id"]
            for e in entries
            for b in blocks
            if e["schedule_block_entry_id"] == b["id"] and b["faculty_id"] == faculty_id
        ]

        return [
            a for a in appointments
            if a["schedule_block_entry_id"] in faculty_entries
        ]

    # ===========================
    # UPDATE APPOINTMENT
    # ===========================
    def update_appointment(self, appointment_id, updates):
        """Simulates UpdateAppointmentAPIView (PUT/PATCH)."""
        valid_statuses = ["pending", "approved", "canceled", "denied"]
        if "status" in updates and updates["status"] not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        updates["updated_at"] = str(datetime.now())
        return self.appointments_db.update(appointment_id, updates)

    # ===========================
    # CREATE APPOINTMENT
    # ===========================
    def create_appointment(self, student_id, schedule_entry_id, details, address, date_str, image_path):
        """Simulates CreateAppointmentAPIView (POST)."""
        return self.appointments_db.create({
            "student_id": student_id,
            "appointment_schedule_entry_id": schedule_entry_id,
            "additional_details": details,
            "address": address,
            "status": "pending",
            "appointment_date": date_str,
            "created_at": str(datetime.now()),
            "updated_at": str(datetime.now()),
            "image_path": image_path
        })

# ===========================
# SAMPLE USAGE
# ===========================
if __name__ == "__main__":
    appointment_crud = appointment_crud()
    
    # --- Create sample faculty and student ---
    # faculty = appointment_crud.create_faculty("Kim", "Kim@school.edu", "IT Department")
    # student = appointment_crud.create_student("Alice Santos", "alice@student.edu", "BSIT", 3)
    # student1 = appointment_crud.create_student("Badong Lee", "badong@student.edu", "BSIT", 3)

    # print("All Faculty:\n", appointment_crud.list_faculty())
    # print("All Students:\n", appointment_crud.list_students())

    # # --- Faculty plots a schedule ---
    # result = appointment_crud.plot_schedule(
    #     faculty_id=faculty["id"],
    #     time_slots=[
    #         {"start": "09:00", "end": "10:00", "day": "Monday"},
    #         {"start": "10:00", "end": "11:00", "day": "Monday"}
    #     ]
    # )
    # print("\nSchedule plotted:", result)

    # # --- Student books an appointment ---
    # # new_appointment = appointment_crud.create_appointment(
    # #     student_id=student["id"],
    # #     schedule_entry_id=result["entries"][0]["id"],
    # #     details="Consultation about project",
    # #     address="Room 305",
    # #     date_str="2025-10-08",
    # #     image_path="Uploads/consultation.png"
    # # )
    # # print("\nNew Appointment Created:", new_appointment)

    # # --- Faculty views their appointments ---
    # faculty_appts = appointment_crud.get_faculty_appointments(faculty["id"])
    # print("\nFaculty Appointments:", faculty_appts)

    # # --- Student views their appointments ---
    # student_appts = appointment_crud.get_student_appointments(student["id"])
    # print("\nStudent Appointments:", student_appts)

    # --- Update appointment status ---
    # updated = appointment_crud.update_appointment(new_appointment["id"], {"status": "approved"})
    # print("\nUpdated Appointment:", updated)