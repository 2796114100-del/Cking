# Cking — 影视器材AI专家系统

基于 LangChain + Ollama 的本地 AI 智能助手，专注于影视器材领域。支持知识库检索、联网搜索、文件处理（Word/PPT/Excel）、图片分析与调色建议。

## 功能概览

- 影视器材专业问答（相机、镜头、灯光、录音、稳定器、无人机等）
- RAG 知识库检索（34 篇专业文档，向量语义搜索）
- 联网搜索（DuckDuckGo，知识库没有时自动补充）
- 文件读写（支持 .txt .docx .pptx .xlsx）
- 图片分析（EXIF 参数提取 + 色彩分析 + 调色建议）
- Gradio Web UI（网页聊天 + 文件上传）
- MCP Server（标准协议，可被 Claude Code 等客户端调用）
- 桌面控制面板（一键管理 Ollama、模型、网页界面、公网隧道）

---

## 一、环境准备

### 1.1 安装 Python

需要 Python 3.10 或以上版本。

下载地址：https://www.python.org/downloads/

安装时务必勾选 **"Add Python to PATH"**。

安装完成后打开终端（CMD 或 PowerShell），验证：

```bash
python --version
# 应该显示 Python 3.10.x 或更高
```

### 1.2 安装 Ollama

Ollama 是本地大模型运行平台，类似于大模型的"容器"。

下载地址：https://ollama.com/download

下载 Windows 版本，双击安装即可。安装后它会自动在后台运行（任务栏右下角能看到图标）。

验证安装：

```bash
ollama --version
```

### 1.3 下载模型

需要下载两个模型：一个对话模型，一个嵌入模型。

打开终端，依次运行：

```bash
# 对话模型（约 9GB，需要一定时间）
ollama pull qwen3:14b

# 嵌入模型（用于知识库向量化，约 270MB）
ollama pull nomic-embed-text
```

下载完成后验证：

```bash
ollama list
# 应该能看到 qwen3:14b 和 nomic-embed-text
```

> 注意：qwen3:14b 需要至少 16GB 内存。如果内存不够，可以换小模型：
> ```bash
> ollama pull qwen3:8b
> ```
> 然后修改 `agent.py` 第 57 行的模型名称。

### 1.4 安装 Git（可选，用于克隆项目）

下载地址：https://git-scm.com/downloads

---

## 二、获取项目代码

### 方式一：Git 克隆（推荐）

```bash
git clone https://github.com/2796114100-del/Cking.git
cd Cking
```

### 方式二：下载 ZIP

1. 打开 https://github.com/2796114100-del/Cking
2. 点绿色 "Code" 按钮 → "Download ZIP"
3. 解压到任意位置
4. 用终端进入解压后的文件夹

---

## 三、安装 Python 依赖

在项目目录下打开终端，依次运行：

```bash
# 创建虚拟环境（隔离项目依赖，不影响系统 Python）
python -m venv venv

# 激活虚拟环境
# Windows CMD：
venv\Scripts\activate.bat
# Windows PowerShell：
venv\Scripts\Activate.ps1
# Git Bash：
source venv/Scripts/activate

# 安装所有依赖
pip install langchain langgraph langchain-ollama langchain-core langchain-text-splitters
pip install chromadb requests
pip install mcp
pip install gradio
pip install duckduckgo-search
pip install python-docx python-pptx openpyxl
pip install Pillow colorthief
```

> 如果 PowerShell 提示"在此系统上禁止运行脚本"，以管理员身份运行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## 四、构建知识库索引

知识库文档在 `docs/` 文件夹下（34 篇 .txt 文件），需要先建立向量索引。

```bash
python setup_rag.py
```

正常输出应该是：

```
知识库索引建立完成！共 102 块。
```

这一步会把所有文档切块、向量化，存入 `chroma_db/` 文件夹。只需要运行一次，之后文档没变就不需要重新构建。

如果以后修改了 `docs/` 里的文档，重新运行一次即可。

---

## 五、启动项目

### 方式一：命令行启动（最简单）

```bash
# 确保虚拟环境已激活
venv\Scripts\activate.bat

# 启动网页界面
python webui.py
```

