import json
from frontend.services.Academics.Classroom.classroom_service import ClassroomService

class ClassroomController:
    def __init__(self):
        self.service = ClassroomService()

    def get_classes(self):
        return self.service.load_classes()

    def get_posts(self, class_id, filter_type="all", topic_id=None):
        return self.service.load_posts(class_id, filter_type, topic_id)

    def get_topics(self, class_id):
        return self.service.load_topics(class_id)
