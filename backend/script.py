# Script for manual role manipulation and initial setup
# This script will:
# 1. Create virtual environment
# 2. Install dependencies
# 3. Run migrations
# 4. Create default users
import os
import sys
import subprocess
from pathlib import Path

# Get the project root directory (one level up from backend/)
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

def run_command(command, description, shell=True, check=True, use_backend_dir=False):
    """Run a shell command and print status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {command}\n")
    
    # Determine working directory
    if use_backend_dir:
        work_dir = str(BACKEND_DIR)
    else:
        work_dir = str(PROJECT_ROOT)
    
    print(f"Working directory: {work_dir}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            text=True,
            cwd=work_dir
        )
        print(f"✓ {description} completed successfully!")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during: {description}")
        print(f"Error: {e}")
        if not check:
            return None
        raise

def cleanup_database():
    """Clean up database and migrations before setup."""
    print(f"\n{'='*60}")
    print("CLEANUP: Removing old database and migrations")
    print(f"{'='*60}\n")
    
    # Delete db.sqlite3
    db_file = BACKEND_DIR / "db.sqlite3"
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"✓ Deleted: {db_file}")
        except Exception as e:
            print(f"✗ Error deleting {db_file}: {e}")
    else:
        print(f"- {db_file} does not exist (skipping)")
    
    # Delete Users app migrations (except __init__.py)
    users_migrations_dir = BACKEND_DIR / "apps" / "Users" / "migrations"
    if users_migrations_dir.exists():
        for migration_file in users_migrations_dir.glob("*.py"):
            # Keep __init__.py, delete everything else
            if migration_file.name != "__init__.py":
                try:
                    migration_file.unlink()
                    print(f"✓ Deleted: {migration_file}")
                except Exception as e:
                    print(f"✗ Error deleting {migration_file}: {e}")
        
        # Also delete __pycache__ in migrations folder
        pycache_dir = users_migrations_dir / "__pycache__"
        if pycache_dir.exists():
            try:
                import shutil
                shutil.rmtree(pycache_dir)
                print(f"✓ Deleted: {pycache_dir}")
            except Exception as e:
                print(f"✗ Error deleting {pycache_dir}: {e}")
    else:
        print(f"- {users_migrations_dir} does not exist (skipping)")
    
    print(f"\n{'='*60}")
    print("Cleanup completed!")
    print(f"{'='*60}\n")

def setup_environment():
    """Set up virtual environment and dependencies."""
    
    # Step 1: Create virtual environment
    if not VENV_DIR.exists():
        run_command(
            f"python.exe -m venv {VENV_DIR}",
            "Creating virtual environment",
        )
    else:
        print(f"\n{'='*60}")
        print("Virtual environment already exists, skipping creation...")
        print(f"{'='*60}")
    
    # Step 2: Determine pip path
    if sys.platform == "win32":
        pip_path = VENV_DIR / "Scripts" / "pip.exe"
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
        python_path = VENV_DIR / "bin" / "python"
    
    # Step 3: Install requirements
    if REQUIREMENTS_FILE.exists():
        run_command(
            f'"{pip_path}" install -r "{REQUIREMENTS_FILE}"',
            "Installing requirements",
        )
    else:
        print(f"Warning: requirements.txt not found at {REQUIREMENTS_FILE}")
    
    # Step 4: Run makemigrations (needs to run from backend directory)
    run_command(
        f'"{python_path}" manage.py makemigrations',
        "Running makemigrations",
        use_backend_dir=True
    )
    
    # Step 5: Run migrate (needs to run from backend directory)
    run_command(
        f'"{python_path}" manage.py migrate',
        "Running migrations",
        use_backend_dir=True
    )
    
    print(f"\n{'='*60}")
    print("Environment setup completed!")
    print(f"{'='*60}\n")

# Run setup if this is the main script
if __name__ == "__main__":
    print("\n" + "="*60)
    print("DJANGO PROJECT SETUP AND USER CREATION SCRIPT")
    print("="*60)
    
    # Check if we're running in the virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("\n" + "="*60)
        print("PHASE 1: Environment Setup")
        print("="*60)
        
        # Clean up old database and migrations first
        cleanup_database()
        
        # Run setup commands
        setup_environment()
        
        # Now re-run this script using the virtual environment's Python
        print(f"\n{'='*60}")
        print("PHASE 2: Launching script in virtual environment...")
        print(f"{'='*60}\n")
        
        if sys.platform == "win32":
            venv_python = VENV_DIR / "Scripts" / "python.exe"
        else:
            venv_python = VENV_DIR / "bin" / "python"
        
        # Re-run this script with the venv Python
        subprocess.run([str(venv_python), __file__], check=True)
        sys.exit(0)
    
    # If we're here, we're in the virtual environment
    print("\n" + "="*60)
    print("Running in virtual environment - Setting up Django...")
    print("="*60 + "\n")

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.Users.models import Program, Section, StudentProfile, StaffProfile, FacultyProfile, FacultyDepartment, Position
User = get_user_model()
import requests
from datetime import date

# Get a user
def get_user(identifier):
    # Fetch user by id, username, or email.
    # Returns User instance or None.
    if isinstance(identifier, int):
        return User.objects.filter(pk=identifier).first()
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()
    return User.objects.filter(username__iexact=identifier).first() 
def assign_role(identifier, new_role):
    """Since roles are defaulted to student upon creation, use this method to change it.
    identifier - username
    new_role - new role to assign (e.g. admin, faculty)"""
    # Get user
    u = User.objects.get(username=identifier)
    # # Remove a role
    u.groups.remove(Group.objects.get(name="student"))
    # # Assign a role
    u.groups.add(Group.objects.get(name=new_role))

def create_users():
    """Create all default users."""
    print(f"\n{'='*60}")
    print("CREATING DEFAULT USERS")
    print(f"{'='*60}\n")
    
    #==============================Start of User Creation==============================
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@cmu.edu.ph",
            password="admin123",
            institutional_id="ADM-0001",
            role_type="admin"
        )
        assign_role("admin","admin")
        print("Admin superuser created")
    else:
        print("Admin already exists")
    if not User.objects.filter(username="Adolf").exists():
        user1 = User.objects.create_user(
            username="Marcus",
            email="immarcusmercer@gmail.com",
            password="password123",
            first_name="Marcus",
            last_name="Mercer",
            institutional_id="456456456",
            role_type="student",
        )
        assign_role("Marcus", "student")

        #DEfault program and section, for example rani
        prog, _ = Program.objects.get_or_create(program_name="BS IT")
        sec, _  = Section.objects.get_or_create(section_name="IT-1A")
        #then create a student profile
        sp1 = StudentProfile.objects.create(
            user=user1,
            program=prog,
            section=sec,
            year_level=1,
            indiv_points=0,
        )
        print(f"Account {user1.get_username()} created")
    else:
        print("Account already exists. Aborting creation...")

        
    # Default Positions
    pos1, _ = Position.objects.get_or_create(position_name="Instructor 1")
    #Default Department
    dep1, _ = FacultyDepartment.objects.get_or_create(department_name="CISC")
    if not User.objects.filter(username="Donald").exists():
        user2 = User.objects.create_user(
            username="Donald",
            email="donaldtrump@cmu.edu.ph",
            password="password123",
            first_name="Donald",
            last_name="Trump",
            institutional_id="123123123",
            role_type="staff",
        )
        assign_role("Donald", "staff")

        # Create Staff(Registrar)
        staff1= StaffProfile.objects.create(
            user=user2,
            faculty_department=dep1,
            job_title="registrar"
        )
        print(f"Account {user2.get_username()} created")
    else:
        print("Account already exists. Aborting creation...")
        
    if not User.objects.filter(username="Kim").exists():
        user3 = User.objects.create_user(
            username="Kim",
            email="kimjongun@cmu.edu.ph",
            password="password123",
            first_name="Kim",
            last_name="Jong Un",
            institutional_id="789789789",
            role_type="faculty",
        )
        assign_role("Kim", "faculty")
        # Create faculty(Instructor 1)
        Fac1= FacultyProfile.objects.create(
            user=user3,
            faculty_department=dep1,
            position= pos1,
            hire_date= date(2001, 9,11),
        )
        print(f"Account {user3.get_username()} created")
    else:
        print("Account already exists. Aborting creation...")

    # Verify creation
    for ident in ("admin","Marcus", "Donald", "Kim"):
        u = get_user(ident)
        if u:
            print(f"Verified creation for Username: {u.get_username()} ID: {u.id}")
        else:
            print(f"User {ident} not found")
    #==============================End of User Creation==============================

# Call the user creation function if running as main script
if __name__ == "__main__":
    create_users()
    
    print("\n" + "="*60)
    print("SCRIPT COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nYou can now run: python manage.py runserver")
    print("="*60 + "\n")

# list(u.groups.values_list("name", flat=True))


# u = User.objects.get(username="Janmarc")

# # Assign a role
# u.groups.add(Group.objects.get(name="staff"))

# # Remove a role
# u.groups.remove(Group.objects.get(name="student"))

# # See roles
# list(u.groups.values_list("name", flat=True))

# Script for managing groups
# from django.contrib.auth.models import Group
# from apps.Users.models import Program, Section, StudentProfile
# Group.objects.get_or_create(name="org_officer")


# # Creation + promotion/demotion
# user = User.objects.create_user(
#     username="Adolf",
#     email="adolfhitler@cmu.edu.ph",
#     password="password123",
#     first_name="Adolf",
#     last_name="Hitler",
#     institutional_id="123123123",
#     role_type="student",
# )

# prog, _ = Program.objects.get_or_create(program_name="BS IT")
# sec, _  = Section.objects.get_or_create(section_name="IT-1A")

# sp = StudentProfile.objects.create(
#     user=user,
#     program=prog,
#     section=sec,
#     year_level=1,
#     indiv_points=0,
# )

# Methods (for shell, method is in views.py)

# def grant_org_officer(user):
#     group, _ = Group.objects.get_or_create(name="org_officer")
#     user.groups.add(group)\
    
# def revoke_org_officer(user):
#     group, _ = Group.objects.get_or_create(name="org_officer")
#     user.groups.remove(group)

# Check roles
# user.groups.values_list("name", flat=True)



# In-script methods only, already created api-callable methods from Users/view
# def promote_officer(self, user_id, token):
#     url = f"http://127.0.0.1:8000/api/roles/org-officer/{user_id}/promote/"
#     headers = {"Authorization": f"Bearer {token}"}
#     resp = requests.post(url, headers=headers, timeout=10)
#     return resp.json()

# def demote_officer(self, user_id, token):
#     url = f"http://127.0.0.1:8000/api/roles/org-officer/{user_id}/demote/"
#     headers = {"Authorization": f"Bearer {token}"}
#     resp = requests.post(url, headers=headers, timeout=10)
#     return resp.json()