# scripts/editor_utils.py

import subprocess
import json
import re
from pathlib import Path

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

def sanitize_json_output(text: str) -> str:
    # Extract raw JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in output.")
    json_text = match.group()

    # Fix common issues
    json_text = re.sub(r'([{\[,])\s*(\w+)\s*:', r'\1 "\2":', json_text)  # Quote unquoted keys
    json_text = re.sub(r':\s*([a-zA-Z_][^"\[{,}\n]*)', r': "\1"', json_text)  # Quote unquoted string values
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)  # Remove trailing commas

    return json_text

def generate_editor_profile(editor_name: str, topic: str, output_folder: Path):
    prompt_template = load_prompt_template("editor_profile_prompt.txt")
    prompt = prompt_template.replace("{{editor_name}}", editor_name).replace("{{topic}}", topic)
    result = run_ollama_prompt(prompt)

    try:
        json_text = sanitize_json_output(result)
        profile = json.loads(json_text)

        # Flatten nested fields
        flatten_fields(profile, ["background", "tone", "avatar_prompt"])
        profile["raw_profile"] = result.strip()

    except Exception as e:
        print(f"❌ Failed to parse JSON for {editor_name}: {e}")
        print("Raw output:\n", result)
        return

    output_folder.mkdir(parents=True, exist_ok=True)
    profile_path = output_folder / f"{editor_name.replace(' ', '_').lower()}.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"✅ Saved profile for {editor_name}")
