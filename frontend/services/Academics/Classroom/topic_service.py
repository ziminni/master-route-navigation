# topic_service.py
import json
from typing import List, Dict, Optional
from datetime import datetime

class TopicService:
    def __init__(self, data_file="services/Academics/data/classroom_data.json"):
        self.data_file = data_file
    
    def _load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"classes": [], "posts": [], "topics": [], "users": []}
    
    def _save_data(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_topics_by_class_id(self, class_id: int) -> List[Dict]:
        """Get all topics for a specific class"""
        data = self._load_data()
        return [topic for topic in data.get("topics", []) 
                if topic.get("class_id") == class_id]
    
    def create_topic(self, class_id: int, title: str, type_: str) -> Optional[Dict]:
        """Create a new topic"""
        data = self._load_data()
        
        # Get next topic ID
        topics = data.get("topics", [])
        next_id = max([t.get("id", 0) for t in topics], default=0) + 1
        
        new_topic = {
            "id": next_id,
            "class_id": class_id,
            "title": title,
            "type": type_,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        data.setdefault("topics", []).append(new_topic)
        self._save_data(data)
        
        return new_topic
    
    def get_topic_by_name(self, class_id: int, title: str) -> Optional[Dict]:
        """Get topic by name"""
        data = self._load_data()
        
        for topic in data.get("topics", []):
            if topic.get("class_id") == class_id and topic.get("title") == title:
                return topic
        
        return None
    
    def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """Get topic by ID"""
        data = self._load_data()
        
        for topic in data.get("topics", []):
            if topic.get("id") == topic_id:
                return topic
        
        return None