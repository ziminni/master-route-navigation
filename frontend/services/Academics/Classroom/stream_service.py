# stream_service.py (refactored)
from datetime import datetime
from typing import List, Dict
from .base_service import BaseService

class StreamService(BaseService):
    def __init__(self, json_path: str):
        super().__init__(json_path)
    
    def get_posts_by_class_id(self, class_id: int) -> List[Dict]:
        """Get posts for a class, sorted by date (newest first)."""
        posts = [p for p in self.data.get("posts", []) if p.get("class_id") == class_id]
        
        try:
            return sorted(posts, 
                         key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"), 
                         reverse=True)
        except (KeyError, ValueError):
            return posts  # Fallback to original order
    
    def add_post(self, class_id: int, post_data: Dict) -> bool:
        """Add a new post to the stream."""
        try:
            post_data["id"] = self.generate_id("posts")
            post_data["class_id"] = class_id
            post_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if "posts" not in self.data:
                self.data["posts"] = []
            
            self.data["posts"].append(post_data)
            return self.save_data()
            
        except Exception as e:
            self.logger.error(f"Error adding post: {e}")
            return False