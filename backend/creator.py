"""Skill creator powered by the Nuwa methodology."""

import json
import re
from pathlib import Path


SKILLS_DIR = Path(__file__).parent / "skills"
NUWA_DIR = Path(__file__).parent / "nuwa"


def _load_nuwa_prompt() -> str:
    """Build the system prompt for skill creation."""
    template = (NUWA_DIR / "skill-template.md").read_text(encoding="utf-8")
    framework = (NUWA_DIR / "extraction-framework.md").read_text(encoding="utf-8")

    return f"""你是「女娲 · Skill造人术」——一个将任何人物的认知框架蒸馏为可运行思维操作系统的引擎。

## 你的任务

用户会给你一个人物名称。你需要基于你对这个人的知识，生成一份完整的人物 Skill 文件（prompt.md）。

## 方法论

### 提炼框架
{framework}

### 输出模板
{template}

## 关键要求

1. **输出格式**：直接输出完整的 SKILL.md 内容（markdown格式），不要加任何前缀说明
2. **质量标准**：
   - 3-7个心智模型，每个有跨领域证据、应用方法、局限
   - 5-10条决策启发式，有具体案例
   - 完整的表达DNA（句式、词汇、节奏、幽默、确定性）
   - 身份卡用第一人称，50字自我介绍
   - 诚实边界：明确标注做不到什么
3. **矛盾是特征**：保留内在张力，不强行统一
4. **角色扮演规则**必须放在最前面
5. **不要**在开头加"以下是..."之类的说明，直接输出markdown内容
6. **表达DNA要有辨识度**：删掉名字后还能认出是谁
7. **Frontmatter**必须包含 name 和 description 字段

## 语言

- 如果人物是中国人或华语圈人物，用中文输出
- 其他人物也用中文输出（因为用户群体是中文用户）
"""


def build_user_message(person_name: str, extra_context: str = "") -> str:
    msg = f"请为「{person_name}」生成完整的人物 Skill。"
    if extra_context:
        msg += f"\n\n补充信息：{extra_context}"
    return msg


def slugify(name: str) -> str:
    """Convert a person name to a directory-safe slug."""
    # Try to use ASCII for common names
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = slug.strip('-')
    return slug or "new-skill"


async def create_skill_streaming(provider, person_name: str, extra_context: str = ""):
    """Stream the skill creation and save the result when done."""
    system_prompt = _load_nuwa_prompt()
    user_msg = build_user_message(person_name, extra_context)
    messages = [{"role": "user", "content": user_msg}]

    skill_id = slugify(person_name)
    skill_dir = SKILLS_DIR / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "assets").mkdir(exist_ok=True)

    full_content = []

    async for chunk in provider.stream_chat(system_prompt, messages):
        full_content.append(chunk)
        yield chunk

    # Save the generated content
    content = "".join(full_content)

    # Strip markdown code fences if the model wrapped it
    content = re.sub(r'^```(?:markdown)?\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)

    (skill_dir / "prompt.md").write_text(content, encoding="utf-8")

    # Extract name and description from frontmatter if present
    name = person_name
    description = f"{person_name}的思维框架与行为逻辑"
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        name_match = re.search(r'name:\s*(.+)', fm)
        if name_match:
            raw = name_match.group(1).strip()
            # Use person_name for display, keep raw for id
        desc_match = re.search(r'description:\s*\|?\s*\n?\s*(.+)', fm)
        if desc_match:
            description = desc_match.group(1).strip()[:120]

    # Create skill.json
    meta = {
        "name": person_name,
        "description": description,
        "tags": ["generated"],
        "avatar": "",
        "image": "",
    }
    (skill_dir / "skill.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    yield f"\n\n<!-- SKILL_CREATED:{skill_id} -->"
