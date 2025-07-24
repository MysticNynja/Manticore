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
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.decode()

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

def generate_editor_profile(editor_name: str, topic: str, output_folder: Path):
    prompt_template = load_prompt_template("editor_profile_prompt.txt")
    prompt = prompt_template.replace("{{editor_name}}", editor_name).replace("{{topic}}", topic)
    result = run_ollama_prompt(prompt)

    try:
        # Extract first JSON object from model output
        json_text = re.search(r"\{.*\}", result, re.DOTALL).group()
        profile = json.loads(json_text)

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


