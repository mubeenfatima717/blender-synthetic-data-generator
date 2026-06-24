bl_info = {
    "name": "SynthGen Pro",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > SynthGen Tab",
    "description": "Professional Synthetic Data Generator for AI Training",
    "category": "Pipeline",
}

import bpy
from . import ui
from .utils import license_check

def register():
    # 1. Check if the environment is safe to run
    if not license_check.check_dependencies():
        print("SynthGen Error: Missing Dependencies.")
        return

    # 2. Check License
    if not license_check.verify_active_license():
        print("SynthGen Error: Invalid License.")
        return

    # 3. Register the UI and Operators
    ui.register()
    print("SynthGen Pro Registered Successfully.")

def unregister():
    # Unregister the UI
    ui.unregister()
    print("SynthGen Pro Unregistered.")

if __name__ == "__main__":
    register()