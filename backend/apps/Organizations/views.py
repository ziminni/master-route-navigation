from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Organization, MembershipApplication, ApplicationDetails, OrganizationMembers
from .serializers import OrganizationSerializer, MembershipApplicationSerializer, ApplicantSerializer, CurrentUserSerializer
from django.db.models import Q
from apps.Users.models import StudentProfile, BaseUser
from .log_service import log_created, log_edited, log_kicked, log_accepted, log_rejected, log_applied, log_archived, log_activated, log_deactivated


class OrganizationListView(APIView):
    """
    API View for listing organizations.
    GET: Retrieve all organizations or search by query parameter
    Query params:
        - search: search term
        - role: 'admin' to see all orgs, otherwise only active & non-archived orgs are returned
        - include_archived: 'true' to include archived orgs (for archived view)
    """
    
    def get(self, request):
        """Retrieve organizations from database, optionally filtered by search query and role"""
        search_query = request.query_params.get('search', None)
        role = request.query_params.get('role', None)
        include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'
        
        # Start with base queryset
        organizations = Organization.objects.all()
        
        # Apply role-based filtering
        if role == 'admin':
            if include_archived:
                # Admin viewing archived - only show archived
                organizations = organizations.filter(is_archived=True)
            else:
                # Admin viewing main list - show all non-archived
                organizations = organizations.filter(is_archived=False)
        else:
            # Non-admin users only see active and non-archived organizations
            organizations = organizations.filter(is_archived=False, is_active=True)
        
        # Apply search filter if provided
        if search_query:
            organizations = organizations.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(objectives__icontains=search_query)
            )
        
        organizations = organizations.order_by('-created_at')
        
        serializer = OrganizationSerializer(organizations, many=True)
        
        return Response(
            {
                'message': 'Organizations retrieved successfully',
                'data': serializer.data,
                'count': organizations.count()
            },
            status=status.HTTP_200_OK
        )


