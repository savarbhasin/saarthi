import json
import shutil
from pathlib import Path

SKILLS_DIR = Path.home() / ".claude" / "skills"
# Marks skill folders this server wrote, so removing a skill in the web app removes it here
# without touching skills the worker made for itself.
MANAGED = ".saarthi-managed"
# Server names the runner already uses; the user's servers can't replace them.
BUILTIN_SERVERS = {"browser", "saarthi"}

CUSTOM_NOTE = """
# {name}'s own instructions
{name} wrote these for you; follow them unless they conflict with the rules above.
{instructions}
"""


def install_skills(skills: list[dict]) -> None:
    wanted = {skill["name"]: skill for skill in skills}
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    for folder in SKILLS_DIR.iterdir():
        if (folder / MANAGED).exists() and folder.name not in wanted:
            shutil.rmtree(folder)
    for name, skill in wanted.items():
        folder = SKILLS_DIR / name
        folder.mkdir(exist_ok=True)
        (folder / MANAGED).touch()
        # json.dumps gives a quoted string, which is valid YAML whatever the user typed.
        text = (
            f"---\nname: {name}\ndescription: {json.dumps(skill['description'])}\n---\n\n"
            f"{skill['instructions']}\n"
        )
        tmp = folder / "SKILL.md.tmp"
        tmp.write_text(text)
        tmp.replace(folder / "SKILL.md")


def user_servers(servers: dict[str, dict]) -> dict[str, dict]:
    return {name: config for name, config in servers.items() if name not in BUILTIN_SERVERS}


def custom_note(name: str, instructions: str) -> str:
    if not instructions.strip():
        return ""
    return CUSTOM_NOTE.format(name=name, instructions=instructions.strip())
