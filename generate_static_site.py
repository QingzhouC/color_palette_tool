"""
预生成静态网站所需的所有色板数据 (JSON)

用法:
    python3 generate_static_site.py

输出:
    docs/data/brand_palette.json       — 完整 10 组品牌色板数据
    docs/data/figma_palette_tokens.json — Figma 导入用 Tokens
"""

import json
from pathlib import Path

from generate_brand_palette import generate_palette

# ============================================================
# 10 个主品牌色（与 app.py 保持一致）
# ============================================================

BRAND_COLORS = [
    {"name": "Red",    "hex": "#E92B3B"},
    {"name": "Pink",   "hex": "#DF0CC6"},
    {"name": "Purple", "hex": "#A010F9"},
    {"name": "Violet", "hex": "#5C5CEB"},
    {"name": "Brand",  "hex": "#005AEB"},
    {"name": "Blue",   "hex": "#008DEB"},
    {"name": "Cyan",   "hex": "#00CBEB"},
    {"name": "Green",  "hex": "#14B822"},
    {"name": "Yellow", "hex": "#F2CC0D"},
    {"name": "Orange", "hex": "#ED881D"},
]

DOCS_DIR = Path(__file__).parent / "docs"
DATA_DIR = DOCS_DIR / "data"


# ============================================================
# WCAG 对比度计算 (从 app.py 复制)
# ============================================================

def _hex_to_rgb_int(hex_color):
    h = hex_color.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _relative_luminance(hex_color):
    r, g, b = _hex_to_rgb_int(hex_color)
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(hex_a, hex_b):
    la = _relative_luminance(hex_a)
    lb = _relative_luminance(hex_b)
    lighter = max(la, lb)
    darker = min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def accessibility_for(hex_color):
    ratio_white = contrast_ratio(hex_color, "#FFFFFF")
    ratio_black = contrast_ratio(hex_color, "#000000")

    def grade(ratio):
        if ratio >= 7.0:
            label = "AAA"
        elif ratio >= 4.5:
            label = "AA"
        elif ratio >= 3.0:
            label = "AA Large"
        else:
            label = "Fail"
        return {"ratio": round(ratio, 2), "level": label}

    return {"on_white": grade(ratio_white), "on_black": grade(ratio_black)}


# ============================================================
# 生成完整色板数据
# ============================================================

def generate_brand_palette_data():
    """生成与 /api/brand-palette 相同格式的数据。"""
    groups = []

    for bc in BRAND_COLORS:
        df = generate_palette(bc["hex"])

        colors = []
        for _, row in df.iterrows():
            level = row["Level"]
            hex_val = row["HEX"]
            colors.append({
                "level": level,
                "hex": hex_val,
                "is_core": hex_val.upper() == bc["hex"].upper(),
                "l": round(float(row["L"]), 1),
                "c": round(float(row["C"]), 1),
                "h": round(float(row["H"]), 1),
                "accessibility": accessibility_for(hex_val),
            })

        groups.append({
            "name": bc["name"],
            "core_hex": bc["hex"],
            "is_core": bc["name"] == "Brand",
            "colors": colors,
        })

    return {"groups": groups}


def generate_single_palette_data():
    """为曲线工具预生成 10 组品牌色色板，用于静态品牌色模式。

    返回:
        {
            "#005AEB": ["#...", ...],  // C10 → C1
            "#E92B3B": ["#...", ...],
            ...
        }
    """
    result = {}
    for bc in BRAND_COLORS:
        df = generate_palette(bc["hex"])
        palette = df["HEX"].tolist()
        result[bc["hex"].upper()] = palette
    return result


# ============================================================
# 生成 Figma Tokens
# ============================================================

def generate_figma_tokens(palettes_data):
    tokens = {"color": {"brand": {}}}
    for group in palettes_data["groups"]:
        name_key = group["name"].lower().replace(" ", "_")
        tokens["color"]["brand"][name_key] = {}
        for color in group["colors"]:
            level_key = color["level"].lower()
            tokens["color"]["brand"][name_key][level_key] = {
                "value": color["hex"],
                "type": "color",
            }
    tokens["color"]["semantic"] = {
        "primary": {"value": "{color.brand.brand.c6}", "type": "color"},
        "primaryHover": {"value": "{color.brand.brand.c5}", "type": "color"},
        "primaryActive": {"value": "{color.brand.brand.c7}", "type": "color"},
    }
    return tokens


# ============================================================
# 主函数
# ============================================================

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("正在生成静态色板数据...")

    # 1. 完整品牌色板数据
    palettes_data = generate_brand_palette_data()
    brand_path = DATA_DIR / "brand_palette.json"
    with open(brand_path, "w", encoding="utf-8") as f:
        json.dump(palettes_data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 品牌色板数据: {brand_path}")

    # 2. 单色生成数据 (供曲线工具品牌色模式使用)
    single_data = generate_single_palette_data()
    single_path = DATA_DIR / "single_palettes.json"
    with open(single_path, "w", encoding="utf-8") as f:
        json.dump(single_data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 单色色板数据: {single_path}")

    # 3. Figma Tokens
    tokens = generate_figma_tokens(palettes_data)
    tokens_path = DATA_DIR / "figma_palette_tokens.json"
    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Figma Tokens: {tokens_path}")

    print("\n静态数据生成完成!")


if __name__ == "__main__":
    main()
