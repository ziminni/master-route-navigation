from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organization, MembershipApplication, ApplicationDetails
from .serializers import OrganizationSerializer, MembershipApplicationSerializer
from django.db.models import Q
from apps.Users.models import StudentProfile


class OrganizationListView(APIView):
    """
    API View for listing organizations.
    GET: Retrieve all organizations or search by query parameter
    """
    
    def get(self, request):
        """Retrieve organizations from database, optionally filtered by search query"""
        search_query = request.query_params.get('search', None)
        
        if search_query:
            # Search in name, description, and objectives
            organizations = Organization.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(objectives__icontains=search_query)
            ).order_by('-created_at')
        else:
            organizations = Organization.objects.all().order_by('-created_at')
        
        serializer = OrganizationSerializer(organizations, many=True)
        
        return Response(
            {
                'message': 'Organizations retrieved successfully',
                'data': serializer.data,
                'count': organizations.count()
            },
            status=status.HTTP_200_OK
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
        """Get all pending/accepted/rejected applications for a student"""
        try:
            student = StudentProfile.objects.get(user__id=user_id)
            
            # Get all applications for this student
            applications = MembershipApplication.objects.filter(user_id=student).select_related('organization_id')
            
            # Build response with organization IDs and their status
            application_statuses = {}
            for app in applications:
                application_statuses[app.organization_id.id] = {
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
