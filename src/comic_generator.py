from __future__ import annotations
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .api_client import get_text_client, get_image_client


# === 资源加载相关 ===

def load_all_resources(project_root: str | Path) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    加载小说文本、角色图片、术语图片。

    project_root: 项目根目录（包含 data/、images/ 等）
    返回:
        novel_text: 小说原文字符串
        character_images: {角色名: 图片路径}
        term_images: {术语名: 图片路径}
    """
    root = Path(project_root)

    # 小说文本
    novel_path = root / "data" / "novel.txt"
    if not novel_path.exists():
        raise FileNotFoundError(f"找不到小说文件: {novel_path}")
    novel_text = novel_path.read_text(encoding="utf-8")

    # 角色图像
    characters_dir = root / "images" / "characters"
    character_images: Dict[str, str] = {}
    if characters_dir.exists():
        for p in characters_dir.glob("*"):
            if p.is_file():
                name = p.stem
                character_images[name] = str(p)

    # 术语图像
    terms_dir = root / "images" / "terms"
    term_images: Dict[str, str] = {}
    if terms_dir.exists():
        for p in terms_dir.glob("*"):
            if p.is_file():
                name = p.stem
                term_images[name] = str(p)

    return novel_text, character_images, term_images


# === STEP 1: 小说 -> 分镜结构（纯文字，不含图片 prompt） ===

def parse_novel_to_comic_panels(
    novel_text: str,
    character_names: list[str] | None = None,
    term_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    使用大模型把小说拆分成漫画分镜列表。

    返回的每个 panel 是一个 dict，例如：
    {
        "panel_number": 1,
        "scene_description": "...",
        "characters": ["麟奈狸", "某村民"],
        "dialogue": [
            {"character": "麟奈狸", "line": "……"},
            ...
        ],
        # 这里只生成结构，不生成 image_prompt
    }
    """
    character_names = character_names or []
    term_names = term_names or []

    text_client = get_text_client()

    prompt = f"""你是一名资深分镜师，请将以下小说内容拆解成漫画分镜。

要求：
- 输出一个 YAML list，每个元素代表一个 panel。
- 每个 panel 必须包含字段：
  - panel_number: 序号，从 1 开始
  - scene_description: 对画面内容的简要说明
  - characters: 出现在这个分镜里的角色名字列表
  - dialogue: 对话列表，每个元素是 {{character: 角色名, line: 台词}}

- 当前项目中已知角色：{character_names}
- 已知术语/重要物件：{term_names}

小说内容：
{novel_text}
"""

    yaml_string = text_client.generate_text(prompt=prompt).strip()

    # 防止模型包了一层 ```yaml ``` 代码块
    if yaml_string.startswith("```yaml"):
        yaml_string = yaml_string[len("```yaml"):].strip()
    if yaml_string.endswith("```"):
        yaml_string = yaml_string[:-3].strip()

    panels = yaml.safe_load(yaml_string)
    if not isinstance(panels, list):
        raise ValueError("模型返回的分镜数据不是 list，请检查 prompt 或输出格式。")
    return panels
from pathlib import Path
import yaml
from typing import Dict

def load_reference_images(project_root: Path) -> Dict[str, str]:
    """
    从 data/reference_images.yaml 读取人物/场景/风格参考图，
    统一拼成 { "character:麟奈狸": url, "scene:xxx": url, ... } 这样的 dict。
    """
    cfg_path = project_root / "data" / "reference_images.yaml"
    if not cfg_path.exists():
        print(f"[WARN] reference_images.yaml not found: {cfg_path}")
        return {}

    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    ref: Dict[str, str] = {}

    for name, url in (data.get("characters") or {}).items():
        ref[f"character:{name}"] = url

    for name, url in (data.get("scenes") or {}).items():
        ref[f"scene:{name}"] = url

    for name, url in (data.get("styles") or {}).items():
        ref[f"style:{name}"] = url

    return ref

# === STEP 2: 分镜 + 资源 -> 每格图片描述 ===

