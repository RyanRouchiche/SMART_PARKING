import os
import sys
import django

# Add the project root directory to the Python module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')
django.setup()

from django.conf import settings

def test():
    print(f"BASE_DIR: {settings.BASE_DIR}")

test()