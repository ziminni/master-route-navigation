from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organization
from .serializers import OrganizationSerializer


class OrganizationListView(APIView):
    """
    API View for listing organizations.
    GET: Retrieve all organizations
    """
    
    def get(self, request):
        """Retrieve all organizations from database"""
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
