from __future__ import annotations
import os
import json
import yaml
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

from . import comic_generator
# 🔥 load_reference_images()

from typing import Dict
import yaml

def load_reference_images(project_root: Path) -> Dict[str, str]:
    """
    从 data/reference_images.yaml 读取人物/场景/风格参考图，
    自动补 https://
    """
    cfg_path = project_root / "data" / "reference_images.yaml"
    if not cfg_path.exists():
        print(f"[WARN] reference_images.yaml not found: {cfg_path}")
        return {}

    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    ref: Dict[str, str] = {}

    def fmt(url: str) -> str:
        # 自动补 https 链接，保证可以被豆包访问
        if url.startswith("http"):
            return url
        return "https://" + url.lstrip("/")

    for name, url in (data.get("characters") or {}).items():
        ref[f"character:{name}"] = fmt(url)

    for name, url in (data.get("scenes") or {}).items():
        ref[f"scene:{name}"] = fmt(url)

    for name, url in (data.get("styles") or {}).items():
        ref[f"style:{name}"] = fmt(url)

    print(f"[INFO] Loaded {len(ref)} reference images")
    return ref


def step1_export_comic_panels(project_root: Path):
    """
    第一步：
    - 只从 data/novel.txt 中加载小说文本
    - 调用 parse_novel_to_comic_panels 得到【纯文字分镜数据】
    - 保存为 YAML，方便人工修改
    """
    print("=== STEP 1: 导出分镜草稿（不生成图片提示） ===")

    # 只读小说文本
    novel_path = project_root / "data" / "novel.txt"
    if not novel_path.exists():
        raise FileNotFoundError(f"找不到小说文件: {novel_path}")

    print(f"Loading novel text from: {novel_path}")
    novel_text = novel_path.read_text(encoding="utf-8")
    print(f"Loaded novel text (length: {len(novel_text)} chars).")

    # 不再依赖角色图 / 术语图，先传空列表即可
    character_names: list[str] = []
    term_names: list[str] = []

    print("Parsing novel into comic panels (text-only)...")
    comic_panels_data = comic_generator.parse_novel_to_comic_panels(
        novel_text,
        character_names,
        term_names,
    )
    print(f"Generated {len(comic_panels_data)} comic panels (draft).")

    # 保存分镜 YAML 供人工修改
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    draft_yaml_path = output_dir / "comic_panels_draft.yaml"

    with draft_yaml_path.open("w", encoding="utf-8") as f:
        yaml.dump(comic_panels_data, f, allow_unicode=True, sort_keys=False)

    print(f"Comic panels draft saved to: {draft_yaml_path}")
    print("你现在可以去手动编辑这个 YAML，再执行 step 2 生成图片提示。")


def step2_generate_image_descriptions(project_root: Path, panels_yaml_path: Optional[str] = None):
    """
    第二步：
    - 读取已经人工修改好的分镜 YAML
    - 为每个 panel 生成 generated_image_description
    - 保存为 JSON（或你想要的其他格式）
    """
    print("=== STEP 2: 从分镜文档生成图片提示 ===")

    # 默认从 output/comic_panels_draft.yaml 读取
    if panels_yaml_path is None:
        panels_yaml_path = project_root / 'output' / 'comic_panels_draft.yaml'
    else:
        panels_yaml_path = Path(panels_yaml_path)

    if not panels_yaml_path.exists():
        raise FileNotFoundError(
            f"""找不到分镜 YAML 文件：{panels_yaml_path}
请先运行 step 1 生成，或指定 --panels-file 路径。"""
        )

    print(f"Loading panels from YAML: {panels_yaml_path}")
    with panels_yaml_path.open('r', encoding='utf-8') as f:
        comic_panels_data = yaml.safe_load(f)

    if not isinstance(comic_panels_data, list):
        raise ValueError("YAML 中的分镜数据应为一个 list，每个元素为一个 panel 的 dict。")

    # 再次加载资源（主要是角色图像 / 术语图像，用于辅助生成描述）
    print("Loading character and term images for image description generation...")
    novel_text, character_images, term_images = comic_generator.load_all_resources(project_root)
    print(f"Loaded {len(character_images)} character images.")
    print(f"Loaded {len(term_images)} term images.")

    print("Generating image descriptions for each comic panel...")
    full_comic_data = []

    for i, panel in enumerate(comic_panels_data):
        panel_number = panel.get('panel_number', i + 1)
        print(f"Processing panel {panel_number}...")

        image_description = comic_generator.generate_comic_panel_image_description(
            panel,
            character_images,
            term_images
        )

        panel['generated_image_description'] = image_description
        full_comic_data.append(panel)
        print(f"Image description for panel {panel_number} generated.")

    # 保存为 JSON
    output_dir = project_root / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'generated_comic_data.json'

    with output_file_path.open('w', encoding='utf-8') as f:
        json.dump(full_comic_data, f, ensure_ascii=False, indent=2)

    print(f"Complete comic data with image descriptions saved to {output_file_path}")
    print("STEP 2 finished.")

def step3_generate_comic_images(project_root: Path):
    """
    第三步：
    - 读取 step2 生成的 comic_data.json
    - 遍历每个 panel，使用 generated_image_description 生成图片
    - 保存图片到 output/comic_images 目录
    """
    print("=== STEP 3: 生成漫画图片 ===")

    # 从 generated_comic_data.json 读取数据
    comic_data_path = project_root / 'output' / 'generated_comic_data.json'
    if not comic_data_path.exists():
        raise FileNotFoundError(
            f"""找不到生成的漫画数据文件：{comic_data_path}
请先运行 step 2 生成图片提示。"""
        )
    
    print(f"Loading comic data from: {comic_data_path}")
    with comic_data_path.open('r', encoding='utf-8') as f:
        comic_data: List[Dict[str, Any]] = json.load(f)
    print(f"Loaded {len(comic_data)} panels.")

    comic_generator.generate_comic_images(project_root, comic_data)

def main():
    parser = argparse.ArgumentParser(description="Novel to Comic two-step pipeline")
    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3],
        required=True,
        help="选择执行哪一步：1 = 导出分镜草稿（YAML）；2 = 从分镜 YAML 生成图片提示；3 = 根据图片提示生成漫画图片"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="项目根目录（默认=本文件两级上级目录）"
    )
    parser.add_argument(
        "--panels-file",
        type=str,
        default=None,
        help="step 2 指定分镜 YAML 路径（默认使用 output/comic_panels_draft.yaml）"
    )

    args = parser.parse_args()

    # 自动推断 project_root
    # cli.py 在 novel_comic_project/src/cli.py
    # parents[1] -> novel_comic_project
    if args.project_root is None:
      project_root = Path(__file__).resolve().parents[1]
    else:
        project_root = Path(args.project_root).resolve()

    if args.step == 1:
        step1_export_comic_panels(project_root)
    elif args.step == 2:
        step2_generate_image_descriptions(project_root, args.panels_file)
    elif args.step == 3:
        step3_generate_comic_images(project_root)
    else:
        raise ValueError("Step must be 1, 2 or 3.")


if __name__ == "__main__":
    main()