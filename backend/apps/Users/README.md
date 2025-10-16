Implementation of Sub-roles
1. Created a user (example: staff)
2. Login as admin (admin, admin123)
3. Change role of staff user via promote/demote logic using admin panel(same as other user types, just recycled the code)
    - So Staff can be promoted to Registrar but does really not include a new Model, just custom permissions

Update to setup
1. initalize virtual environment
2. in backend directory:
    python makemigrations
    python migrate
    python script.py
    python manage.py runserver

3. Open new terminal:
    in frontend:
        python main.py

Additions:
    Script file
        - Serves as a seeder
        - Default users with default roles
        - Usable Usernames: Adolf, Kim, Donald, admin
        - And passwords: admin123 and password123
    
    Admin dashboard
        - table to show all users
        - options to promote/demote users, soon to be filtered(conditions in promoting)

Inquiries:
    1. Is the implementation correct?
    2. Is the promote/demote methods logical?
    3. Should the features below be implemented?

Future Development:
    - Role based feature authenticator
    - Or Permission based?