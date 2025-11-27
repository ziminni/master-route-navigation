from django.db import models

class ActivityTrackingMixin:
   
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