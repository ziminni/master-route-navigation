from .component_item import ComponentItem

class TermRubric:
    """Represents rubric for a single term"""
    def __init__(self, term_name: str, term_percentage: int):
        self.term_name = term_name
        self.term_percentage = term_percentage
        self.components = []
    
    def add_component(self, component: ComponentItem):
        self.components.append(component)
    
    def remove_component(self, index: int):
        if 0 <= index < len(self.components):
            del self.components[index]
    
    def update_component(self, index: int, name: str, percentage: int):
        if 0 <= index < len(self.components):
            self.components[index].name = name
            self.components[index].percentage = percentage
    
    def get_total_percentage(self):
        return sum(c.percentage for c in self.components)
    
    def is_valid(self):
        return self.get_total_percentage() == 100
    
    def to_dict(self):
        return {
            'term_name': self.term_name,
            'term_percentage': self.term_percentage,
            'components': [c.to_dict() for c in self.components]
        }
    
    @classmethod
    def from_dict(cls, data):
        rubric = cls(
            term_name=data.get('term_name', ''),
            term_percentage=data.get('term_percentage', 0)
        )
        for comp_data in data.get('components', []):
            rubric.add_component(ComponentItem.from_dict(comp_data))
        return rubric