"""
Script to populate the Positions table with default positions
Run this once to initialize the positions in the database
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.Organizations.models import Positions

def populate_positions():
    """Populate the Positions table with default officer positions"""
    
    positions_data = [
        {"name": "President", "rank": 1, "description": "Head of the organization"},
        {"name": "Vice President - Internal", "rank": 2, "description": "Internal affairs officer"},
        {"name": "Vice President - External", "rank": 3, "description": "External affairs officer"},
        {"name": "Secretary", "rank": 4, "description": "Records and documentation officer"},
        {"name": "Treasurer", "rank": 5, "description": "Financial officer"},
        {"name": "Auditor", "rank": 6, "description": "Audits financial records"},
        {"name": "Public Relations Officer", "rank": 7, "description": "Handles public relations"},
        {"name": "Technical Officer", "rank": 8, "description": "Technical support and IT"},
        {"name": "Events Coordinator", "rank": 9, "description": "Organizes events and activities"},
        {"name": "Member", "rank": 100, "description": "Regular member (non-officer)"},
    ]
    
    created_count = 0
    updated_count = 0
    
    for pos_data in positions_data:
        position, created = Positions.objects.get_or_create(
            name=pos_data["name"],
            defaults={
                "rank": pos_data["rank"],
                "description": pos_data["description"]
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {position.name} (Rank: {position.rank})")
        else:
            # Update rank and description if position already exists
            position.rank = pos_data["rank"]
            position.description = pos_data["description"]
            position.save()
            updated_count += 1
            print(f"↻ Updated: {position.name} (Rank: {position.rank})")
    
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Created: {created_count} positions")
    print(f"  Updated: {updated_count} positions")
    print(f"  Total: {Positions.objects.count()} positions in database")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("Populating Positions table...")
    print(f"{'='*50}\n")
    populate_positions()
    print("\n✓ Done!")
