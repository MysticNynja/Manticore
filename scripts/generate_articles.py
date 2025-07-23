import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
OLLAMA_MODEL = "llama3"
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "models" / "prompts"
BLOGS_DIR = BASE_DIR / "blogs"

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

def get_article_topics_dynamic(topic: str, num_articles: int = 5) -> list:
    prompt_template = load_prompt_template("article_topic_ideas_prompt.txt")
    prompt = prompt_template.replace("{{topic}}", topic).replace("{{num_articles}}", str(num_articles))

    response = run_ollama_prompt(prompt)

    try:
        data = json.loads(re.search(r'\{.*\}', response, re.DOTALL).group())
        return data.get("article_ideas", [])
    except Exception as e:
        print("⚠️ Failed to parse dynamic article topics. Falling back to generic ones.")
        return [f"A unique angle on {topic} #{i+1}" for i in range(num_articles)]

def generate_article_prompt(site_name, topic, editor, article_topic, date_str, tags):
    profile_path = BLOGS_DIR / site_name / "editors" / f"{editor.replace(' ', '_').lower()}.json"
    if not profile_path.exists():
        print(f"❌ Editor profile not found: {profile_path}")
        return None

    with open(profile_path) as f:
        profile = json.load(f)

    prompt_template = load_prompt_template("article_prompt.txt")
    prompt = prompt_template.replace("{{editor_name}}", editor)
    prompt = prompt.replace("{{site_name}}", site_name.replace('_', ' ').title())
    prompt = prompt.replace("{{topic}}", topic)
    prompt = prompt.replace("{{editor_tone}}", profile.get("tone", ""))
    prompt = prompt.replace("{{editor_background}}", profile.get("background", ""))
    prompt = prompt.replace("{{date}}", date_str)
    prompt = prompt.replace("{{comma_separated_tags}}", ", ".join(tags))
    prompt = prompt.replace("{{avatar_filename}}", f"{editor.replace(' ', '_').lower()}.png")
    prompt = prompt.replace("{{article_topic}}", article_topic)

    return prompt

def generate_articles(site_name: str, topic: str, editors: list, tags: list):
    blog_dir = BLOGS_DIR / site_name
    articles_dir = blog_dir / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"💡 Generating article topics for: {topic}")
    article_topics = get_article_topics_dynamic(topic, num_articles=len(editors))

    for i, editor in enumerate(editors):
        article_topic = article_topics[i % len(article_topics)]
        prompt = generate_article_prompt(site_name, topic, editor, article_topic, date_str, tags)

        if not prompt:
            continue

        print(f"✍️ Generating article by {editor} on: {article_topic}")
        result = run_ollama_prompt(prompt)
        filename = articles_dir / f"{editor.replace(' ', '_').lower()}_{date_str}.md"

        with open(filename, "w") as f:
            f.write(result)

        print(f"✅ Article saved to {filename}")

# --- RUN ---
if __name__ == "__main__":
    example_site = "virtual_event_design_for_mental_wellness"
    example_topic = "Virtual Events and Mental Health"
    example_editors = ["Ava Satori", "Dante Wells"]
    example_tags = ["virtual events", "mental health", "wellness"]

    generate_articles(example_site, example_topic, example_editors, example_tags)
