import os
import json
import subprocess
import random
from datetime import datetime
from pathlib import Path

# --- CONFIG ---
OLLAMA_MODEL = "llama3"
BASE_DIR = Path(__file__).resolve().parent.parent
BLOGS_DIR = BASE_DIR / "blogs"
PROMPTS_DIR = BASE_DIR / "models" / "prompts"

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

def load_editors(blog_path: Path) -> list:
    editors_path = blog_path / "editors"
    return [json.load(open(editors_path / f)) for f in os.listdir(editors_path) if f.endswith(".json")]

def get_article_topics(site_topic: str, num_articles: int = 5) -> list:
    # Optionally replace this with dynamic topic generation
    return [f"Deep dive into {site_topic} #{i+1}" for i in range(num_articles)]

def generate_article(blog_path: Path, editor: dict, article_topic: str, tags: list):
    prompt_template = load_prompt_template("article_prompt.txt")

    prompt = prompt_template.replace("{{editor_name}}", editor["name"])
    prompt = prompt.replace("{{site_name}}", blog_path.name.replace("_", " "))
    prompt = prompt.replace("{{topic}}", editor["topic"])
    prompt = prompt.replace("{{editor_tone}}", editor.get("tone", "Neutral"))
    prompt = prompt.replace("{{editor_background}}", editor.get("background", ""))
    prompt = prompt.replace("{{date}}", datetime.now().strftime('%Y-%m-%d'))
    prompt = prompt.replace("{{comma_separated_tags}}", ", ".join(tags))
    prompt = prompt.replace("{{avatar_filename}}", editor["name"].replace(" ", "_").lower() + ".png")
    prompt = prompt.replace("{{article_topic}}", article_topic)

    result = run_ollama_prompt(prompt)

    # Save to articles folder
    articles_path = blog_path / "articles"
    articles_path.mkdir(parents=True, exist_ok=True)
    slug = article_topic.lower().replace(" ", "-").replace("#", "")
    filename = f"{editor['name'].replace(' ', '_').lower()}_{slug}.md"
    with open(articles_path / filename, "w") as f:
        f.write(result)

    print(f"✅ Article saved: {filename}")

# --- RUN ---
if __name__ == "__main__":
    # Get most recent blog folder
    all_blogs = sorted(BLOGS_DIR.iterdir(), key=os.path.getmtime, reverse=True)
    if not all_blogs:
        print("❌ No blog directories found.")
        exit(1)

    blog_path = all_blogs[0]
    print(f"📂 Using blog: {blog_path.name}")

    # Load editors
    editors = load_editors(blog_path)
    tags = []
    try:
        with open(BASE_DIR / "registry" / "blogs_registry.json") as f:
            registry = json.load(f)
            for entry in registry:
                if entry["site_name"].replace(" ", "_").lower() == blog_path.name:
                    tags = entry.get("tags", [])
                    break
    except:
        pass

    # Generate topics and articles
    article_topics = get_article_topics(editors[0]['topic'], num_articles=7)
    for i, editor in enumerate(editors):
        topic = article_topics[i % len(article_topics)]
        generate_article(blog_path, editor, topic, tags)
