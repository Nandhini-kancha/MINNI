import os
import sys

# Ensure project root is on sys.path for Netlify Serverless Functions
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mangum import Mangum
from app.main import app

# Handler function exported for Netlify AWS Lambda environment
handler = Mangum(app, api_gateway_base_path="/.netlify/functions/api")
