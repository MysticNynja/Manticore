# generate_articles.py
import os
import json
import random
import re
from pathlib import Path
from generate_site import run_ollama_prompt, load_prompt_template, BLOGS_DIR


def parse_article_response(raw_response: str) -> dict:
    try:
        matches = re.findall(r'\{.*?\}', raw_response, re.DOTALL)
        article_data = json.loads(matches[0]) if matches else {}
        return article_data
    except Exception as e:
        print("Error parsing article response:", e)
        print(raw_response)
        return {}


def generate_articles_for_editor(site_folder: Path, editor_profile: dict, topic: str):
    editor_name = editor_profile["name"]
    tone = editor_profile.get("tone", "")

    prompt_template = load_prompt_template("article_prompt.txt")

    # Random number of articles per editor
    article_count = random.randint(1, 3)
    articles_folder = site_folder / "articles" / editor_name.replace(" ", "_").lower()
    articles_folder.mkdir(parents=True, exist_ok=True)

    for i in range(article_count):
        prompt = prompt_template.replace("{{editor_name}}", editor_name)
        prompt = prompt.replace("{{topic}}", topic)
        prompt = prompt.replace("{{tone}}", tone)

        print(f"\n📝 Generating article {i + 1} for {editor_name}...")
        result = run_ollama_prompt(prompt)
        parsed = parse_article_response(result)

        if parsed:
            slug = re.sub(r'[^a-zA-Z0-9_-]', '', parsed["title"].replace(" ", "_").lower())
            out_path = articles_folder / f"{slug}.json"
            with open(out_path, "w") as f:
                json.dump(parsed, f, indent=2)
        else:
            print("❌ Failed to parse article.")


if __name__ == "__main__":
    # Discover existing blogs
    blogs = [d for d in BLOGS_DIR.iterdir() if d.is_dir() and (d / "site_generated.txt").exists()]

    print("Available Blogs:")
    for i, blog in enumerate(blogs):
        print(f"[{i}] {blog.name}")

    selected = int(input("Select a blog by number: "))
    blog_folder = blogs[selected]

    # Load topic
    with open(blog_folder / "site_generated.txt") as f:
        site_text = f.read()
    topic_match = re.search(r'Topic\s*[:\-]\s*(.+)', site_text, re.IGNORECASE)
    topic = topic_match.group(1).strip() if topic_match else "Unknown"

    # Load editors
    editors_folder = blog_folder / "editors"
    editor_files = list(editors_folder.glob("*.json"))
    for editor_file in editor_files:
        with open(editor_file) as f:
            profile = json.load(f)
            generate_articles_for_editor(blog_folder, profile, topic)

    print("\n✅ All articles generated.")
