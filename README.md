# Palette Curve Lab

一个本地运行的简易色彩曲线工具。

## 1. 创建虚拟环境

macOS:

```bash
git clone https://github.com/QingzhouC/color_palette_tool.git
cd color_palette_tool
python3 -m venv .venv
source .venv/bin/activate
```

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 运行

```bash
python app.py
```
如果这个不行运行
```bash
python3 app.py
```

程序会自动打开：

http://127.0.0.1:5000/

## 功能

- 输入 C10 ~ C1 的 HEX
- 实时生成色卡
- 实时计算 CIE LCH(ab)
- 实时计算 HSL
- 绘制 LCH 的 L/C/H 三条曲线
- 绘制 HSL 的 H/S/L 三条曲线

