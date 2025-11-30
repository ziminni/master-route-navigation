from rest_framework import serializers
from .models import Organization


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
        fields = ['id', 'name', 'description', 'status', 'logo_path', 'created_at', 'org_level', 'main_org']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Create organization without main_org, it will be set separately"""
        main_org = validated_data.pop('main_org', None)
        organization = Organization.objects.create(**validated_data)
        if main_org:
            organization.main_org.set(main_org)
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
