import json
from pathlib import Path
from generate_site import generate_editor_profile  # Assuming it's in the same module

BASE_DIR = Path(__file__).resolve().parent.parent
BLOGS_DIR = BASE_DIR / "blogs"

if __name__ == "__main__":
    site_name = "virtual_event_design_for_mental_wellness"
    topic = "Virtual Events and Mental Health"
    editors = ["Ava Satori", "Dante Wells"]

    editors_folder = BLOGS_DIR / site_name / "editors"
    for editor in editors:
        print(f"🧠 Generating profile for {editor}")
        generate_editor_profile(editor, topic, editors_folder)
