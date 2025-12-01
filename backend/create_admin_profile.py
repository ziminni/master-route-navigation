import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.Users.models import BaseUser, StudentProfile
from apps.Academics.models import Program

# Get admin user
admin = BaseUser.objects.get(username='admin')
print(f'Admin BaseUser ID: {admin.id}')

# Check if StudentProfile already exists
if hasattr(admin, 'student_profile'):
    print('Admin already has StudentProfile')
else:
    # Get a default program (or None)
    default_program = Program.objects.first()
    
    # Create StudentProfile for admin
    student_profile = StudentProfile.objects.create(
        user=admin,
        program=default_program,
        year_level=0,  # or appropriate value
        student_id_number='ADMIN-001'  # or appropriate ID
    )
    print(f'Created StudentProfile ID={student_profile.id} for admin')
    print(f'Admin can now be used in updated_by field')
