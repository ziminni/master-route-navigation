from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class ActivityTrackingMixin(models.Model):
    """Mixin to add activity tracking to any model"""
    
    activities = GenericRelation(
        'ActivityLog',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='%(class)s'
    )
    
    class Meta:
        abstract = True
   
    def log_activity(self, action, user=None, description='', **metadata):
        """Log an activity for this instance"""
        from .models import ActivityLog
        return ActivityLog.log(
            action=action,
            content_object=self,
            user=user,
            description=description,
            **metadata
        )
    
    def get_activities(self, action=None, user=None):
        """Get activities for this instance"""
        activities = self.activities.all()
        
        if action:
            activities = activities.filter(action=action)
        if user:
            activities = activities.filter(user=user)
            
        return activities
    
    def get_activity_count(self, action=None):
        """Get count of activities"""
        activities = self.activities.all()
        
        if action:
            activities = activities.filter(action=action)
            
        return activities.count()