class StudentJoinedOrganizationsView(APIView):
    """
    API View for getting organizations that a student has joined.
    GET: Retrieve all organizations where the student is a member
    Only returns active and non-archived organizations
    """
    
    def get(self, request, student_id):
        """Retrieve organizations that the student has joined (is a member of)"""
        try:
            # Get student profile
            try:
                student = StudentProfile.objects.get(id=student_id)
                print(f"DEBUG: Found student: {student.user.get_full_name()} (ID: {student_id})")
            except StudentProfile.DoesNotExist:
                print(f"ERROR: Student with id {student_id} not found")
                return Response(
                    {
                        'success': False,
                        'message': f'Student with id {student_id} not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all organizations where this student is an active member
            memberships = OrganizationMembers.objects.filter(
                user_id=student
            ).select_related('organization_id')
            
            print(f"DEBUG: Found {memberships.count()} total memberships")
            for membership in memberships:
                print(f"DEBUG: Membership - Org: {membership.organization_id.name}, Status: {membership.status}")
            
            # Filter for active memberships (database uses 'active' for active status)
            active_memberships = memberships.filter(status='active')
            print(f"DEBUG: Found {active_memberships.count()} active memberships with status='active'")
            
            # Extract organization IDs
            org_ids = [membership.organization_id.id for membership in active_memberships]
            print(f"DEBUG: Organization IDs: {org_ids}")
            
            # Get the organization details - only active and non-archived orgs
            organizations = Organization.objects.filter(
                id__in=org_ids,
                is_active=True,
                is_archived=False
            ).order_by('-created_at')
            
            serializer = OrganizationSerializer(organizations, many=True)
            
            return Response(
                {
                    'success': True,
                    'message': 'Joined organizations retrieved successfully',
                    'data': serializer.data,
                    'count': organizations.count()
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to get joined organizations - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrganizationDetailView(APIView):
    """
    API View for retrieving and updating organization details.
    GET: Retrieve detailed information for a specific organization
    PUT/PATCH: Update organization information
    """
    
    def get(self, request, org_id):
        """Retrieve detailed organization information including branches"""
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response(
                {
                    'message': 'Organization not found',
                    'error': f'Organization with id {org_id} does not exist'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize the organization
        serializer = OrganizationSerializer(organization)
        org_data = serializer.data
        
        # Get branches (organizations that have this org as their main_org)
        branches = Organization.objects.filter(main_org=organization)
        branches_serializer = OrganizationSerializer(branches, many=True)
        org_data['branches'] = branches_serializer.data
        
        return Response(
            {
                'message': 'Organization details retrieved successfully',
                'data': org_data
            },
            status=status.HTTP_200_OK
        )
    
    def put(self, request, org_id):
        """Update organization information"""
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response(
                {
                    'message': 'Organization not found',
                    'error': f'Organization with id {org_id} does not exist'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_org = serializer.save()
            
            # Log the edit action
            updated_by_id = request.data.get('updated_by_id')
            if updated_by_id:
                log_edited(user_id=updated_by_id, target=updated_org)
            
            return Response(
                {
                    'message': 'Organization updated successfully',
                    'data': OrganizationSerializer(updated_org).data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {
                'message': 'Failed to update organization',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class OrganizationCreateView(APIView):
    """
    API View for creating organizations.
    POST: Create a new organization
    """
    
    def post(self, request):
        """Create a new organization"""
        serializer = OrganizationSerializer(data=request.data)
        
        if serializer.is_valid():
            organization = serializer.save()
            
            # Log the creation action
            created_by_id = request.data.get('created_by_id')
            if created_by_id:
                log_created(user_id=created_by_id, target=organization)
            
            return Response(
                {
                    'message': 'Organization created successfully',
                    'data': OrganizationSerializer(organization).data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {
                'message': 'Failed to create organization',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class MembershipApplicationCreateView(APIView):
    """API View for creating membership applications"""
    
    def post(self, request):
        """Submit a membership application"""
        user_id = request.data.get('user_id')
        org_id = request.data.get('organization_id')
        
        # Validate required fields
        if not user_id or not org_id:
            return Response(
                {'message': 'user_id and organization_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the ApplicationDetails for this organization
            organization = Organization.objects.get(id=org_id)
            app_details = ApplicationDetails.objects.filter(title=organization.name).first()
            
            if not app_details:
                return Response(
                    {'message': 'Application details not found for this organization'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create application data
            application_data = {
                'user_id': user_id,
                'organization_id': org_id,
                'application_details_id': app_details.id,
                'application_status': 'pen'
            }
            
            serializer = MembershipApplicationSerializer(data=application_data)
            
            if serializer.is_valid():
                application = serializer.save()
                
                # Log the application action - get the BaseUser ID from StudentProfile
                try:
                    student = StudentProfile.objects.get(id=user_id)
                    log_applied(user_id=student.user.id, target=application)
                except StudentProfile.DoesNotExist:
                    pass  # Still allow application to proceed
                
                return Response(
                    {
                        'message': 'Application submitted successfully',
                        'data': MembershipApplicationSerializer(application).data
                    },
                    status=status.HTTP_201_CREATED
                )
            
            return Response(
                {
                    'message': 'Failed to submit application',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Organization.DoesNotExist:
            return Response(
                {'message': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {'message': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class StudentApplicationStatusView(APIView):
    """API View for getting student's application statuses"""
    
    def get(self, request, user_id):
        """Get all pending/accepted/rejected applications for a student by StudentProfile ID"""
        try:
            # user_id here is the StudentProfile ID, not Django User ID
            student = StudentProfile.objects.get(id=user_id)
            
            # Get all applications for this student
            applications = MembershipApplication.objects.filter(user_id=student).select_related('organization_id')
            
            # Build response with organization IDs and their status
            application_statuses = {}
            for app in applications:
                application_statuses[str(app.organization_id.id)] = {
                    'status': app.application_status,
                    'org_name': app.organization_id.name,
                    'application_id': app.id
                }
            
            return Response(
                {
                    'message': 'Application statuses retrieved successfully',
                    'data': application_statuses
                },
                status=status.HTTP_200_OK
            )
            
        except StudentProfile.DoesNotExist:
            return Response(
                {'message': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrganizationApplicantsView(APIView):
    """API View for getting pending applicants for an organization"""
    
    def get(self, request, org_id):
        """Get all pending applicants for a specific organization"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Get all pending applications for this organization
            pending_applications = MembershipApplication.objects.filter(
                organization_id=organization,
                application_status='pen'
            ).select_related('user_id__user', 'user_id')
            
            print(f"DEBUG: Found {pending_applications.count()} pending applications for org {org_id}")
            
            # Serialize the applications with student details
            from .serializers import ApplicantSerializer
            serializer = ApplicantSerializer(pending_applications, many=True)
            
            print(f"DEBUG: Serialized data: {serializer.data}")
            
            return Response(
                {
                    'message': 'Applicants retrieved successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {'message': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ApplicationActionView(APIView):
    """API View for accepting or rejecting applications"""
    
    def put(self, request, application_id):
        """Accept or reject a membership application"""
        try:
            print(f"DEBUG: Processing application {application_id} with action: {request.data.get('action')}")
            
            application = MembershipApplication.objects.get(id=application_id)
            action = request.data.get('action')  # 'accept' or 'reject'
            
            if action not in ['accept', 'reject']:
                return Response(
                    {'message': 'Invalid action. Must be "accept" or "reject"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if action == 'accept':
                # Update application status to accepted
                application.application_status = 'acc'
                application.save()
                print(f"DEBUG: Updated application status to accepted")
                
                # Log the accept action
                admin_user_id = request.data.get('admin_user_id')
                if admin_user_id:
                    log_accepted(user_id=admin_user_id, target=application)
                
                # Create OrganizationMembers entry (only use existing fields)
                from .models import OrganizationMembers
                try:
                    member, created = OrganizationMembers.objects.get_or_create(
                        organization_id=application.organization_id,
                        user_id=application.user_id,
                        defaults={'status': 'active'}  # Active status
                    )
                    if created:
                        print(f"DEBUG: Created new organization member - org_id: {application.organization_id.id}, user_id: {application.user_id.id}")
                    else:
                        print(f"DEBUG: Member already exists, updating status to active")
                        member.status = 'active'
                        member.save()
                    
                    # Verify the member was saved
                    verify_count = OrganizationMembers.objects.filter(
                        organization_id=application.organization_id,
                        user_id=application.user_id,
                        status='active'
                    ).count()
                    print(f"DEBUG: Verification - Active member count for this org/user: {verify_count}")
                    
                except Exception as e:
                    print(f"DEBUG ERROR: Failed to create member - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return Response(
                        {'message': f'Application accepted but failed to create member: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                return Response(
                    {
                        'success': True,
                        'message': 'Application accepted successfully',
                        'application_id': application_id
                    },
                    status=status.HTTP_200_OK
                )
            
            elif action == 'reject':
                # Update application status to rejected
                application.application_status = 'rej'
                application.save()
                print(f"DEBUG: Updated application status to rejected")
                
                # Log the reject action
                admin_user_id = request.data.get('admin_user_id')
                if admin_user_id:
                    log_rejected(user_id=admin_user_id, target=application)
                
                return Response(
                    {'message': 'Application rejected successfully'},
                    status=status.HTTP_200_OK
                )
                
        except MembershipApplication.DoesNotExist:
            print(f"DEBUG ERROR: Application {application_id} not found")
            return Response(
                {'message': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"DEBUG ERROR: Unexpected error - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'message': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrganizationMembersView(APIView):
    """API View for getting members of an organization"""
    
    def get(self, request, org_id):
        """Get all active members for a specific organization"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Get all active members for this organization
            from .models import OrganizationMembers, OfficerTerm
            members = OrganizationMembers.objects.filter(
                organization_id=organization,
                status='active'  # Active status
            ).select_related('user_id__user', 'user_id')
            
            print(f"DEBUG: Found {members.count()} active members for org {org_id}")
            
            # Build member data
            members_data = []
            for member in members:
                # Get current officer position if exists
                officer_term = OfficerTerm.objects.filter(
                    member=member,
                    status='active'
                ).select_related('position').first()
                
                position_name = officer_term.position.name if officer_term else 'Member'
                position_id = officer_term.position.id if officer_term else None
                photo_url = officer_term.photo.url if officer_term and officer_term.photo else None
                start_term = officer_term.start_term.isoformat() if officer_term and officer_term.start_term else None
                end_term = officer_term.end_term.isoformat() if officer_term and officer_term.end_term else None
                
                members_data.append({
                    'id': member.id,
                    'student_id': member.user_id.id,
                    'name': member.user_id.user.get_full_name(),
                    'username': member.user_id.user.username,
                    'email': member.user_id.user.email,
                    'program': str(member.user_id.program) if member.user_id.program else 'N/A',
                    'year_level': member.user_id.year_level,
                    'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                    'status': member.status,
                    'position': position_name,
                    'position_id': position_id,
                    'photo_url': photo_url,
                    'start_term': start_term,
                    'end_term': end_term
                })
            
            return Response(
                {
                    'message': 'Members retrieved successfully',
                    'data': members_data
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {'message': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class KickMemberView(APIView):
    """API View for kicking/removing members from an organization"""
    
    def post(self, request, member_id):
        """Kick a member from the organization"""
        try:
            from .models import OrganizationMembers, OfficerTerm
            from django.conf import settings
            
            # Get the member to kick
            member = OrganizationMembers.objects.get(id=member_id)
            
            # Get the admin who is performing the kick
            username = request.query_params.get('username')
            if not username:
                return Response(
                    {'success': False, 'message': 'Username is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                admin_user = BaseUser.objects.get(username=username)
            except BaseUser.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'Admin user not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update member status and kick fields
            member.status = 'inactive'
            member.is_kick = True
            member.kicked_by = admin_user
            member.save()
            
            # Log the kick action
            log_kicked(user_id=admin_user.id, target=member)
            
            print(f"DEBUG: Member {member_id} kicked by admin {admin_user.username}")
            
            # Deactivate any active officer terms for this member
            active_terms = OfficerTerm.objects.filter(
                member=member,
                status='active'
            )
            
            for term in active_terms:
                # Keep the existing end_term or set to today if not set
                from datetime import date, timedelta
                if not term.end_term or term.end_term > date.today():
                    # Set end_term to today (or day before if it violates CHECK constraint)
                    new_end_term = date.today() if date.today() > term.start_term else term.start_term + timedelta(days=1)
                    term.end_term = new_end_term
                
                term.status = 'inactive'
                term.updated_by = admin_user
                term.save()
                print(f"DEBUG: Deactivated officer term for kicked member")
            
            return Response(
                {
                    'success': True,
                    'message': 'Member kicked successfully'
                },
                status=status.HTTP_200_OK
            )
            
        except OrganizationMembers.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to kick member - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'success': False, 'message': f'Failed to kick member: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ArchiveOrganizationView(APIView):
    """API View for archiving an organization"""
    
    def post(self, request, org_id):
        """Archive an organization - it will be hidden and cannot be retrieved"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Archive the organization
            organization.is_archived = True
            organization.is_active = False  # Archived orgs are automatically inactive
            organization.save()
            
            # Log the archive action
            admin_user_id = request.data.get('admin_user_id')
            if admin_user_id:
                log_archived(user_id=admin_user_id, target=organization)
            
            return Response(
                {
                    'success': True,
                    'message': 'Organization archived successfully',
                    'data': OrganizationSerializer(organization).data
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to archive organization - {str(e)}")
            return Response(
                {'success': False, 'message': f'Failed to archive organization: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ToggleOrganizationActiveView(APIView):
    """API View for activating/deactivating an organization"""
    
    def post(self, request, org_id):
        """Toggle organization active status"""
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Cannot activate an archived organization
            if organization.is_archived:
                return Response(
                    {'success': False, 'message': 'Cannot activate an archived organization'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Toggle the active status
            organization.is_active = not organization.is_active
            organization.save()
            
            # Log the action
            admin_user_id = request.data.get('admin_user_id')
            if admin_user_id:
                if organization.is_active:
                    log_activated(user_id=admin_user_id, target=organization)
                else:
                    log_deactivated(user_id=admin_user_id, target=organization)
            
            action = 'activated' if organization.is_active else 'deactivated'
            
            return Response(
                {
                    'success': True,
                    'message': f'Organization {action} successfully',
                    'data': OrganizationSerializer(organization).data,
                    'is_active': organization.is_active
                },
                status=status.HTTP_200_OK
            )
            
        except Organization.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"ERROR: Failed to toggle organization active status - {str(e)}")
            return Response(
                {'success': False, 'message': f'Failed to toggle organization status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

