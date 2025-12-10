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
```
```
🚀 快速开始
1. 环境准备
确保你的环境中有 Python 3.8 或以上版本。
```
```Bash
# 克隆项目到本地
git clone [https://github.com/GYED123/novel_comic_project.git](https://github.com/GYED123/novel_comic_project.git)
cd novel_comic_project
# 安装依赖
pip install -r requirements.txt
```

```
2. 配置 API Key
你需要一个 Google Gemini 的 API Key。如果没有，请前往 Google AI Studio 申请。
```

Linux / macOS / Google Colab:
```Bash
export GOOGLE_API_KEY="你的_API_KEY_粘贴在这里"
```
```
Windows (PowerShell):
```

```PowerShell
$env:GOOGLE_API_KEY="你的_API_KEY_粘贴在这里"
```
3. 准备数据
小说文本：将你要转换的小说内容放入 data/ 目录（例如 data/novel.txt）。

角色参考（可选）：将主要角色的图片放入 images/characters/，文件名最好与小说中人名一致（如 Alice.png）。

场景/道具参考（可选）：将特殊设定的图片放入 images/terms/。

4. 运行生成
请根据你的实际入口文件位置运行（通常在 src 或 scripts 文件夹下）：

# 示例命令 (请根据实际文件名调整)
python src/main.py

🧩 输出示例
程序运行完成后，会在 output/ 目录下生成 generated_comic_data.json。结构如下：

{
  "panels": [
    {
      "id": 1,
      "scene_description": "昏暗的废弃仓库，光线从破窗射入，尘埃飞舞。",
      "characters": ["李明", "神秘人"],
      "dialog": "李明：'你到底是谁？'",
      "action": "李明紧握着手中的手电筒，警惕地盯着前方。",
      "camera_angle": "低角度仰视",
      "visual_prompt": "cinematic shot, low angle, dark abandoned warehouse, dust particles in light beams, a young man holding a flashlight looking tense, anime style, cel shading"
    }
  ]
}
🛠️ 二次开发
本项目代码结构清晰，易于扩展：

修改 src/comic_generator.py 中的 Prompt 模板，可以调整生成风格（如：日漫风、美漫风）。

在 src/api_client.py 中可以更换为 Gemini 的其他模型版本（如 gemini-1.5-flash 以获得更快的速度）。

📝 TODO
[x] 文本分镜生成

[x] 多模态图片理解

[ ] 接入 Stable Diffusion API 自动生图

[ ] Web 可视化界面 (Gradio/Streamlit)

[ ] 支持长篇小说自动切分处理

📄 License
本项目采用 MIT License 开源。欢迎 Star ⭐ 和 Fork！
