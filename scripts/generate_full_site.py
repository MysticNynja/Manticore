import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
OLLAMA_MODEL = "llama3"
BASE_DIR = Path(__file__).resolve().parent.parent
BLOGS_DIR = BASE_DIR / "blogs"
PROMPTS_DIR = BASE_DIR / "models" / "prompts"
REGISTRY_FILE = BASE_DIR / "registry" / "blogs_registry.json"

# --- HELPERS ---
def run_ollama_prompt(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.decode()

def load_prompt_template(name: str) -> str:
    with open(PROMPTS_DIR / name, "r") as f:
        return f.read()

def save_registry_entry(site_name: str, topic: str):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
    else:
        registry = []
    registry.append({"site_name": site_name, "topic": topic})
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def is_duplicate(site_name: str, topic: str) -> bool:
    if not REGISTRY_FILE.exists():
        return False
    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)
    for entry in registry:
        if entry["site_name"].lower() == site_name.lower() or entry["topic"].lower() == topic.lower():
            return True
    return False

# --- MAIN WORKFLOW ---
def generate_blog_idea():
    prompt = load_prompt_template("idea_prompt.txt")
    output = run_ollama_prompt(prompt)

    try:
        idea_json = json.loads(output.split("```json")[-1].split("```")[-2].strip())
    except Exception as e:
        print("Error parsing JSON from Ollama response:", e)
        print(output)
        return None

    return idea_json

def generate_site(site_name: str, topic: str, editors: list):
    prompt_template = load_prompt_template("site_prompt.txt")
    filled_prompt = prompt_template.replace("{{site_name}}", site_name)
    filled_prompt = filled_prompt.replace("{{topic}}", topic)
    filled_prompt = filled_prompt.replace("{{editors}}", json.dumps(editors))

    blog_folder = BLOGS_DIR / site_name.replace(" ", "_").lower()
    blog_folder.mkdir(parents=True, exist_ok=True)
    (blog_folder / "site.txt").write_text(filled_prompt)

    result = run_ollama_prompt(filled_prompt)
    (blog_folder / "site_generated.txt").write_text(result)
    print(f"✅ Blog '{site_name}' generated at: {blog_folder}")

# --- RUN ---
if __name__ == "__main__":
    idea = generate_blog_idea()
    if not idea:
        print("Failed to generate a blog idea.")
        exit(1)

    site_name = idea["site_name"]
    topic = idea["topic"]
    editors = idea["editors"]

    if is_duplicate(site_name, topic):
        print(f"⚠️ Duplicate blog idea: '{site_name}' / '{topic}'")
    else:
        save_registry_entry(site_name, topic)
        generate_site(site_name, topic, editors)