浏览器会自动打开 http://127.0.0.1:7860 ，即可开始对话。

### 方式二：控制面板启动

项目自带一个桌面控制面板（`launcher.py`），可以一键管理 Ollama、模型、网页界面和公网隧道。

```bash
python launcher.py
```

控制面板功能：

| 区域 | 功能 |
|------|------|
| Ollama 服务 | 检测 Ollama 是否运行，可关闭 Ollama |
| 模型管理 | 下拉选择已安装的模型，启动/停止模型 |
| 网页界面 | 启动/停止 Gradio 网页聊天界面 |
| 公网隧道 | 开启/关闭 Cloudflare 公网访问 |
| 运行日志 | 显示所有操作的实时日志 |

使用流程：

1. 运行 `python launcher.py` 打开控制面板
2. 确认 Ollama 状态显示"运行中"（绿色）
3. 选择模型（如 qwen3:14b），点击"启动模型"
4. 等待模型加载完成（首次约 30 秒）
5. 点击"启动网页界面"
6. 浏览器会自动打开 http://127.0.0.1:7860
7. （可选）点击"开启公网隧道"，复制链接发给别人

> 提示：可以创建桌面快捷方式方便以后使用。在桌面右键 → 新建 → 快捷方式，输入：
> `pythonw.exe 你的项目路径\launcher.py`

---

## 六、使用指南

### 6.1 基本对话

在网页界面的输入框输入问题即可：

```
推荐一个5000元的相机
索尼A7M4和佳能R6怎么选？
拍夜景需要什么镜头？
```

Cking 会先搜索本地知识库，如果知识库没有相关信息，会自动联网搜索。

### 6.2 上传文件

点击界面底部的"上传文件"按钮，支持以下格式：

| 格式 | 说明 |
|------|------|
| .txt | 纯文本文件 |
| .docx | Word 文档 |
| .pptx | PowerPoint 幻灯片 |
| .xlsx | Excel 表格 |
| .jpg/.png/.bmp/.webp | 图片文件 |

上传后输入指令：

```
# 读取文件
帮我读一下这个文件

# 修改文件
把第三行的价格改成16000元

# 写入新文件
帮我写一个拍摄方案，保存成PPT
```

### 6.3 图片分析

上传照片后输入：

```
帮我分析一下这张照片
这张照片的调色方向是什么？
给我一些调色建议
```

Cking 会返回：
- 拍摄参数（相机型号、光圈、快门、ISO、焦距等，需照片有 EXIF 信息）
- 色彩分析（亮度、色温、主色调、饱和度、对比度）
- 调色建议（具体的后期调整思路和工具推荐）

### 6.4 Excel 读写

上传 Excel 文件后可以进行数据操作：

```
帮我读一下这个表格
把第二行的年龄改成28
新增一行：王五 | 28 | 导演
```

Excel 写入时，数据用 `|` 分隔列，每行一条数据。

### 6.5 PPT 读写

上传 PPT 后可以读取每页内容。写入 PPT 时用 `---` 分隔每一页：

```
帮我写一个3页的拍摄方案PPT
内容：
第一页标题：项目概述
内容：这是一个旅拍项目
---
第二页标题：器材清单
内容：索尼A7M4 + 24-70 F2.8
---
第三页标题：拍摄计划
内容：第一天日出延时，第二天城市夜景
```

---

## 七、项目结构

```
Cking/
├── agent.py              # Agent 核心逻辑（模型 + 工具 + System Prompt）
├── webui.py              # Gradio 网页界面
├── launcher.py           # 桌面控制面板（tkinter）
├── mcp_server.py         # MCP Server（标准工具协议）
├── setup_rag.py          # 知识库索引构建脚本
├── .mcp.json             # MCP 配置文件
├── tools/
│   ├── file_tools.py     # 文件读写工具（txt/docx/pptx/xlsx）
│   ├── rag_tools.py      # 知识库搜索工具
│   ├── web_tools.py      # 联网搜索工具（DuckDuckGo）
│   └── image_tools.py    # 图片分析工具（EXIF + 色彩分析）
├── rag/
│   └── vector_store.py   # RAG 向量检索核心（ChromaDB + Ollama Embedding）
├── docs/                 # 知识库文档（34 篇影视器材资料）
│   ├── 索尼相机全系型号.txt
│   ├── 镜头基础知识.txt
│   ├── 预算方案_5000元.txt
│   └── ... (共 34 篇)
├── chroma_db/            # 向量数据库（运行 setup_rag.py 后生成）
├── uploads/              # 用户上传的文件
├── venv/                 # Python 虚拟环境
├── .gitignore
└── README.md             # 本文件
```

