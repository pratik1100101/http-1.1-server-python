import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Determine the project root dynamically
# os.path.dirname(__file__) is 'C:\Code\HTTP 1.1 Server - Python\tests'
# os.path.abspath(os.path.join(..., os.pardir)) goes up one level to 'C:\Code\HTTP 1.1 Server - Python'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# --- CRITICAL FIX: Add project root to sys.path ---
# Insert at the beginning so 'src' is found before other paths if conflicts exist
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ----------------------------------------------------