def generate_comic_panel_image_description(
    panel: dict[str, Any],
    character_images: Dict[str, str],
    term_images: Dict[str, str],
) -> str:
    """
    根据单个 panel + 角色图 + 术语图，生成适合喂给图像模型的详细 image prompt。
    """
    text_client = get_text_client()

    scene_description = panel.get("scene_description", "")
    characters = panel.get("characters", [])
    dialogue = panel.get("dialogue", [])

    prompt = f"""你是一名专精于由文本生成图像（Text-to-Image）的提示词工程师，擅长动漫插画风格。

请根据以下剧情信息，编写一段**适合 AI 绘画模型（如 Midjourney, Stable Diffusion）**的英文 Image Prompt：

**输入信息：**
- 场景描述 (Scene): {scene_description}
- 角色 (Characters): {characters}
- 对白 (Dialogue - 仅作情绪/氛围参考): {dialogue}
- 可参考的角色特征 (Ref): {list(character_images.keys())}
- 可参考的物品特征 (Ref): {list(term_images.keys())}

**输出要求：**
1. **格式：** 直接输出一段英文提示词，不要包含任何解释或前缀。
2. **内容结构：** (主体描述 + 动作与互动) + (环境与背景) + (光影与构图) + (强制艺术风格)。
3. **强制艺术风格 (必须包含以下关键词的语义)：**
   - **核心风格：**  Hand-painted Gouache style (水粉手绘), Cel-shading (赛璐珞).
   - **线条与质感：** Clear and sharp outlines, distinct color blocks, hard-edged shadows, no complex gradients, natural brushstrokes, rich details.
   - **色彩：** High saturation, vibrant colors, poster color aesthetic.
"""

    image_prompt = text_client.generate_text(prompt=prompt).strip()
    return image_prompt


# === STEP 3: 根据图片描述生成最终图片 ===

def generate_comic_images(
    project_root: Path,
    comic_data: List[Dict[str, Any]],
    reference_images: Dict[str, str] | None = None,
    image_output_dir_name: str = "comic_images"
) -> None:
    print("=== STEP 3: 生成漫画图片 ===")

    reference_images = reference_images or {}

    image_client = get_image_client()
    output_dir = project_root / 'output' / image_output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, panel in enumerate(comic_data):
        panel_number = panel.get('panel_number', i + 1)
        image_description = panel.get('generated_image_description')

        if not image_description:
            print(f"Skipping panel {panel_number}: No generated_image_description found.")
            continue

        # 👇 这里根据 panel 内容收集参考图
        ref_urls: list[str] = []

        # 人物参考
        for ch in panel.get("characters", []):
            key = f"character:{ch}"
            url = reference_images.get(key)
            if url:
                ref_urls.append(url)

        # 场景参考（如果你在 panel 里有 scene_tag 之类的字段）
        scene_tag = panel.get("scene_tag")
        if scene_tag:
            key = f"scene:{scene_tag}"
            url = reference_images.get(key)
            if url:
                ref_urls.append(url)

        # 全局风格（比如每一话都用同一个 style tag）
        style_tag = panel.get("style_tag", "水粉暖阳")  # 没写就用一个默认
        key = f"style:{style_tag}"
        url = reference_images.get(key)
        if url:
            ref_urls.append(url)

        image_filename = f"panel_{panel_number:03d}.png"
        output_path = output_dir / image_filename

        print(f"Generating image for panel {panel_number} using description: {image_description[:60]}...")
        try:
            image_path = image_client.generate_image(
                prompt=image_description,
                output_path=str(output_path),
                size="2048x2048",
                style="anime",
                reference_images=ref_urls  # ⭐ 关键：把参考图列表传进去
            )
            if image_path:
                print(f"Successfully generated and saved image for panel {panel_number} to {image_path}")
                panel['generated_image_path'] = str(Path(image_path).relative_to(project_root))
            else:
                print(f"Failed to generate image for panel {panel_number}. Image client returned None.")
        except Exception as e:
            print(f"Error generating image for panel {panel_number}: {e}")

    updated_comic_data_path = project_root / 'output' / 'final_comic_data_with_images.json'
    with updated_comic_data_path.open('w', encoding='utf-8') as f:
        json.dump(comic_data, f, ensure_ascii=False, indent=2)

    print(f"Updated comic data with image paths saved to {updated_comic_data_path}")
    print("STEP 3 finished.")
