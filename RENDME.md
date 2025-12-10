Novel Comic Generator

利用 Google Gemini API 将小说自动转换为漫画脚本与分镜描述。
本项目能够自动解析小说文本、拆分分镜，并为每个分镜生成视觉描述，便于后续图像生成（DALL-E / Stable Diffusion 等）。

目标：只需要一份小说文本，本工具就能帮助你生成完整的“漫画脚本 + 画面描述”。

✨ Features

自动解析小说文本 → 漫画分镜结构

自动生成角色 + 场景图像描述

支持角色立绘、术语演示图加入模型输入

基于 Gemini Text + Vision 多模态能力

可灵活扩展其他模型

结果存储为 JSON（可供漫画生成器进一步使用）

📦 Project Structure
novel_comic_project/
├── api_client.py
├── utils.py
├── comic_generator.py
├── main.py
├── novel.txt
├── images/
│   ├── characters/
│   └── terms/
└── output/
    └── generated_comic_data.json

🔧 Installation
pip install google-generativeai Pillow

🔑 API Key
export GOOGLE_API_KEY="your_api_key_here"


Colab 用户可通过左侧 “🔑 Secrets” 设置 GOOGLE_API_KEY。

📥 Prepare Input Files
小说文本
novel_comic_project/novel.txt

角色立绘示例
novel_comic_project/images/characters/Sir_Reginald.png

术语示例
novel_comic_project/images/terms/Shadow_Serpent.jpg

🚀 Run
python novel_comic_project/main.py


将生成：

novel_comic_project/output/generated_comic_data.json

🧩 Output Format
{
  "panels": [
    {
      "scene": "...",
      "dialog": "...",
      "characters": ["A","B"],
      "terms": ["Shadow_Serpent"],
      "generated_image_description": "..."
    }
  ]
}

🧠 API Example
from novel_comic_project import api_client

text = api_client.generate_text_content(
    "写一个关于宇宙飞船失事的故事。",
    model_name="gemini-1.5-pro"
)

multimodal = api_client.generate_multimodal_content(
    "描述这张图片。",
    image_list,
    model_name="gemini-1.5-pro-vision"
)

🌟 Next Steps (TODO)
Feature	状态
文本分镜生成	✔ Done
多模态提示生成	✔ Done
图片生成 (Stable Diffusion / DALL-E)	⏳
Web 漫画阅读器	⏳
Demo Notebook	⏳
📘 License

MIT License

⭐ Star

欢迎给项目点个 ⭐ 支持一下！