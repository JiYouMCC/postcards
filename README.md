# Postcards / 明信片收藏

## 中文说明

### 项目概览

这是一个基于 Jekyll 的静态网站，用于展示个人明信片收藏（收到/寄出），并提供地图、日历统计、交换记录等功能。  
仓库同时提供一个 Python Qt 桌面工具，用于浏览数据与导入新明信片。

### 功能结构（网站 + 桌面工具）

- 网站（Jekyll）
  - 页面层：`index.html`、`received.html`、`sent.html`、`exchange.html`、`geo-*.html`、`calendar.html`
  - 数据层：`_data\received.csv`、`_data\sent.csv`、`_data\grouped.csv`、`_data\*.yml`
  - 模板样式层：`_layouts\`、`_includes\`、`_sass\`、`css\`、`js\`
- 桌面工具（Qt）
  - 主程序：`scripts\postcards_qt.py`
  - 依赖文件：`scripts\requirements.txt`
  - 导入相关脚本：`scripts\sort.py`、`scripts\grouped.py`、`scripts\date_format.py` 等

### Jekyll 使用说明

安装依赖：

```powershell
bundle install
```

本地开发预览：

```powershell
bundle exec jekyll serve
```

生产构建：

```powershell
bundle exec jekyll build
```

说明：站点配置了 `baseurl: "/postcards"`，适配 GitHub Pages 部署。

### Qt 桌面工具说明

安装依赖：

```powershell
python -m pip install -r scripts\requirements.txt
```

启动工具：

```powershell
python scripts\postcards_qt.py
```

指定界面语言（可选，`zh`/`en`）：

```powershell
python scripts\postcards_qt.py --lang zh
```

也可以在菜单栏中切换：`Language -> 中文 / English`（切换后会自动重启应用）。

指定项目根目录（可选）：

```powershell
python scripts\postcards_qt.py --root C:\codes\postcards
```

### Qt 主要功能

- 统一窗口浏览 `Received` / `Sent` 数据
- 关键词搜索与多维筛选（平台、国家、类型、地区、日期范围）
- 查看卡片详情与图片预览，打开卡片/用户 URL
- `Tools -> Import new postcards...` 导入工具：
  - `Post-Hi`：选择 received/sent/expired-sent 三个 CSV 导入
  - `Postcrossing`：粘贴 ID 批量导入
  - `iCardYou`：支持列表格式或逐行 `type,path,id` 格式
  - `Images`：候选卡片、源图选择、预览、已有图片对比、图片分配与执行导入
- 导入后可运行 `Run sort.py + grouped.py` 更新排序和日历聚合数据

---

## English

### Overview

This repository contains a Jekyll-based static website for a personal postcard collection (received/sent), plus a Python Qt desktop tool for data browsing and import workflows.

### Functional Structure (Website + Desktop)

- Website (Jekyll)
  - Page layer: `index.html`, `received.html`, `sent.html`, `exchange.html`, `geo-*.html`, `calendar.html`
  - Data layer: `_data\received.csv`, `_data\sent.csv`, `_data\grouped.csv`, `_data\*.yml`
  - Template/style layer: `_layouts\`, `_includes\`, `_sass\`, `css\`, `js\`
- Desktop tool (Qt)
  - Main app: `scripts\postcards_qt.py`
  - Dependencies: `scripts\requirements.txt`
  - Import helpers: `scripts\sort.py`, `scripts\grouped.py`, `scripts\date_format.py`, etc.

### Jekyll Usage

Install dependencies:

```powershell
bundle install
```

Run local development server:

```powershell
bundle exec jekyll serve
```

Build production site:

```powershell
bundle exec jekyll build
```

Note: the site uses `baseurl: "/postcards"` for GitHub Pages deployment.

### Qt Desktop App Usage

Install dependencies:

```powershell
python -m pip install -r scripts\requirements.txt
```

Run:

```powershell
python scripts\postcards_qt.py
```

Optional UI language (`zh`/`en`):

```powershell
python scripts\postcards_qt.py --lang zh
```

You can also switch from the menu: `Language -> 中文 / English` (the app restarts automatically after switching).

Optional custom project root:

```powershell
python scripts\postcards_qt.py --root C:\codes\postcards
```

### Qt Feature Highlights

- Unified viewer with `Received` / `Sent` switching
- Keyword search and linked filters (platform, country, type, region, date range)
- Detail panel with postcard image preview and URL open actions
- `Tools -> Import new postcards...`:
  - `Post-Hi`: import 3 CSV files (received/sent/expired-sent)
  - `Postcrossing`: import by pasted card IDs
  - `iCardYou`: import from list format or line-based `type,path,id`
  - `Images`: candidate cards, source image selection, side-by-side preview, assignment, and execute import
- Post-processing via `Run sort.py + grouped.py`
