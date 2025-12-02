"""
Grade Item data structure
"""

class GradeItem:
    def __init__(self):
        self.value = ""
        self.is_draft = True
    
    def get_numeric_score(self):
        """Get numeric score percentage from value like '35/40'"""
        if not self.value or '/' not in self.value:
            return 0.0
        
        try:
            parts = self.value.split('/')
            score = float(parts[0])
            max_score = float(parts[1])
            if max_score > 0:
                return (score / max_score) * 100
        except (ValueError, IndexError, ZeroDivisionError):
            pass
        
        return 0.0