# Novel Comic Generator (小说漫改辅助工具)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Gemini API](https://img.shields.io/badge/Google-Gemini%20API-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Novel Comic Generator** 是一个利用 Google Gemini API 强大的多模态能力，将小说文本自动转换为**漫画脚本**与**分镜描述**的辅助开发工具。

只需要提供一段小说文本，本工具就能为你生成结构化的分镜数据（包含画面描述、台词、角色站位等），可以直接对接 Stable Diffusion、Midjourney 或 DALL-E 进行漫画绘制。

## ✨ 主要功能

- 📚 **自动分镜解析**：智能识别小说中的场景切换、对话和动作，自动拆分为标准漫画分镜。
- 🖼️ **AI 画面描述生成**：为每个分镜生成详细的 Prompt（提示词），包含镜头角度、光影氛围。
- 👥 **角色一致性辅助**：支持读取本地角色立绘（Character Sheet），让 AI 生成时参考特定的人物特征。
- 🧩 **多模态支持**：基于 Gemini Vision 能力，可理解术语图示和参考图。
- 💾 **结构化输出**：结果保存为标准 JSON 格式，便于二次开发或直接导入漫画生成工作流。

## 📂 项目结构

```text
novel_comic_project/
├── data/                  # 📂 存放输入的小说文本文件
├── images/                # 📂 存放参考图片
│   ├── characters/        #     - 角色立绘/设定图
│   └── terms/             #     - 专有名词/道具/场景参考图
├── output/                # 📂 存放生成的 JSON 结果
├── scripts/               # 📂 辅助脚本或入口文件
├── src/                   # 📂 核心源代码
│   ├── api_client.py      #     - Gemini API 调用封装
│   ├── comic_generator.py #     - 漫画生成逻辑
│   └── utils.py           #     - 工具函数
├── .gitignore
├── pyproject.toml         # 📦 项目配置文件
├── requirements.txt       # 📦 依赖列表
└── README.md
