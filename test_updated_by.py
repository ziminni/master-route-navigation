"""
Test script to verify updated_by field is properly saved
Run this from the backend directory:
cd backend && python ../test_updated_by.py
"""
import os
import sys
import django

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.Organizations.models import OfficerTerm, OrganizationMembers, Positions, Organization
from apps.Users.models import StudentProfile

def test_updated_by():
    print("=" * 60)
    print("Testing updated_by field in OfficerTerm")
    print("=" * 60)
    
    # Get a sample officer term
    officer_term = OfficerTerm.objects.first()
    
    if officer_term:
        print(f"\nSample OfficerTerm:")
        print(f"  ID: {officer_term.id}")
        print(f"  Member: {officer_term.member.user_id.user.get_full_name()}")
        print(f"  Position: {officer_term.position.name}")
        print(f"  Start Term: {officer_term.start_term}")
        print(f"  End Term: {officer_term.end_term}")
        print(f"  Status: {officer_term.status}")
        print(f"  Updated By: {officer_term.updated_by.user.get_full_name() if officer_term.updated_by else 'NULL'}")
        print(f"  Updated At: {officer_term.updated_at}")
        
        if officer_term.updated_by is None:
            print("\n⚠️  WARNING: updated_by is NULL!")
            print("This means the audit trail is incomplete.")
        else:
            print("\n✅ updated_by is properly set!")
    else:
        print("\n⚠️  No OfficerTerm records found in database")
    
    # Check all officer terms
    print(f"\n\nChecking all {OfficerTerm.objects.count()} OfficerTerm records...")
    null_count = OfficerTerm.objects.filter(updated_by__isnull=True).count()
    non_null_count = OfficerTerm.objects.filter(updated_by__isnull=False).count()
    
    print(f"  Records with updated_by NULL: {null_count}")
    print(f"  Records with updated_by set: {non_null_count}")
    
    if null_count > 0:
        print(f"\n⚠️  {null_count} records have NULL updated_by field")
        print("These records were likely created before the updated_by field was implemented")
        print("or were created without passing the updated_by_id parameter.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_updated_by()
