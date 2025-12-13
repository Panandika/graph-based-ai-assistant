import os
import sys

sys.path.append(os.getcwd())

from app.main import app

print("Listing all registered routes:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.methods} {route.path}")
    else:
        print(f"Mounted: {route.path}")
