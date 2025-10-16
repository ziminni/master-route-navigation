"""
Role-based Routing Utility for Document Management System

This module provides utilities for routing users to appropriate dashboards
based on their roles and permissions.
"""

from typing import Optional, Callable, Dict, Any
from PyQt6.QtWidgets import QWidget


class RoleRouter:
    """
    Utility class for routing users to role-appropriate dashboards.
    
    This class handles the logic of determining which dashboard/view
    a user should see based on their role(s).
    
    Supports hierarchical roles with sub-roles:
    - Primary roles: admin, faculty, staff, student
    - Sub-roles: org_officer (student), dean (faculty), registrar (staff), etc.
    """
    
    # Primary role categories
    PRIMARY_ROLES = {
        'admin': 'admin',
        'faculty': 'faculty',
        'staff': 'staff',
        'student': 'student'
    }
    
    # Hierarchical role mapping: primary_role -> [list of sub-roles]
    ROLE_HIERARCHY = {
        'admin': ['admin', 'super_admin', 'administrator'],
        'faculty': ['faculty', 'dean', 'professor', 'instructor', 'teacher'],
        'staff': ['staff', 'registrar', 'hr', 'clerk', 'secretary'],
        'student': ['student', 'org_officer', 'officer', 'learner']
    }
    
    # Legacy role lists (kept for backward compatibility)
    ADMIN_ROLES = ROLE_HIERARCHY['admin']
    FACULTY_ROLES = ROLE_HIERARCHY['faculty']
    STAFF_ROLES = ROLE_HIERARCHY['staff']
    STUDENT_ROLES = ROLE_HIERARCHY['student']
    
    @staticmethod
    def is_admin(primary_role: str = None, roles: list = None) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            bool: True if user is admin
        """
        if primary_role and primary_role.lower() in RoleRouter.ADMIN_ROLES:
            return True
        
        if roles:
            return any(role.lower() in RoleRouter.ADMIN_ROLES for role in roles)
        
        return False
    
    @staticmethod
    def is_faculty(primary_role: str = None, roles: list = None) -> bool:
        """
        Check if user has faculty privileges.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            bool: True if user is faculty
        """
        if primary_role and primary_role.lower() in RoleRouter.FACULTY_ROLES:
            return True
        
        if roles:
            return any(role.lower() in RoleRouter.FACULTY_ROLES for role in roles)
        
        return False
    
    @staticmethod
    def is_staff(primary_role: str = None, roles: list = None) -> bool:
        """
        Check if user has staff privileges.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            bool: True if user is staff
        """
        if primary_role and primary_role.lower() in RoleRouter.STAFF_ROLES:
            return True
        
        if roles:
            return any(role.lower() in RoleRouter.STAFF_ROLES for role in roles)
        
        return False
    
    @staticmethod
    def is_student(primary_role: str = None, roles: list = None) -> bool:
        """
        Check if user has student role.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            bool: True if user is student
        """
        if primary_role and primary_role.lower() in RoleRouter.STUDENT_ROLES:
            return True
        
        if roles:
            return any(role.lower() in RoleRouter.STUDENT_ROLES for role in roles)
        
        return False
    
    @staticmethod
    def get_primary_role(primary_role: str = None, roles: list = None) -> str:
        """
        Get the primary role category from a role or sub-role.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            str: Primary role category ('admin', 'faculty', 'staff', 'student', 'guest')
        """
        # Check primary_role first
        if primary_role:
            role_lower = primary_role.lower()
            for primary, sub_roles in RoleRouter.ROLE_HIERARCHY.items():
                if role_lower in [r.lower() for r in sub_roles]:
                    return primary
        
        # Check roles list
        if roles:
            for role in roles:
                role_lower = role.lower()
                for primary, sub_roles in RoleRouter.ROLE_HIERARCHY.items():
                    if role_lower in [r.lower() for r in sub_roles]:
                        return primary
        
        return 'guest'
    
    @staticmethod
    def get_role_type(primary_role: str = None, roles: list = None) -> str:
        """
        Get the role type category (alias for get_primary_role for backward compatibility).
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            str: Role type ('admin', 'faculty', 'staff', 'student', 'guest')
        """
        return RoleRouter.get_primary_role(primary_role, roles)
    
    @staticmethod
    def get_sub_role(primary_role: str = None, roles: list = None) -> str:
        """
        Get the specific sub-role from the user's roles.
        
        Args:
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            str: The sub-role or primary role if found, None otherwise
            
        Example:
            # User with primary_role='dean' returns 'dean'
            # User with roles=['org_officer'] returns 'org_officer'
        """
        if primary_role:
            return primary_role.lower()
        
        if roles and len(roles) > 0:
            # Return the first recognized sub-role
            for role in roles:
                role_lower = role.lower()
                for sub_roles in RoleRouter.ROLE_HIERARCHY.values():
                    if role_lower in [r.lower() for r in sub_roles]:
                        return role_lower
        
        return None
    
    @staticmethod
    def has_sub_role(sub_role: str, primary_role: str = None, roles: list = None) -> bool:
        """
        Check if user has a specific sub-role.
        
        Args:
            sub_role (str): Sub-role to check for (e.g., 'dean', 'org_officer')
            primary_role (str): User's primary role
            roles (list): List of all user roles
            
        Returns:
            bool: True if user has the specified sub-role
            
        Example:
            if RoleRouter.has_sub_role('dean', primary_role, roles):
                # Dean-specific features
        """
        sub_role_lower = sub_role.lower()
        
        if primary_role and primary_role.lower() == sub_role_lower:
            return True
        
        if roles:
            return any(role.lower() == sub_role_lower for role in roles)
        
        return False
    
    @staticmethod
    def route_to_dashboard(username: str, roles: list, primary_role: str, token: str,
                          admin_dashboard: Callable = None,
                          faculty_dashboard: Callable = None,
                          staff_dashboard: Callable = None,
                          student_dashboard: Callable = None,
                          default_dashboard: Callable = None,
                          sub_role_dashboards: Dict[str, Callable] = None) -> Optional[QWidget]:
        """
        Route user to appropriate dashboard based on role and sub-role.
        
        Args:
            username (str): User's username
            roles (list): List of user roles
            primary_role (str): User's primary role
            token (str): Authentication token
            admin_dashboard (Callable): Function/class that returns admin dashboard widget
            faculty_dashboard (Callable): Function/class that returns faculty dashboard widget
            staff_dashboard (Callable): Function/class that returns staff dashboard widget
            student_dashboard (Callable): Function/class that returns student dashboard widget
            default_dashboard (Callable): Function/class that returns default dashboard widget
            sub_role_dashboards (dict): Optional dict mapping sub-roles to specific dashboards
                                       e.g., {'dean': DeanDash, 'org_officer': OrgOfficerDash}
            
        Returns:
            QWidget: The appropriate dashboard widget, or None if no dashboard provided
            
        Example:
            from Users.Admin.AdminDash import AdminDash
            from Users.Faculty.FacultyDash import FacultyDash
            from Users.Non_Admin.Dash import UserDash
            
            # Basic routing by primary role
            dashboard = RoleRouter.route_to_dashboard(
                username, roles, primary_role, token,
                admin_dashboard=AdminDash,
                faculty_dashboard=FacultyDash,
                student_dashboard=UserDash
            )
            
            # Advanced routing with sub-role specific dashboards
            dashboard = RoleRouter.route_to_dashboard(
                username, roles, primary_role, token,
                admin_dashboard=AdminDash,
                faculty_dashboard=FacultyDash,
                student_dashboard=UserDash,
                sub_role_dashboards={
                    'dean': DeanDash,
                    'org_officer': OrgOfficerDash,
                    'registrar': RegistrarDash
                }
            )
        """
        # First, check for specific sub-role dashboard
        if sub_role_dashboards:
            sub_role = RoleRouter.get_sub_role(primary_role, roles)
            if sub_role and sub_role in sub_role_dashboards:
                dashboard_class = sub_role_dashboards[sub_role]
                if dashboard_class:
                    return dashboard_class(username, roles, primary_role, token)
        
        # Fall back to primary role routing
        role_type = RoleRouter.get_primary_role(primary_role, roles)
        
        dashboard_map = {
            'admin': admin_dashboard,
            'faculty': faculty_dashboard,
            'staff': staff_dashboard,
            'student': student_dashboard,
            'guest': default_dashboard
        }
        
        dashboard_class = dashboard_map.get(role_type, default_dashboard)
        
        if dashboard_class:
            return dashboard_class(username, roles, primary_role, token)
        
        return None


# Convenience functions for quick role checks
def is_admin(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is admin."""
    return RoleRouter.is_admin(primary_role, roles)


def is_faculty(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is faculty."""
    return RoleRouter.is_faculty(primary_role, roles)


def is_staff(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is staff."""
    return RoleRouter.is_staff(primary_role, roles)


def is_student(primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user is student."""
    return RoleRouter.is_student(primary_role, roles)


def has_sub_role(sub_role: str, primary_role: str = None, roles: list = None) -> bool:
    """Quick check if user has specific sub-role (e.g., 'dean', 'org_officer')."""
    return RoleRouter.has_sub_role(sub_role, primary_role, roles)
