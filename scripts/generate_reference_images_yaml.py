from __future__ import annotations
import os
from pathlib import Path
from typing import Dict

import yaml
import tos  # ✅ 新的 TOS SDK

_TOS_CLIENT = None

def get_tos_client() -> "tos.TosClientV2":
    global _TOS_CLIENT
    if _TOS_CLIENT is not None:
        return _TOS_CLIENT

    ak = os.getenv("TOS_ACCESS_KEY_ID")
    sk = os.getenv("TOS_SECRET_ACCESS_KEY")
    endpoint = os.getenv("TOS_ENDPOINT")   # 例如：https://tos-cn-beijing.volces.com
    region = os.getenv("TOS_REGION")      # 例如：cn-beijing

    if not ak or not sk or not endpoint or not region:
        raise ValueError(
            "TOS_ACCESS_KEY_ID / TOS_SECRET_ACCESS_KEY / TOS_ENDPOINT / TOS_REGION "
            "有未设置的环境变量，请先在环境里配置好。"
        )

    # 官方 SDK 的创建方式:contentReference[oaicite:1]{index=1}
    _TOS_CLIENT = tos.TosClientV2(ak, sk, endpoint, region)
    return _TOS_CLIENT
def upload_to_tos(local_path: Path, object_key: str) -> str:
    """
    把本地文件上传到 TOS，并返回一个可公开访问的 URL（假设你桶是公网读或者有自定义域名）。
    """
    client = get_tos_client()
    bucket = os.getenv("TOS_BUCKET")
    public_base_url = os.getenv("TOS_PUBLIC_BASE_URL")  # 例如：https://your-bucket.tos-cn-beijing.volces.com

    if not bucket:
        raise ValueError("TOS_BUCKET 环境变量未设置。")

    # 上传文件（用 content 传 bytes）:contentReference[oaicite:2]{index=2}
    with open(local_path, "rb") as f:
        resp = client.put_object(bucket, object_key, content=f.read())
        # 一般 resp.status_code == 200 就算成功

    # 拼一个访问 URL（具体域名看你桶配置）
    if not public_base_url:
        # 兜底：用官方 endpoint + bucket 拼
        endpoint = os.getenv("TOS_ENDPOINT").rstrip("/")
        url = f"{endpoint}/{bucket}/{object_key}"
    else:
        url = f"{public_base_url.rstrip('/')}/{object_key}"

    print(f"[INFO] Uploaded {local_path} -> {url}")
    return url

def guess_character_name_from_filename(filename: str) -> str:
    """
    根据文件名猜角色名：
    - 默认去掉扩展名
    - 如果包含『常服』『战斗服』『便服』之类后缀，则去掉后缀部分
    """
    stem = Path(filename).stem  # 去掉 .png / .jpg
    # 简单规则：遇到这些关键词就截断
    suffix_keywords = ["常服", "战斗服", "便服", "立绘", "全身", "头像"]
    for k in suffix_keywords:
        if k in stem:
            idx = stem.index(k)
            if idx > 0:
                return stem[:idx]
    return stem


def generate_reference_images_yaml(project_root: Path) -> None:
    """
    遍历 images/characters 下的图片：
      1. 上传到 TOS
      2. 生成 { 角色名: URL } 映射
      3. 写入 data/reference_images.yaml 的 characters 字段
         - 若文件存在则会合并保留 scenes/styles 字段
    """
    characters_dir = project_root / "images" / "characters"
    if not characters_dir.exists():
        raise FileNotFoundError(f"角色图片目录不存在: {characters_dir}")

    print(f"[INFO] 扫描角色图片目录: {characters_dir}")

    # 1. 遍历本地立绘文件
    character_url_map: Dict[str, str] = {}
    for p in sorted(characters_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
            continue

        char_name = guess_character_name_from_filename(p.name)
        # object_key 用一个相对规范的路径，例如 characters/麟奈狸/原图文件名
        object_key = f"comic_refs/characters/{char_name}/{p.name}"

        url = upload_to_tos(p, object_key)
        character_url_map[char_name] = url

    # 2. 读取 / 合并 reference_images.yaml
    ref_yaml_path = project_root / "data" / "reference_images.yaml"
    if ref_yaml_path.exists():
        existing = yaml.safe_load(ref_yaml_path.read_text(encoding="utf-8")) or {}
    else:
        existing = {}

    characters = existing.get("characters", {}) or {}
    # 更新/覆盖已有同名角色
    characters.update(character_url_map)
    existing["characters"] = characters

    # 确保 scenes/styles 字段存在（即使为空）
    existing.setdefault("scenes", {})
    existing.setdefault("styles", {})

    # 3. 写回 YAML
    ref_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with ref_yaml_path.open("w", encoding="utf-8") as f:
        yaml.dump(existing, f, allow_unicode=True, sort_keys=False)

    print(f"[DONE] reference_images.yaml 已更新: {ref_yaml_path}")
    print("当前 characters 映射：")
    for name, url in characters.items():
        print(f"  - {name}: {url}")


if __name__ == "__main__":
    # 根据你的项目结构修改这里的根目录
    project_root = Path(__file__).resolve().parents[1]  # scripts/ 的上一级当成项目根
    generate_reference_images_yaml(project_root)