---

## 八、技术架构

```
用户
 ↓
Gradio Web UI (webui.py)
 ↓
Agent (agent.py)
 ├── System Prompt（人设 + 行为准则 + 工具使用策略）
 ├── 大模型：qwen3:14b (Ollama)
 ├── 短期记忆：MemorySaver
 └── 工具调用（ReAct 推理 + 行动循环）：
      ├── search_my_knowledge → RAG 知识库（ChromaDB + nomic-embed-text）
      ├── web_search → DuckDuckGo 联网搜索
      ├── read_file / write_file → 文件读写（txt/docx/pptx/xlsx）
      └── analyze_image → 图片分析（EXIF + Pillow + ColorThief）
```

决策流程：

```
用户提问
 ↓
Agent 思考：需要查资料吗？
 ↓
是 → 先查知识库（本地，快，免费）
 ↓
知识库没有？→ 联网搜索（远程，实时）
 ↓
综合所有信息 → 组织语言回答
```

---

## 九、常见问题

### Q: Ollama 没有运行怎么办？

确保 Ollama 已安装并在后台运行。任务栏右下角应该有 Ollama 图标。如果没有：

```bash
ollama serve
```

### Q: 模型加载很慢怎么办？

首次加载模型需要将模型从硬盘读入内存，qwen3:14b 约需 30 秒。后续对话会快很多。如果内存不足，换用更小的模型：

```bash
ollama pull qwen3:8b
```

然后修改 `agent.py` 中的模型名称。

### Q: 知识库搜索没有结果？

确保已运行 `python setup_rag.py` 构建索引。如果修改了 `docs/` 中的文档，需要重新运行。

### Q: Gradio 界面打不开？

检查端口 7860 是否被占用：

```bash
netstat -an | findstr 7860
```

如果有进程占用，可以修改 `webui.py` 中的 `server_port=7860` 为其他端口。

### Q: 联网搜索不工作？

DuckDuckGo 在某些网络环境下可能无法访问。可以尝试使用代理。如果不需要联网搜索，可以忽略，Agent 仍会使用知识库和模型自身知识回答。

### Q: 公网链接打不开？

Cloudflare Tunnel 的链接在进程运行期间有效。关闭控制面板后链接会失效，需要重新开启。每次开启会生成新的链接。

### Q: 如何添加自己的知识库文档？

1. 在 `docs/` 文件夹下放入 .txt 文件
2. 运行 `python setup_rag.py` 重建索引
3. 重启 Agent

文档格式建议：纯文本，每段一个主题，500 字以内效果最好。

### Q: 如何更换模型？

修改 `agent.py` 第 57 行：

```python
model = ChatOllama(model="你要用的模型名", temperature=0)
```

可用模型列表：https://ollama.com/library

---

## 十、依赖列表

| 库 | 用途 |
|----|------|
| langchain | AI Agent 框架 |
| langgraph | ReAct Agent 实现 |
| langchain-ollama | Ollama 模型接入 |
| chromadb | 向量数据库 |
| mcp | Model Context Protocol |
| gradio | Web UI |
| duckduckgo-search | 联网搜索 |
| python-docx | Word 文件读写 |
| python-pptx | PowerPoint 文件读写 |
| openpyxl | Excel 文件读写 |
| Pillow | 图片处理 |
| colorthief | 主色调提取 |
| requests | HTTP 请求 |

---

## 十一、许可证

本项目仅供学习和个人使用。知识库文档内容来自公开资料整理。
