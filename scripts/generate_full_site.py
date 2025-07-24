import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from generate_articles import generate_articles
from generate_editor import generate_editor_profile
from editor_utils import generate_editor_profile

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

def generate_blog_idea():
    prompt_template = load_prompt_template("idea_prompt.txt")
    response = run_ollama_prompt(prompt_template)

    try:
        matches = re.findall(r'\{.*?\}', response, re.DOTALL)
        idea_json = json.loads(matches[0]) if matches else {}
        return idea_json
    except Exception as e:
        print("Error parsing JSON from Ollama response:", e)
        print(response)
        return None

def save_registry_entry(site_name: str, topic: str, tags: list = []):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r") as f:
                registry = json.load(f)
        except json.JSONDecodeError:
            registry = []
    else:
        registry = []
    registry.append({"site_name": site_name, "topic": topic, "tags": tags})
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def is_duplicate(site_name: str, topic: str) -> bool:
    if not REGISTRY_FILE.exists():
        return False
    try:
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
    except json.JSONDecodeError:
        return False
    for entry in registry:
        if entry["site_name"].lower() == site_name.lower() or entry["topic"].lower() == topic.lower():
            return True
    return False

def parse_editor_profile(raw_profile: str) -> dict:
    background_match = re.search(
        r"(?:background|1\.\s*A short background:)[\s:.-]*([\s\S]*?)(?=2\.|tone of voice|writing style|avatar|$)",
        raw_profile, re.IGNORECASE
    )

    tone_match = re.search(
        r"(?:tone of voice and writing style|tone-wise|2\.\s*tone)[\s:.-]*([\s\S]*?)(?=3\.|avatar|$)",
        raw_profile, re.IGNORECASE
    )

    avatar_match = re.search(
        r"(?:avatar prompt|visual description|4\.\s*avatar)[\s:.-]*([\s\S]*?)$",
        raw_profile, re.IGNORECASE
    )

    return {
        "background": background_match.group(1).strip() if background_match else "",
        "tone": tone_match.group(1).strip() if tone_match else "",
        "avatar_prompt": avatar_match.group(1).strip() if avatar_match else "",
        "raw_profile": raw_profile.strip()
    }


def generate_editor_profile(editor_name: str, topic: str, output_folder: Path):
    prompt_template = load_prompt_template("editor_profile_prompt.txt")
    prompt = prompt_template.replace("{{editor_name}}", editor_name).replace("{{topic}}", topic)
    result = run_ollama_prompt(prompt)
    parsed = parse_editor_profile(result)

    editor_data = {
        "name": editor_name,
        "topic": topic,
        "background": parsed["background"],
        "tone": parsed["tone"],
        "avatar_prompt": parsed["avatar_prompt"],
        "raw_profile": parsed["raw_profile"]
    }

    output_folder.mkdir(parents=True, exist_ok=True)
    profile_path = output_folder / f"{editor_name.replace(' ', '_').lower()}.json"
    with open(profile_path, "w") as f:
        json.dump(editor_data, f, indent=2)

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

    # Generate profiles for each editor
    editors_folder = blog_folder / "editors"
    for editor in editors:
        generate_editor_profile(editor_name=editor, topic=topic, output_folder=editors_folder)

# --- RUN ---
if __name__ == "__main__":
    idea = generate_blog_idea()
    if not idea:
        print("Failed to generate a blog idea.")
        exit(1)

    site_name = idea["site_name"]
    topic = idea["topic"]
    tags = idea.get("tags", [])

    # Clean editor names to remove titles like "Dr.", "Mr.", etc.
    raw_editors = idea["editors"]
    editors = [
        re.sub(r"^(Dr\\.|Mr\\.|Mrs\\.|Ms\\.|Prof\\.)\\s+", "", name.strip(), flags=re.IGNORECASE)
        for name in raw_editors
    ]

    if is_duplicate(site_name, topic):
        print(f"⚠️ Duplicate blog idea: '{site_name}' / '{topic}'")
    else:
        save_registry_entry(site_name, topic, tags)
        generate_site(site_name, topic, editors)

        # Generate articles for the new site
        normalized_site_name = site_name.replace(" ", "_").lower()
        generate_articles(normalized_site_name, topic, editors, tags)
