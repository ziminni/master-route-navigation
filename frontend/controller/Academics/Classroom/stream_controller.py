# # stream_controller.py (refactored)
# from typing import List, Dict
# from frontend.services.stream_service import StreamService

# class StreamController:
#     def __init__(self, service: StreamService):
#         """Initialize with dependency injection."""
#         self.service = service
#         self.current_class_id = None
    
#     def set_class(self, class_id: int) -> None:
#         """Set the current class context."""
#         self.current_class_id = class_id
    
#     def get_posts(self) -> List[Dict]:
#         """Get posts for current class."""
#         if self.current_class_id is None:
#             return []
#         return self.service.get_posts_by_class_id(self.current_class_id)
    
#     def create_post(self, title: str, content: str, author: str) -> bool:
#         """Create a new post in the stream."""
#         if self.current_class_id is None:
#             return False
        
#         post_data = {
#             "title": title,
#             "content": content,
#             "author": author
#         }
        
#         return self.service.add_post(self.current_class_id, post_data)