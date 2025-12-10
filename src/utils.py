
import os
from PIL import Image

def load_image_from_path(image_path: str) -> Image.Image:
    """Loads an image from a given file path."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")
    return Image.open(image_path)

def save_image_to_path(image: Image.Image, save_path: str):
    """Saves a PIL Image object to the specified path."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    image.save(save_path)
    # print(f"Image saved to: {save_path}")

def load_novel_text(file_path: str) -> str:
    """Loads text content from a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Novel text file not found at: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
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