"""
Views for managing positions and member positions
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from datetime import date

from .models import Positions, OrganizationMembers, OfficerTerm, Organization
from apps.Users.models import BaseUser


class PositionsListView(APIView):
    """API View for listing all available positions"""
    
    def get(self, request):
        """Get all positions ordered by rank, excluding 'Member' position"""
        try:
            # Exclude positions named "Member" to avoid duplicates
            positions = Positions.objects.exclude(name__iexact='member').order_by('rank', 'name')
            
            positions_data = [{
                'id': pos.id,
                'name': pos.name,
                'rank': pos.rank,
                'description': pos.description
            } for pos in positions]
            
            return Response(
                {
                    'success': True,
                    'message': 'Positions retrieved successfully',
                    'data': positions_data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to fetch positions - {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': f'Failed to retrieve positions: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemberPositionUpdateView(APIView):
    """API View for updating a member's position"""
    
    def get(self, request, member_id):
        """
        Get current officer term information for a member
        
        Args:
            member_id: OrganizationMembers ID
            
        Returns:
            position_id, position_name, start_term, end_term (if exists)
        """
        try:
            # Get the member
            try:
                member = OrganizationMembers.objects.select_related(
                    'organization_id', 'user_id__user'
                ).get(id=member_id)
            except OrganizationMembers.DoesNotExist:
                return Response(
                    {
                        'success': False,
                        'message': 'Member not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get current active officer term if exists
            officer_term = OfficerTerm.objects.filter(
                member=member,
                status='active'
            ).select_related('position').first()
            
            if officer_term:
                term_data = {
                    'position_id': officer_term.position.id,
                    'position_name': officer_term.position.name,
                    'start_term': officer_term.start_term.isoformat() if officer_term.start_term else None,
                    'end_term': officer_term.end_term.isoformat() if officer_term.end_term else None,
                    'has_officer_term': True
                }
            else:
                # Regular member with no officer position
                term_data = {
                    'position_id': None,
                    'position_name': 'Member',
                    'start_term': None,
                    'end_term': None,
                    'has_officer_term': False
                }
            
            return Response(
                {
                    'success': True,
                    'message': 'Officer term data retrieved successfully',
                    'data': term_data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"ERROR: Failed to get officer term data - {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, member_id):
        """
        Update a member's position and manage OfficerTerm records
        
        Args:
            member_id: OrganizationMembers ID
            position_id: Positions ID (from request data)
            position_name: Position name (for reference)
            start_term: Term start date (for officers)
            end_term: Term end date (for officers, optional)
            updated_by_id: StudentProfile ID of the user making the update
        """
        try:
            position_id = request.data.get('position_id')
            position_name = request.data.get('position_name', 'Unknown')
            start_term_str = request.data.get('start_term')
            end_term_str = request.data.get('end_term')
            updated_by_id = request.data.get('updated_by_id')
            
            print(f"DEBUG: Updating member {member_id} to position {position_name} (ID: {position_id})")
            print(f"DEBUG: Term dates - Start: {start_term_str}, End: {end_term_str}")
            print(f"DEBUG: Updated by BaseUser ID: {updated_by_id}")
            
            # Get the member
            try:
                member = OrganizationMembers.objects.select_related(
                    'organization_id', 'user_id__user'
                ).get(id=member_id)
                print(f"DEBUG: Found member: {member.user_id.user.get_full_name()}")
            except OrganizationMembers.DoesNotExist:
                print(f"ERROR: Member {member_id} not found")
                return Response(
                    {
                        'success': False,
                        'message': 'Member not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get updated_by user if provided (BaseUser ID)
            updated_by_user = None
            if updated_by_id:
                try:
                    updated_by_user = BaseUser.objects.get(id=updated_by_id)
                    print(f"DEBUG: Updated by BaseUser: {updated_by_user.get_full_name() or updated_by_user.username} (ID: {updated_by_user.id})")
                except BaseUser.DoesNotExist:
                    print(f"WARNING: BaseUser {updated_by_id} not found, continuing without audit trail")
            else:
                print("WARNING: No updated_by_id provided")
            
            # Check if position_id is None or "Member" (regular member, no officer role)
            is_regular_member = (position_id is None or position_name.lower() == 'member')
            
            with transaction.atomic():
                if is_regular_member:
                    # Remove any existing active officer terms for this member
                    # Set end_term to NULL to avoid CHECK constraint issues
                    updated_count = OfficerTerm.objects.filter(
                        member=member,
                        status='active'
                    ).update(
                        status='inactive',
                        end_term=None,
                        updated_by=updated_by_user
                    )
                    print(f"DEBUG: Deactivated {updated_count} officer terms for member {member_id}")
                    
                else:
                    # Validate start_term and end_term are provided for officer positions
                    if not start_term_str:
                        return Response(
                            {
                                'success': False,
                                'message': 'Start term date is required for officer positions'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    if not end_term_str:
                        return Response(
                            {
                                'success': False,
                                'message': 'End term date is required for officer positions'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Parse dates
                    try:
                        from datetime import datetime
                        start_term = datetime.strptime(start_term_str, '%Y-%m-%d').date()
                        end_term = datetime.strptime(end_term_str, '%Y-%m-%d').date()
                        print(f"DEBUG: Parsed dates - Start: {start_term}, End: {end_term}")
                        
                        # Validate date order - start_term must be before end_term
                        if start_term >= end_term:
                            print(f"ERROR: Invalid date range - start_term ({start_term}) >= end_term ({end_term})")
                            return Response(
                                {
                                    'success': False,
                                    'message': f'Start term date ({start_term}) must be before end term date ({end_term})'
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except ValueError as e:
                        print(f"ERROR: Invalid date format - {str(e)}")
                        return Response(
                            {
                                'success': False,
                                'message': f'Invalid date format: {str(e)}'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Get the position
                    try:
                        position = Positions.objects.get(id=position_id)
                        print(f"DEBUG: Found position: {position.name}")
                    except Positions.DoesNotExist:
                        print(f"ERROR: Position {position_id} not found")
                        return Response(
                            {
                                'success': False,
                                'message': 'Position not found'
                            },
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    # Check if position is already occupied by another member
                    existing_officer = OfficerTerm.objects.filter(
                        org=member.organization_id,
                        position=position,
                        status='active'
                    ).exclude(member=member).first()
                    
                    if existing_officer:
                        existing_member_name = existing_officer.member.user_id.user.get_full_name()
                        print(f"ERROR: Position already occupied by {existing_member_name}")
                        return Response(
                            {
                                'success': False,
                                'message': f'Position already occupied by {existing_member_name}'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Deactivate any existing officer terms for this member
                    # Set end_term to NULL to avoid CHECK constraint issues (start_term < end_term)
                    deactivated = OfficerTerm.objects.filter(
                        member=member,
                        status='active'
                    ).update(
                        status='inactive',
                        end_term=None,
                        updated_by=updated_by_user
                    )
                    print(f"DEBUG: Deactivated {deactivated} existing officer terms")
                    
                    # Create new officer term
                    new_term = OfficerTerm.objects.create(
                        org=member.organization_id,
                        position=position,
                        member=member,
                        start_term=start_term,
                        end_term=end_term,
                        status='active',
                        updated_by=updated_by_user
                    )
                    print(f"DEBUG: Created new officer term (ID: {new_term.id}) for {member.user_id.user.get_full_name()} as {position.name}")
                
                # Get updated member data with current position
                current_officer = OfficerTerm.objects.filter(
                    member=member,
                    status='active'
                ).select_related('position').first()
                
                position_display = current_officer.position.name if current_officer else 'Member'
                position_id_display = current_officer.position.id if current_officer else None
                
                # Return complete updated member data matching OrganizationMembersView format
                updated_member_data = {
                    'id': member.id,
                    'student_id': member.user_id.id,
                    'name': member.user_id.user.get_full_name(),
                    'username': member.user_id.user.username,
                    'email': member.user_id.user.email,
                    'program': str(member.user_id.program) if member.user_id.program else 'N/A',
                    'year_level': member.user_id.year_level,
                    'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                    'status': member.status,
                    'position': position_display,
                    'position_id': position_id_display
                }
                
                print(f"DEBUG: Returning updated member data: {updated_member_data}")
                
                return Response(
                    {
                        'success': True,
                        'message': f'Member position updated to {position_display}',
                        'data': updated_member_data
                    },
                    status=status.HTTP_200_OK
                )
                
        except OSError as e:
            print(f"ERROR: OSError in update member position - {str(e)}")
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            print(f"ERROR: OSError details - errno: {e.errno}, strerror: {e.strerror if hasattr(e, 'strerror') else 'N/A'}")
            return Response(
                {
                    'success': False,
                    'message': f'System error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            print(f"ERROR: Failed to update member position - {str(e)}")
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)
            return Response(
                {
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
