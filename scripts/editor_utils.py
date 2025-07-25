# scripts/editor_utils.py

import subprocess
import json
import re
from pathlib import Path
import unicodedata

OLLAMA_MODEL = "llama3"
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "models" / "prompts"

def run_ollama_prompt(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Handles encoding/decoding
    )
    return result.stdout

def load_prompt_template(name: str) -> str:
    with open(PROMPTS_DIR / name, "r") as f:
        return f.read()

def flatten_fields(profile: dict, keys: list):
    for key in keys:
        val = profile.get(key, "")
        if isinstance(val, dict):
            profile[key] = " ".join(str(v).strip() for v in val.values())
        elif not isinstance(val, str):
            profile[key] = str(val).strip()

import html

def clean_json_output(json_text):
    match = re.search(r'\{.*\}', json_text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON found")

    raw = match.group(0)
    # Fix boolean strings (e.g. "true" -> true)
    fixed = re.sub(r'":\s*"true"', '": true', raw)
    fixed = re.sub(r'":\s*"false"', '": false', fixed)
    return json.loads(fixed)

def sanitize_json_output(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in output.")
    json_text = match.group()

    # Remove comments
    json_text = re.sub(r'//.*', '', json_text)

    # Remove or escape control characters
    json_text = re.sub(r'[\x00-\x1F\x7F]', '', json_text)  # Control characters

    # Properly quote unquoted keys (e.g., {key: "value"})
    json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_text)

    # Fix simple unquoted values
    json_text = re.sub(r':\s*([^"\[{][^,\n}]*)', r': "\1"', json_text)

    # Remove trailing commas before } or ]
    json_text = re.sub(r',\s*([\]}])', r'\1', json_text)

    # Ensure JSON ends properly
    if not json_text.strip().endswith("}"):
        json_text += "}"

    return json_text

def slugify(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'\W+', '_', name.lower()).strip('_')


def generate_editor_profile(editor_name: str, topic: str, output_folder: Path):
    prompt_template = load_prompt_template("editor_profile_prompt.txt")
    prompt = prompt_template.replace("{{editor_name}}", editor_name).replace("{{topic}}", topic)
    result = run_ollama_prompt(prompt)

    try:
        profile = clean_json_output(result)
        flatten_fields(profile, ["background", "tone", "avatar_prompt"])
        profile["raw_profile"] = result.strip()

    except Exception as e:
        print(f"❌ Failed to parse JSON for {editor_name}: {e}")
        print("Raw output:\n", result)

        output_folder.mkdir(parents=True, exist_ok=True)
        debug_path = output_folder / f"{slugify(editor_name)}_debug.txt"
        with open(debug_path, "w") as f:
            f.write(result)
        return

    editor_slug = slugify(editor_name)
    profile_path = output_folder / f"{editor_slug}.json"

    output_folder.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"✅ Saved profile for {editor_name}")

