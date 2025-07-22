import os
import json
from pathlib import Path
import subprocess

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent
BLOGS_DIR = BASE_DIR / "blogs"
PROMPT_TEMPLATE_PATH = BASE_DIR / "models" / "prompts" / "site_prompt.txt"
OLLAMA_MODEL = "llama3"

# --- Helper Functions ---

def run_ollama(prompt: str) -> str:
    """Call Ollama CLI and return the response."""
    print("[+] Running Ollama with prompt:\n", prompt)
    result = subprocess.run([
        "ollama", "run", OLLAMA_MODEL
    ], input=prompt.encode(), stdout=subprocess.PIPE)
    return result.stdout.decode()

def sanitize_name(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-")

def create_blog_structure(site_name: str):
    slug = sanitize_name(site_name)
    blog_path = BLOGS_DIR / slug
    (blog_path / "editors").mkdir(parents=True, exist_ok=True)
    (blog_path / "articles").mkdir(exist_ok=True)
    (blog_path / "images").mkdir(exist_ok=True)
    (blog_path / "site").mkdir(exist_ok=True)
    return blog_path

# --- Main Function ---

def generate_site(site_name: str, editor_names: list[str], topic: str):
    print(f"[+] Generating site: {site_name}")
    blog_path = create_blog_structure(site_name)

    # Load prompt template
    with open(PROMPT_TEMPLATE_PATH, "r") as f:
        template = f.read()

    # Prepare prompt for Ollama
    prompt = template.replace("{{site_name}}", site_name)
    prompt = prompt.replace("{{topic}}", topic)
    prompt = prompt.replace("{{editors}}", ", ".join(editor_names))

    # Run prompt through Ollama
    response = run_ollama(prompt)

    # Save response as config
    config_path = blog_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "site_name": site_name,
            "topic": topic,
            "editors": editor_names,
            "response": response.strip()
        }, f, indent=2)

    print(f"[+] Site '{site_name}' created at {blog_path}")
    return blog_path

# --- Entry Point ---

if __name__ == "__main__":
    # Example usage
    site_name = "Garden Tech Weekly"
    editors = ["Sam", "Jerome", "Nicholas"]
    topic = "modern gardening technology"

    generate_site(site_name, editors, topic)
