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

def parse_editor_profile(raw_profile: str) -> dict:
    background_match = re.search(r"(?i)(background|story)[\s:.-]*(.*?)(?=tone of voice|writing style|avatar|$)", raw_profile, re.DOTALL)
    tone_match = re.search(r"(?i)(tone of voice|writing style)[\s:.-]*(.*?)(?=avatar|$)", raw_profile, re.DOTALL)
    avatar_match = re.search(r"(?i)(avatar prompt|visual description)[\s:.-]*(.*)$", raw_profile, re.DOTALL)

    return {
        "background": background_match.group(2).strip() if background_match else "",
        "tone": tone_match.group(2).strip() if tone_match else "",
        "avatar_prompt": avatar_match.group(2).strip() if avatar_match else "",
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
