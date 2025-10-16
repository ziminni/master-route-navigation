import json

class ClassroomService:
    def __init__(self):
        self.data_file = "services/Academics/data/classroom_data.json"
        self.load_data()

    def load_data(self):
        with open(self.data_file, "r") as f:
            self.data = json.load(f)

    def load_classes(self):
        self.load_data()
        return self.data["classes"]

    def load_topics(self, class_id):
        return [t for t in self.data["topics"] if t["class_id"] == class_id]

    def load_posts(self, class_id, filter_type="all", topic_id=None):
        posts = [p for p in self.data["posts"] if p["class_id"] == class_id]
        if filter_type != "all":
            posts = [p for p in posts if p["type"] == filter_type]
        if topic_id is not None:
            posts = [p for p in posts if p["topic_id"] == topic_id]
        return posts