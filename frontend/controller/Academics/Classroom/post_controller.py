# post_controller.py (updated)
from typing import List, Dict, Optional
from frontend.services.Academics.Classroom.post_service import PostService
from frontend.services.Academics.Classroom.topic_service import TopicService

class PostController:
    def __init__(self, post_service: Optional[PostService] = None, 
                 topic_service: Optional[TopicService] = None):
        """Initialize with dependency injection support"""
        self.post_service = post_service or PostService("services/Academics/data/classroom_data.json")
        self.topic_service = topic_service or TopicService("services/Academics/data/classroom_data.json")
        self.current_class_id = None
        self.current_filters = {"filter_type": None, "topic_name": None}

    # ADD THESE SYLLABUS METHODS
    def create_syllabus(self, title: str, content: str, author: str) -> bool:
        """Create a syllabus (separate from posts)"""
        if not all([title, content, author]) or self.current_class_id is None:
            return False
        
        result = self.post_service.create_syllabus(
            class_id=self.current_class_id,  # Use current_class_id from controller
            title=title,
            content=content,
            author=author
        )
        return result is not None
    
    def get_syllabus(self) -> Optional[Dict]:
        """Get syllabus for current class"""
        if self.current_class_id is None:
            return None
        return self.post_service.get_syllabus_by_class_id(self.current_class_id)
    
    def update_syllabus(self, updates: Dict) -> bool:
        """Update syllabus for current class"""
        if self.current_class_id is None:
            return False
        return self.post_service.update_syllabus(self.current_class_id, updates)
    
    def syllabus_exists(self) -> bool:
        """Check if syllabus exists for current class"""
        return self.get_syllabus() is not None
    
    # Add this method to PostController class
    def delete_syllabus(self) -> bool:
        """Delete syllabus for current class"""
        if self.current_class_id is None:
            return False
        return self.post_service.delete_syllabus(self.current_class_id)
    
    def set_class(self, class_id: int) -> None:
        """Set the current class context"""
        self.current_class_id = class_id
    
    def set_filters(self, filter_type: Optional[str] = None, topic_name: Optional[str] = None) -> None:
        """Set current filters"""
        self.current_filters = {
            "filter_type": filter_type,
            "topic_name": topic_name
        }
    
    # Post methods
    def get_stream_posts(self) -> List[Dict]:
        """Get all posts for Stream view (no filtering)"""
        if self.current_class_id is None:
            return []
        return self.post_service.get_posts_by_class_id(self.current_class_id)
    
    def get_classwork_posts(self) -> List[Dict]:
        """Get filtered posts for Classworks view"""
        if self.current_class_id is None:
            return []
        
        return self.post_service.get_posts_by_filters(
            class_id=self.current_class_id,
            filter_type=self.current_filters["filter_type"],
            topic_name=self.current_filters["topic_name"]
        )
    # COMMENT OUT - no longer used for Material/Assessment creation (handled by forms)
    # def create_post(self, title: str, content: str, type_: str, 
    #                author: str, topic_name: Optional[str] = None) -> bool:
    #     """Create a new post"""
    #     if not all([title, content, type_, author]) or self.current_class_id is None:
    #         return False
        
    #     result = self.post_service.create_post(
    #         class_id=self.current_class_id,
    #         title=title,
    #         content=content,
    #         type_=type_,
    #         author=author,
    #         topic_name=topic_name
    #     )
        
    #     return result is not None
    
    # def update_post(self, post_id: int, updates: Dict) -> bool:
    #     """Update an existing post"""
    #     return self.post_service.update_post(post_id, updates)
    
    def delete_post(self, post_id: int) -> bool:
        """Delete a post"""
        return self.post_service.delete_post(post_id)
    
    # def get_post(self, post_id: int) -> Optional[Dict]:
    #     """Get a specific post"""
    #     return self.post_service.get_post_by_id(post_id)
    
    # Topic methods
    def get_available_topics(self) -> List[str]:
        """Get available topics for current class"""
        if self.current_class_id is None:
            return []
        
        topics = self.topic_service.get_topics_by_class_id(self.current_class_id)
        topic_titles = [t["title"] for t in topics if t.get("title")]
        return sorted(list(set(topic_titles)))  # Remove duplicates and sort
    
    def create_topic(self, title: str, type_: str) -> bool:
        """Create a new topic"""
        if not title or self.current_class_id is None:
            return False
        
        result = self.topic_service.create_topic(
            class_id=self.current_class_id,
            title=title,
            type_=type_
        )
        
        return result is not None
    
    def get_topic_by_name(self, title: str) -> Optional[Dict]:
        """Get topic by name for current class"""
        if not title or self.current_class_id is None:
            return None
        
        return self.topic_service.get_topic_by_name(self.current_class_id, title)
    def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """Get topic by ID for current class"""
        if self.current_class_id is None:
            return None
        
        topics = self.topic_service.get_topics_by_class_id(self.current_class_id)
        for topic in topics:
            if topic.get("id") == topic_id:
                return topic
        return None
