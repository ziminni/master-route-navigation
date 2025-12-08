import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.Users.models import BaseUser, StudentProfile

admin = BaseUser.objects.get(username='admin')
print(f'Admin BaseUser ID: {admin.id}')
print(f'Has student_profile attr: {hasattr(admin, "student_profile")}')

try:
    if hasattr(admin, 'student_profile'):
        print(f'Admin StudentProfile ID: {admin.student_profile.id}')
    else:
        print('Admin has NO StudentProfile')
except:
    print('Admin has NO StudentProfile (exception)')

# Check all students
students = StudentProfile.objects.all()
print(f'\nTotal StudentProfiles: {students.count()}')
for s in students[:5]:
    print(f'  StudentProfile ID={s.id}, BaseUser ID={s.user.id}, Username={s.user.username}')
