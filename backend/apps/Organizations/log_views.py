"""
Views for accessing organization logs
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Log, Organization, OrganizationMembers, MembershipApplication
from .serializers import LogSerializer
from apps.Users.models import BaseUser


def get_user_name(user_id):
    """Get user's full name by ID"""
    try:
        user = BaseUser.objects.get(id=user_id)
        full_name = user.get_full_name()
        return full_name if full_name else user.username
    except BaseUser.DoesNotExist:
        return f"User #{user_id}"


def get_target_name(target_type, target_id):
    """Get target's name by type and ID"""
    try:
        if target_type == 'Organization':
            org = Organization.objects.get(id=target_id)
            return org.name
        elif target_type == 'OrganizationMembers':
            member = OrganizationMembers.objects.select_related('user_id__user', 'organization_id').get(id=target_id)
            return f"{member.user_id.user.get_full_name()} ({member.organization_id.name})"
        elif target_type == 'MembershipApplication':
            app = MembershipApplication.objects.select_related('user_id__user', 'organization_id').get(id=target_id)
            return f"{app.user_id.user.get_full_name()} → {app.organization_id.name}"
        else:
            return f"{target_type} #{target_id}"
    except Exception:
        return f"{target_type} #{target_id}"


class LogListView(APIView):
    """API View for listing logs"""
    
    def get(self, request):
        """
        Get logs with optional filters:
        - action: Filter by action type
        - target_type: Filter by target type
        - user_id: Filter by user who performed the action
        - limit: Limit number of results (default: 100)
        """
        try:
            # Get query parameters
            action = request.query_params.get('action')
            target_type = request.query_params.get('target_type')
            user_id = request.query_params.get('user_id')
            limit = int(request.query_params.get('limit', 100))
            
            # Start with all logs, ordered by most recent first
            logs = Log.objects.all().order_by('-date_created')
            
            # Apply filters
            if action:
                logs = logs.filter(action=action)
            if target_type:
                logs = logs.filter(target_type=target_type)
            if user_id:
                logs = logs.filter(user_id=user_id)
            
            # Limit results
            logs = logs[:limit]
            
            # Serialize and add user/target names
            serializer = LogSerializer(logs, many=True)
            enriched_data = []
            for log_data, log_obj in zip(serializer.data, logs):
                log_data['user_name'] = get_user_name(log_obj.user_id)
                log_data['target_name'] = get_target_name(log_obj.target_type, log_obj.target_id)
                enriched_data.append(log_data)
            
            return Response(
                {
                    'success': True,
                    'message': 'Logs retrieved successfully',
                    'data': enriched_data,
                    'count': len(enriched_data)
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to fetch logs - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'Failed to retrieve logs: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogDetailView(APIView):
    """API View for getting logs related to a specific target"""
    
    def get(self, request, target_type, target_id):
        """
        Get all logs for a specific target (e.g., all logs for Organization #5)
        
        Args:
            target_type: The type of target (e.g., 'Organization', 'OrganizationMembers')
            target_id: The ID of the target
        """
        try:
            logs = Log.objects.filter(
                target_type=target_type,
                target_id=target_id
            ).order_by('-date_created')
            
            # Serialize and add user/target names
            serializer = LogSerializer(logs, many=True)
            enriched_data = []
            for log_data, log_obj in zip(serializer.data, logs):
                log_data['user_name'] = get_user_name(log_obj.user_id)
                log_data['target_name'] = get_target_name(log_obj.target_type, log_obj.target_id)
                enriched_data.append(log_data)
            
            return Response(
                {
                    'success': True,
                    'message': f'Logs for {target_type} #{target_id} retrieved successfully',
                    'data': enriched_data,
                    'count': len(enriched_data)
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to fetch logs for {target_type} #{target_id} - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to retrieve logs: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
