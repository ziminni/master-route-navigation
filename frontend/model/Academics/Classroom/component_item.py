
class ComponentItem:
    """Represents a single grading component"""
    def __init__(self, name: str, percentage: int, component_id: int = None):
        self.id = component_id
        self.name = name
        self.percentage = percentage
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'percentage': self.percentage
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get('name', ''),
            percentage=data.get('percentage', 0),
            component_id=data.get('id')
        )