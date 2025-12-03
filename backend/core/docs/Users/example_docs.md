# [Module#]_[ModuleName] Documentation

**Example Documentation Format**

Septmeber 8, 2025

Since subclassing BaseUsers like Student/Staff/Faculty to subUsers (Student_org_officer/Dean) is not a practical option:

Goal:
    -Implement organization approach
        - Create and Organization model that would map users to other roles (eg. Student_org_officer)
        - Enable users to have multiple sub-roles (Student ->committee, org_officer, chairperson etc.)

Files Involved:
    - Users/models.py
    - Serializers
    - views.py

walkthrough:
    - Still error, but almost finished
    - Keeps returning HTTP 500 Error