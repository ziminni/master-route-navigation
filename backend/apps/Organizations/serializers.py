from rest_framework import serializers
from .models import Organization, ApplicationDetails, MembershipApplication
from apps.Users.models import StudentProfile


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""
    main_org = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Organization.objects.all(), 
        required=False,
        allow_empty=True,
        read_only=False
    )
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'description', 'objectives', 'status', 'logo_path', 'created_at', 'org_level', 'main_org']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Create organization and corresponding ApplicationDetails entry"""
        main_org = validated_data.pop('main_org', None)
        
        # Create the organization
        organization = Organization.objects.create(**validated_data)
        
        # Set main_org relationships if provided
        if main_org:
            organization.main_org.set(main_org)
        
        # Determine if it's a branch or organization
        org_type = "branch" if main_org else "organization"
        
        # Create ApplicationDetails entry
        ApplicationDetails.objects.create(
            title=organization.name,
            description=f"An application for {organization.name}"
        )
        
        return organization
    
    def update(self, instance, validated_data):
        """Update organization including main_org relationships"""
        main_org = validated_data.pop('main_org', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update main_org ManyToMany relationship if provided
        if main_org is not None:
            instance.main_org.set(main_org)
        
        return instance
    
    def validate_name(self, value):
        """Ensure organization name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Organization name cannot be empty.")
        return value.strip()
    
    def validate_org_level(self, value):
        """Validate org_level is either 'col' or 'prog'"""
        if value not in ['col', 'prog']:
            raise serializers.ValidationError("org_level must be 'col' (College) or 'prog' (Program)")
        return value


class MembershipApplicationSerializer(serializers.ModelSerializer):
    """Serializer for MembershipApplication model"""
    user_id = serializers.PrimaryKeyRelatedField(queryset=StudentProfile.objects.all())
    organization_id = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    application_details_id = serializers.PrimaryKeyRelatedField(queryset=ApplicationDetails.objects.all())
    
    # Read-only fields for display
    student_name = serializers.CharField(source='user_id.user.get_full_name', read_only=True)
    organization_name = serializers.CharField(source='organization_id.name', read_only=True)
    
    class Meta:
        model = MembershipApplication
        fields = ['id', 'user_id', 'organization_id', 'application_details_id', 'application_status', 'student_name', 'organization_name']
        read_only_fields = ['id']
    
    def validate(self, data):
        """Check if student has already applied or is already a member"""
        user = data.get('user_id')
        org = data.get('organization_id')
        
        # Check if already a member
        from .models import OrganizationMembers
        if OrganizationMembers.objects.filter(user_id=user, organization_id=org, status='active').exists():
            raise serializers.ValidationError("You are already a member of this organization.")
        
        # Check if already has a pending application
        if MembershipApplication.objects.filter(user_id=user, organization_id=org, application_status='pen').exists():
            raise serializers.ValidationError("You already have a pending application for this organization.")
        
        return data
