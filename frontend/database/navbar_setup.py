# utils/database_setup.py
# Database schema creation and sample data insertion
from navbar_db_connect import get_connection, close_connection

def init_db():
    """
    Create all required database tables for the navigation system.
    
    Creates three tables with proper relationships:
    1. ParentNavbar - Top-level navigation categories
    2. MainNavbar - Main pages linked to parent categories
    3. ModularNavbar - Sub-pages linked to main pages
    
    This function is safe to run multiple times (uses 'IF NOT EXISTS').
    """
    conn = get_connection()
    c = conn.cursor()

    # Parent Navbar
    c.execute("""
        CREATE TABLE IF NOT EXISTS ParentNavbar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_name TEXT NOT NULL
        )
    """)

    # Main Navbar
    c.execute("""
        CREATE TABLE IF NOT EXISTS MainNavbar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT NOT NULL,
            page_function TEXT NOT NULL,
            access_level TEXT,
            parent_id INTEGER,
            FOREIGN KEY(parent_id) REFERENCES ParentNavbar(id)
        )
    """)

    # Modular Navbar
    c.execute("""
        CREATE TABLE IF NOT EXISTS ModularNavbar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT NOT NULL,
            page_function TEXT NOT NULL,
            main_id INTEGER,
            FOREIGN KEY(main_id) REFERENCES MainNavbar(id)
        )
    """)

    conn.commit()
    close_connection(conn)
    print("Tables created successfully")


def insert_sample_data():
    """
    Insert sample navigation data into the database for testing and demonstration.
    
    This creates a basic navigation structure:
    - Academics (parent)
        - Classes (main, student access)
        - Schedule (main, student access)
        - Progress (main, student access)
        - Appointments (main, student access)
    - Organizations (parent)
        - Browse (main, student access)
        - Membership (main, student access)
        - Events (main, student access)
    - Campus (parent)
        - Calendar (main, student access)
        - Announcements (main, student access)
        - House System (main, student access)
            - Overview (modular)
            - Events (modular)
            - Match History (modular)
            - Leaderboards (modular)
        - Showcase (main, student access)
    - Tools (parent)
        - Messages (main, student access)
        - Student Services (main, student access)
        - Help (main, student access)
    
    Note: This function checks for existing data and skips insertion if data already exists.
    """
    
    conn = get_connection()
    c = conn.cursor()

    # Avoid duplicate inserts
    c.execute("SELECT COUNT(*) FROM ParentNavbar")
    if c.fetchone()[0] > 0:
        print("Sample data already exists, skipping insert.")
        close_connection(conn)
        return

    # Parent Navs
    c.execute("INSERT INTO ParentNavbar (parent_name) VALUES (?)", ("Academics",))
    c.execute("INSERT INTO ParentNavbar (parent_name) VALUES (?)", ("Organizations",))
    c.execute("INSERT INTO ParentNavbar (parent_name) VALUES (?)", ("Campus",))
    c.execute("INSERT INTO ParentNavbar (parent_name) VALUES (?)", ("Tools",))

    # Main Navs
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Classes", "view_class_details", "student", 1))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Schedule", "view_schedule", "student", 1))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Progress", "track_progress", "student", 1))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Appointments", "schedule_meetings", "student", 1))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Browse", "browse_organizations", "student", 2))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Membership", "manage_membership", "student", 2))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Events", "view_events", "student", 2))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Calendar", "view_calendar", "student", 3))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Announcements", "view_announcements", "student", 3))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("House System", "manage_house_system", "student", 3))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Showcase", "view_showcase", "student", 3))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Messages", "send_receive_messages", "student", 4))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Student Services", "access_services", "student", 4))
    c.execute("INSERT INTO MainNavbar (page_name, page_function, access_level, parent_id) VALUES (?,?,?,?)",
            ("Help", "access_help", "student", 4))

    # Modular Navs
    c.execute("INSERT INTO ModularNavbar (page_name, page_function, main_id) VALUES (?,?,?)",
            ("Overview", "view_house_overview", 10))
    c.execute("INSERT INTO ModularNavbar (page_name, page_function, main_id) VALUES (?,?,?)",
            ("Events", "view_house_events", 10))
    c.execute("INSERT INTO ModularNavbar (page_name, page_function, main_id) VALUES (?,?,?)",
            ("Match History", "view_match_history", 10))
    c.execute("INSERT INTO ModularNavbar (page_name, page_function, main_id) VALUES (?,?,?)",
            ("Leaderboards", "view_leaderboards", 10))

    conn.commit()
    close_connection(conn)
    print("Sample data inserted successfully")