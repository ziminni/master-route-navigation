# classwork_service.py (refactored)
from datetime import datetime
from typing import List, Dict, Optional
from .base_service import BaseService

class ClassworkService(BaseService):
    def __init__(self, json_path: str):
        super().__init__(json_path)
    
    def get_classwork_by_class_id(self, class_id: int) -> List[Dict]:
        """Get all posts for a specific class."""
        return [p for p in self.data.get("posts", []) if p.get("class_id") == class_id]
    
    def get_topics_by_class_id(self, class_id: int) -> List[Dict]:
        """Get all topics for a specific class."""
        return [t for t in self.data.get("topics", []) if t.get("class_id") == class_id]
    
    def filter_classwork(self, class_id: int, filter_type: Optional[str] = None, 
                        topic_name: Optional[str] = None) -> List[Dict]:
        """Filter classwork items with proper separation of concerns."""
        posts = self.get_classwork_by_class_id(class_id)
        topics = {t["id"]: t["title"] for t in self.get_topics_by_class_id(class_id)}
        
        filtered_items = []
        for post in posts:
            # Determine topic label
            topic_id = post.get("topic_id")
            topic_label = topics.get(topic_id, "Untitled") if topic_id is not None else "Untitled"
            
            # Apply filters
            if filter_type and post.get("type") != filter_type:
                continue
            if topic_name and topic_label != topic_name:
                continue
            
            # Add topic information to post
            filtered_post = post.copy()
            filtered_post["topic"] = topic_label
            filtered_items.append(filtered_post)
        
        return filtered_items
    
    # COMMENT OUT - creation handled by forms
    # def create_topic(self, class_id: int, title: str, type_: str) -> Optional[Dict]:
    #     """Create a new topic with proper data handling."""
    #     if not title or not class_id:
    #         self.logger.error("Title and class_id are required")
    #         return None
        
    #     try:
    #         topic_data = {
    #             "id": self.generate_id("topics"),
    #             "class_id": class_id,
    #             "title": title,
    #             "type": type_,
    #             "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }
            
    #         if "topics" not in self.data:
    #             self.data["topics"] = []
            
    #         self.data["topics"].append(topic_data)
            
    #         if self.save_data():
    #             return topic_data
    #         return None
            
    #     except Exception as e:
    #         self.logger.error(f"Error creating topic: {e}")
    #         return None
    
    # def create_post(self, class_id: int, title: str, content: str, type_: str, 
    #                topic_name: Optional[str] = None) -> Optional[Dict]:
    #     """Create a new post with proper data handling."""
    #     if not all([title, content, type_, class_id]):
    #         self.logger.error("Title, content, type, and class_id are required")
    #         return None
        
    #     try:
    #         # Find topic ID if topic_name is provided
    #         topic_id = None
    #         if topic_name and topic_name != "None":
    #             topic = next((t for t in self.get_topics_by_class_id(class_id) 
    #                         if t.get("title") == topic_name), None)
    #             topic_id = topic["id"] if topic else None
            
    #         post_data = {
    #             "id": self.generate_id("posts"),
    #             "topic_id": topic_id,
    #             "class_id": class_id,
    #             "title": title,
    #             "content": content,
    #             "type": type_,
    #             "attachment": None,
    #             "score": None if type_ == "material" else 0,
    #             "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #             "author": "Current User"  # This should come from authentication
    #         }
            
    #         if "posts" not in self.data:
    #             self.data["posts"] = []
            
    #         self.data["posts"].append(post_data)
            
    #         if self.save_data():
    #             return post_data
    #         return None
            
    #     except Exception as e:
    #         self.logger.error(f"Error creating post: {e}")
    #         return None
    
    # def update_post(self, post_id: int, updates: Dict) -> bool:
    #     """Update an existing post."""
    #     try:
    #         for i, post in enumerate(self.data.get("posts", [])):
    #             if post.get("id") == post_id:
    #                 self.data["posts"][i].update(updates)
    #                 return self.save_data()
    #         return False
    #     except Exception as e:
    #         self.logger.error(f"Error updating post {post_id}: {e}")
    #         return False
    
    # def delete_post(self, post_id: int) -> bool:
    #     """Delete a post."""
    #     try:
    #         self.data["posts"] = [p for p in self.data.get("posts", []) if p.get("id") != post_id]
    #         return self.save_data()
    #     except Exception as e:
    #         self.logger.error(f"Error deleting post {post_id}: {e}")
    #         return False