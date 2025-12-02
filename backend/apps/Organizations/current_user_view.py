from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.Users.models import BaseUser
from .serializers import CurrentUserSerializer


class CurrentUserView(APIView):
    """API View to get current logged-in user's profile ID"""
    permission_classes = [permissions.AllowAny]  # Allow any for now
    
    def get(self, request):
        """Get current user's BaseUser ID and associated profile ID"""
        try:
            # Get username from query parameter
            username = request.GET.get('username')
            
            if not username:
                return Response(
                    {
                        'success': False,
                        'message': 'Username parameter required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = BaseUser.objects.get(username=username)
            except BaseUser.DoesNotExist:
                return Response(
                    {
                        'success': False,
                        'message': f'User {username} not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get profile ID based on user type
            student_profile_id = None
            profile_type = None
            
            if hasattr(user, 'student_profile') and user.student_profile:
                student_profile_id = user.student_profile.id
                profile_type = 'student'
            elif hasattr(user, 'faculty_profile') and user.faculty_profile:
                profile_type = 'faculty'
            elif hasattr(user, 'staff_profile') and user.staff_profile:
                profile_type = 'staff'
            else:
                profile_type = 'admin'
            
            # base_user_id is the BaseUser.id - used for updated_by field
            base_user_id = user.id
            
            data = CurrentUserSerializer(user).data
            # profile_id is BaseUser.id (for updated_by and general use)
            data['profile_id'] = base_user_id
            data['profile_type'] = profile_type
            data['base_user_id'] = base_user_id
            # student_profile_id is specifically for students to fetch joined orgs
            data['student_profile_id'] = student_profile_id
            data['is_base_user'] = (profile_type == 'admin')
            
            print(f"DEBUG: CurrentUserView - username={user.username}, base_user_id={base_user_id}, student_profile_id={student_profile_id}, profile_type={profile_type}")
            
            return Response(
                {
                    'success': True,
                    'data': data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to get current user - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
