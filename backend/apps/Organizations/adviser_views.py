"""
Views for managing organization advisers
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.Users.models import FacultyProfile
from .models import Organization, OrgAdviserTerm
from .serializers import OrganizationSerializer


class FacultyAdvisedOrganizationsView(APIView):
    """
    API View for getting organizations that a faculty member advises.
    GET: Retrieve all organizations where the faculty is an adviser
    Query params:
        - faculty_id: FacultyProfile ID (required if username not provided)
        - username: Faculty username (required if faculty_id not provided)
        - search: Optional search term
    """
    
    def get(self, request):
        """Retrieve organizations that the faculty advises"""
        try:
            faculty_id = request.query_params.get('faculty_id')
            username = request.query_params.get('username')
            search_query = request.query_params.get('search')
            
            # Get faculty profile by ID or username
            faculty = None
            if faculty_id:
                try:
                    faculty = FacultyProfile.objects.get(id=faculty_id)
                except FacultyProfile.DoesNotExist:
                    return Response(
                        {
                            'success': False,
                            'message': f'Faculty with id {faculty_id} not found'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif username:
                try:
                    faculty = FacultyProfile.objects.get(user__username=username)
                except FacultyProfile.DoesNotExist:
                    return Response(
                        {
                            'success': False,
                            'message': f'Faculty with username {username} not found'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {
                        'success': False,
                        'message': 'Either faculty_id or username is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all organizations where this faculty is an adviser
            adviser_terms = OrgAdviserTerm.objects.filter(adviser=faculty).select_related('org')
            org_ids = [term.org.id for term in adviser_terms]
            
            # Get the organizations - only active and non-archived
            organizations = Organization.objects.filter(
                id__in=org_ids,
                is_archived=False,
                is_active=True
            )
            
            # Apply search filter if provided
            if search_query:
                from django.db.models import Q
                organizations = organizations.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(objectives__icontains=search_query)
                )
            
            organizations = organizations.order_by('-created_at')
            
            serializer = OrganizationSerializer(organizations, many=True)
            
            return Response(
                {
                    'success': True,
                    'message': 'Advised organizations retrieved successfully',
                    'data': serializer.data,
                    'count': organizations.count()
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to get advised organizations - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FacultyListView(APIView):
    """
    API View for listing all faculty members.
    GET: Retrieve all faculty members for adviser selection dropdown
    """
    
    def get(self, request):
        """Retrieve all faculty members from database"""
        try:
            faculty_profiles = FacultyProfile.objects.select_related('user', 'faculty_department').all()
            
            faculty_list = []
            for profile in faculty_profiles:
                faculty_list.append({
                    'id': profile.id,
                    'user_id': profile.user.id,
                    'name': profile.user.get_full_name(),
                    'email': profile.user.email,
                    'department': profile.faculty_department.department_name if profile.faculty_department else 'N/A',
                })
            
            return Response(
                {
                    'success': True,
                    'message': 'Faculty list retrieved successfully',
                    'data': faculty_list,
                    'count': len(faculty_list)
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve faculty list - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to retrieve faculty list: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrganizationAdvisersView(APIView):
    """
    API View for managing organization advisers.
    GET: Retrieve advisers for a specific organization
    POST: Add an adviser to an organization
    DELETE: Remove an adviser from an organization
    """
    
    def get(self, request, org_id):
        """Retrieve advisers for a specific organization"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            adviser_terms = OrgAdviserTerm.objects.filter(org=organization).select_related('adviser__user', 'adviser__faculty_department')
            
            advisers = []
            for term in adviser_terms:
                advisers.append({
                    'id': term.id,
                    'adviser_id': term.adviser.id,
                    'adviser_name': term.adviser.user.get_full_name(),
                    'adviser_email': term.adviser.user.email,
                    'department': term.adviser.faculty_department.department_name if term.adviser.faculty_department else 'N/A',
                    'role': term.role,
                    'role_display': term.get_role_display(),
                    'start_date': term.start_date.isoformat() if term.start_date else None,
                    'end_date': term.end_date.isoformat() if term.end_date else None,
                })
            
            return Response(
                {
                    'success': True,
                    'message': 'Advisers retrieved successfully',
                    'data': advisers,
                    'count': len(advisers)
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Organization with id {org_id} not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to retrieve advisers - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to retrieve advisers: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, org_id):
        """Add an adviser to an organization"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            adviser_id = request.data.get('adviser_id')
            role = request.data.get('role', 'pri')  # Default to primary
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            
            if not adviser_id:
                return Response(
                    {
                        'success': False,
                        'message': 'adviser_id is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate role
            if role not in ['pri', 'sec']:
                return Response(
                    {
                        'success': False,
                        'message': 'role must be "pri" (Primary) or "sec" (Secondary)'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if organization already has 2 advisers (maximum)
            current_adviser_count = OrgAdviserTerm.objects.filter(org=organization).count()
            if current_adviser_count >= 2:
                return Response(
                    {
                        'success': False,
                        'message': 'Organization already has maximum 2 advisers'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the faculty profile
            try:
                adviser = FacultyProfile.objects.get(id=adviser_id)
            except FacultyProfile.DoesNotExist:
                return Response(
                    {
                        'success': False,
                        'message': f'Faculty with id {adviser_id} not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if this adviser already has this role for this org
            existing = OrgAdviserTerm.objects.filter(org=organization, adviser=adviser, role=role).first()
            if existing:
                return Response(
                    {
                        'success': False,
                        'message': f'{adviser.user.get_full_name()} is already a {existing.get_role_display()} adviser for this organization'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If setting as primary, check if primary already exists
            if role == 'pri':
                existing_primary = OrgAdviserTerm.objects.filter(org=organization, role='pri').first()
                if existing_primary:
                    return Response(
                        {
                            'success': False,
                            'message': f'This organization already has a primary adviser: {existing_primary.adviser.user.get_full_name()}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # If setting as secondary, check if secondary already exists
            if role == 'sec':
                existing_secondary = OrgAdviserTerm.objects.filter(org=organization, role='sec').first()
                if existing_secondary:
                    return Response(
                        {
                            'success': False,
                            'message': f'This organization already has a secondary adviser: {existing_secondary.adviser.user.get_full_name()}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate start_date is required
            if not start_date:
                return Response(
                    {
                        'success': False,
                        'message': 'start_date is required for adviser term'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the adviser term
            adviser_term = OrgAdviserTerm.objects.create(
                org=organization,
                adviser=adviser,
                role=role,
                start_date=start_date,
                end_date=end_date if end_date else None
            )
            
            return Response(
                {
                    'success': True,
                    'message': f'{adviser.user.get_full_name()} added as {adviser_term.get_role_display()} adviser',
                    'data': {
                        'id': adviser_term.id,
                        'adviser_id': adviser.id,
                        'adviser_name': adviser.user.get_full_name(),
                        'role': adviser_term.role,
                        'role_display': adviser_term.get_role_display()
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Organization.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Organization with id {org_id} not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to add adviser - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'Failed to add adviser: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, org_id):
        """Remove an adviser from an organization"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            adviser_term_id = request.data.get('adviser_term_id')
            
            if not adviser_term_id:
                return Response(
                    {
                        'success': False,
                        'message': 'adviser_term_id is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                adviser_term = OrgAdviserTerm.objects.get(id=adviser_term_id, org=organization)
            except OrgAdviserTerm.DoesNotExist:
                return Response(
                    {
                        'success': False,
                        'message': f'Adviser term with id {adviser_term_id} not found for this organization'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            adviser_name = adviser_term.adviser.user.get_full_name()
            adviser_term.delete()
            
            return Response(
                {
                    'success': True,
                    'message': f'{adviser_name} removed as adviser'
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Organization with id {org_id} not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to remove adviser - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to remove adviser: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateOrganizationAdviserView(APIView):
    """
    API View for updating an adviser's role.
    PUT: Update an adviser's role for an organization
    """
    
    def put(self, request, org_id, adviser_term_id):
        """Update an adviser's role"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            try:
                adviser_term = OrgAdviserTerm.objects.get(id=adviser_term_id, org=organization)
            except OrgAdviserTerm.DoesNotExist:
                return Response(
                    {
                        'success': False,
                        'message': f'Adviser term with id {adviser_term_id} not found for this organization'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            new_role = request.data.get('role')
            
            if new_role and new_role in ['pri', 'sec']:
                # If changing to primary, check if primary already exists
                if new_role == 'pri' and adviser_term.role != 'pri':
                    existing_primary = OrgAdviserTerm.objects.filter(org=organization, role='pri').exclude(id=adviser_term_id).first()
                    if existing_primary:
                        return Response(
                            {
                                'success': False,
                                'message': f'This organization already has a primary adviser: {existing_primary.adviser.user.get_full_name()}'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                adviser_term.role = new_role
            
            # Update dates if provided
            if 'start_date' in request.data:
                adviser_term.start_date = request.data.get('start_date') or None
            if 'end_date' in request.data:
                adviser_term.end_date = request.data.get('end_date') or None
            
            adviser_term.save()
            
            return Response(
                {
                    'success': True,
                    'message': 'Adviser updated successfully',
                    'data': {
                        'id': adviser_term.id,
                        'adviser_id': adviser_term.adviser.id,
                        'adviser_name': adviser_term.adviser.user.get_full_name(),
                        'role': adviser_term.role,
                        'role_display': adviser_term.get_role_display(),
                        'start_date': adviser_term.start_date.isoformat() if adviser_term.start_date else None,
                        'end_date': adviser_term.end_date.isoformat() if adviser_term.end_date else None
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Organization with id {org_id} not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to update adviser - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to update adviser: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
