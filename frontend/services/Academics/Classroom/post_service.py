# post_service.py
import json
from typing import List, Dict, Optional
from datetime import datetime

class PostService:
    def __init__(self, data_file="services/Academics/data/classroom_data.json"):
        self.data_file = data_file
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"classes": [], "posts": [], "topics": [], "users": []}
    
    def _save_data(self, data):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    # ADD THESE SYLLABUS METHODS
    def create_syllabus(self, class_id: int, title: str, content: str, author: str) -> Optional[Dict]:
        """Create or update syllabus for a class"""
        data = self._load_data()
        
        # Check if syllabus already exists for this class
        syllabus_list = data.setdefault("syllabus", [])
        existing_syllabus = next((s for s in syllabus_list if s.get("class_id") == class_id), None)
        
        if existing_syllabus:
            # Update existing syllabus
            existing_syllabus.update({
                "title": title,
                "content": content,
                "author": author,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Keep full format for parsing
            })
        else:
            # Create new syllabus
            new_syllabus = {
                "id": len(syllabus_list) + 1,
                "class_id": class_id,
                "title": title,
                "content": content,
                "author": author,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Keep full format for parsing
            }
            syllabus_list.append(new_syllabus)
        
        self._save_data(data)
        return self.get_syllabus_by_class_id(class_id)
        
    def get_syllabus_by_class_id(self, class_id: int) -> Optional[Dict]:
        """Get syllabus for a specific class"""
        data = self._load_data()
        syllabus_list = data.get("syllabus", [])
        return next((s for s in syllabus_list if s.get("class_id") == class_id), None)
    
    def update_syllabus(self, class_id: int, updates: Dict) -> bool:
        """Update syllabus for a class"""
        data = self._load_data()
        syllabus_list = data.get("syllabus", [])
        
        for syllabus in syllabus_list:
            if syllabus.get("class_id") == class_id:
                syllabus.update(updates)
                syllabus["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Keep full format for parsing
                self._save_data(data)
                return True
        
        return False
    
    
    def get_posts_by_class_id(self, class_id: int) -> List[Dict]:
        """Get all posts for a specific class"""
        data = self._load_data()
        return [post for post in data.get("posts", []) 
                if post.get("class_id") == class_id]
    
    def get_posts_by_filters(self, class_id: int, filter_type: Optional[str] = None, 
                           topic_name: Optional[str] = None) -> List[Dict]:
        """Get posts with optional filters for type and topic"""
        data = self._load_data()
        posts = [post for post in data.get("posts", []) 
                if post.get("class_id") == class_id]
        
        # Apply type filter
        if filter_type:
            posts = [p for p in posts if p.get("type") == filter_type]
        
        # Apply topic filter
        if topic_name and topic_name != "All":
            # Get topic ID from topic name
            topics = data.get("topics", [])
            topic = next((t for t in topics if t.get("title") == topic_name), None)
            if topic:
                topic_id = topic.get("id")
                posts = [p for p in posts if p.get("topic_id") == topic_id]
        
        return posts
    
    # COMMENT OUT OLD METHODS- will be implemented when upload forms are functional
    # def create_post(self, class_id: int, title: str, content: str, type_: str,
    #                author: str, topic_name: Optional[str] = None) -> Optional[Dict]:
    #     """Create a new post"""
    #     data = self._load_data()
        
    #     # Get next post ID
    #     posts = data.get("posts", [])
    #     next_id = max([p.get("id", 0) for p in posts], default=0) + 1
        
    #     # Get topic ID if topic name provided
    #     topic_id = None
    #     if topic_name:
    #         topics = data.get("topics", [])
    #         topic = next((t for t in topics if t.get("title") == topic_name and 
    #                      t.get("class_id") == class_id), None)
    #         if topic:
    #             topic_id = topic.get("id")
        
    #     # Create post data
    #     new_post = {
    #         "id": next_id,
    #         "class_id": class_id,
    #         "topic_id": topic_id,
    #         "title": title,
    #         "content": content,
    #         "type": type_,
    #         "author": author,
    #         "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #         "attachment": None,
    #         "score": None
    #     }
        
    #     # Add to posts
    #     data.setdefault("posts", []).append(new_post)
    #     self._save_data(data)
        
    #     return new_post
    
    # def update_post(self, post_id: int, updates: Dict) -> bool:
    #     """Update an existing post"""
    #     data = self._load_data()
        
    #     for post in data.get("posts", []):
    #         if post.get("id") == post_id:
    #             post.update(updates)
    #             self._save_data(data)
    #             return True
        
    #     return False
    
    # In post_service.py - update the delete_post method
    # In post_service.py - update the delete_post method
    def delete_post(self, post_id: int) -> bool:
        """Delete a post - FIXED to handle different ID fields"""
        data = self._load_data()
        
        posts = data.get("posts", [])
        initial_count = len(posts)
        
        # FIXED: Check multiple ID fields and handle duplicates
        posts_to_keep = []
        deleted = False
        
        for post in posts:
            # Check all possible ID fields
            if (post.get("id") == post_id or 
                post.get("post_id") == post_id):
                # Skip this post (delete it)
                deleted = True
                print(f"DEBUG: Deleting post - ID: {post_id}, Title: {post.get('title')}")
                continue
            posts_to_keep.append(post)
        
        if deleted:
            data["posts"] = posts_to_keep
            self._save_data(data)
            print(f"DEBUG: Successfully deleted post with ID: {post_id}")
            return True
        
        print(f"DEBUG: Could not find post with ID: {post_id}")
        print(f"DEBUG: Available posts and their IDs:")
        for i, post in enumerate(posts):
            print(f"  {i}: id={post.get('id')}, post_id={post.get('post_id')}, title={post.get('title')}")
        return False
    
    # Add this method to PostService class
    def delete_syllabus(self, class_id: int) -> bool:
        """Delete syllabus for a class"""
        data = self._load_data()
        
        syllabus_list = data.get("syllabus", [])
        initial_count = len(syllabus_list)
        
        # Remove syllabus for this class
        data["syllabus"] = [s for s in syllabus_list if s.get("class_id") != class_id]
        
        if len(data["syllabus"]) < initial_count:
            self._save_data(data)
            print(f"DEBUG: Successfully deleted syllabus for class_id: {class_id}")
            return True
        
        print(f"DEBUG: Could not find syllabus for class_id: {class_id}")
        return False
    
    # def get_post_by_id(self, post_id: int) -> Optional[Dict]:
    #     """Get a specific post by ID"""
    #     data = self._load_data()
        
    #     for post in data.get("posts", []):
    #         if post.get("id") == post_id:
    #             return post
        
    #     return None
    
    def get_posts_by_class_id(self, class_id: int) -> List[Dict]:
        """Get all posts for a specific class, sorted by date (newest first)"""
        data = self._load_data()
        posts = [post for post in data.get("posts", []) 
                if post.get("class_id") == class_id]
        
        # Sort posts by date in descending order (newest first)
        posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return posts
    
    def get_posts_by_filters(self, class_id: int, filter_type: Optional[str] = None, 
                           topic_name: Optional[str] = None) -> List[Dict]:
        """Get posts with optional filters for type and topic, sorted by date (newest first)"""
        data = self._load_data()
        posts = [post for post in data.get("posts", []) 
                if post.get("class_id") == class_id]
        
        # Apply type filter
        if filter_type:
            posts = [p for p in posts if p.get("type") == filter_type]
        
        # Apply topic filter
        if topic_name and topic_name != "All":
            # Get topic ID from topic name
            topics = data.get("topics", [])
            topic = next((t for t in topics if t.get("title") == topic_name), None)
            if topic:
                topic_id = topic.get("id")
                posts = [p for p in posts if p.get("topic_id") == topic_id]
        
        # Sort posts by date in descending order (newest first)
        posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return posts
    
    # Add this method to post_service.py
    def debug_print_posts(self, class_id: int):
        """Debug method to print all posts for a class"""
        data = self._load_data()
        posts = [post for post in data.get("posts", []) 
                if post.get("class_id") == class_id]
        
        print(f"DEBUG: Posts for class_id {class_id}:")
        for i, post in enumerate(posts):
            print(f"  {i}: id={post.get('id')}, post_id={post.get('post_id')}, title='{post.get('title')}'")
        return posts
        