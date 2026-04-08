import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    id: str
    name: str
    description: str
    author: str
    system_prompt: str
    tags: list[str] = field(default_factory=list)
    avatar: str = ""
    image: str = ""


class SkillLoader:
    """Scan the skills directory and load all valid skills."""

    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = skills_dir or Path(__file__).parent
        self._skills: dict[str, Skill] = {}
        self._load_all()

    def _load_all(self):
        for child in sorted(self.skills_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            manifest = child / "skill.json"
            prompt_file = child / "prompt.md"
            if not manifest.exists() or not prompt_file.exists():
                continue
            meta = json.loads(manifest.read_text(encoding="utf-8"))
            system_prompt = prompt_file.read_text(encoding="utf-8")

            # Append reference files if any
            refs_dir = child / "references"
            if refs_dir.is_dir():
                ref_parts = []
                for ref in sorted(refs_dir.iterdir()):
                    if ref.is_file() and ref.suffix == ".md":
                        ref_parts.append(
                            f"\n\n---\n## 参考资料: {ref.stem}\n\n{ref.read_text(encoding='utf-8')}"
                        )
                if ref_parts:
                    system_prompt += "\n".join(ref_parts)

            # Resolve image path to API URL
            image = meta.get("image", "")
            if image and not image.startswith("http"):
                image = f"/api/skills/{child.name}/assets/{image}"

            skill = Skill(
                id=child.name,
                name=meta.get("name", child.name),
                description=meta.get("description", ""),
                author=meta.get("author", ""),
                tags=meta.get("tags", []),
                avatar=meta.get("avatar", ""),
                image=image,
                system_prompt=system_prompt,
            )
            self._skills[skill.id] = skill

    def list_skills(self) -> list[dict]:
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "author": s.author,
                "tags": s.tags,
                "avatar": s.avatar,
                "image": s.image,
            }
            for s in self._skills.values()
        ]

    def get_skill(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def reload(self):
        self._skills.clear()
        self._load_all()
