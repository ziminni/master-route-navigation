# ClassroomWrapper.py
import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import using the full path that includes 'frontend'
from frontend.views.Academics.TaggingMain import TaggingMain

# Re-export the class
TaggingMain = TaggingMain