# utils/initializer.py
# Handles fetching data from DB to JSON

"""
Navigation Data Initializer
Handles fetching navigation data from database and exporting to JSON format.

This module is responsible for:
1. Reading the complete navigation structure from the database
2. Building a hierarchical JSON structure (Parents → Mains → Modulars)
3. Exporting the navigation data to JSON files for use by the frontend

The exported JSON follows this structure:
{
    "parents": [
        {
            "id": 1,
            "name": "Parent Category",
            "mains": [
                {
                    "id": 1,
                    "name": "Main Page",
                    "function": "page_function_name",
                    "access": "access_level",
                    "modulars": [
                        {
                            "id": 1,
                            "name": "Sub Page",
                            "function": "sub_function_name"
                        }
                    ]
                }
            ]
        }
    ]
}
"""
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.navbar_db_connect import get_connection, close_connection
from database.navbar_setup import init_db, insert_sample_data
from utils.db_helper import reload_navigation_data

def export_to_json(filename="navbar.json"):
    """
    Fetch navigation data from database and export to JSON file.

    This function reads the complete navigation hierarchy from the database
    and creates a nested JSON structure that represents:
    - Parent categories (top-level navigation)
    - Main pages (under each parent)
    - Modular pages (under each main page)

    Args:
        filename (str): Name of the JSON file to create (default: "navbar.json")

    The function builds the data in this order:
    1. Get all parent categories
    2. For each parent, get its main pages
    3. For each main page, get its modular sub-pages
    4. Export everything as a hierarchical JSON structure
    """
    conn = get_connection()
    if not conn:
        print("Failed to connect to database, aborting export.")
        return

    c = conn.cursor()
    data = {"parents": []}

    try:
        # Parents: Get all Parent categories (top-level navigation)
        c.execute("SELECT id, parent_name FROM ParentNavbar ORDER BY id")
        parents = c.fetchall()

        for parent_id, parent_name in parents:
            parent_entry = {"id": parent_id, "name": parent_name, "mains": []}

            # Mains: Get all Main pages for this parent
            c.execute("""
                SELECT id, page_name, page_function, access_level
                FROM MainNavbar WHERE parent_id=? ORDER BY id
            """, (parent_id,))
            mains = c.fetchall()

            for mid, pname, pfunc, access in mains:
                main_entry = {
                    "id": mid,
                    "name": pname,
                    "function": pfunc,
                    "access": access,
                    "modulars": []
                }

                # Modulars: Get all Modular pages for this main page
                c.execute("""
                    SELECT id, page_name, page_function
                    FROM ModularNavbar WHERE main_id=? ORDER BY id
                """, (mid,))
                modulars = c.fetchall()

                # Add each modular page to the main entry
                for mod_id, mname, mfunc in modulars:
                    main_entry["modulars"].append({
                        "id": mod_id,
                        "name": mname,
                        "function": mfunc
                    })
                # Add this main page to the parent
                parent_entry["mains"].append(main_entry)
            # Add this parent to the main data structure
            data["parents"].append(parent_entry)

        # Export to JSON file with error handling
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Exported DB → {filename}")
            # Sync with db_helper.py cache
            reload_navigation_data()
        except IOError as e:
            print(f"Error writing JSON file {filename}: {e}")

    except sqlite3.Error as e:
        print(f"Database error during export: {e}")
    finally:
        close_connection(conn)

if __name__ == "__main__":
    """
    Main execution flow:
    1. Initialize database tables
    2. Insert sample data if needed
    3. Export navigation structure to JSON

    This creates a complete navigation system setup.
    """
    init_db()
    conn = get_connection()
    if conn:
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM ParentNavbar")
            if c.fetchone()[0] == 0:
                insert_sample_data()
            export_to_json()
        except sqlite3.Error as e:
            print(f"Error in initialization: {e}")
        finally:
            close_connection(conn)