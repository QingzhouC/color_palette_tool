"""
导出 Figma 可导入的色板 JSON 文件

用法:
    python3 export_figma_palette.py

输出:
    results/figma_palette_tokens.json   — Tokens Studio (W3C Design Tokens) 格式
    results/figma_palette_styles.json   — Figma Color Styles 简单格式
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

OUTPUT_DIR = Path(__file__).parent / "results"


# ============================================================
# 生成所有色板数据
# ============================================================

def generate_all_palettes():
    """为每个品牌色生成完整 10 级色阶 (C10 → C1)。

    返回:
        [
            {
                "name": "Red",
                "core_hex": "#E92B3B",
                "colors": [
                    {"level": "C10", "hex": "#...", "l": .., "c": .., "h": ..},
                    ...
                ]
            },
            ...
        ]
    """
    palettes = []

    for bc in BRAND_COLORS:
        df = generate_palette(bc["hex"])

        colors = []
        for _, row in df.iterrows():
            colors.append({
                "level": row["Level"],
                "hex": row["HEX"],
                "l": round(float(row["L"]), 2),
                "c": round(float(row["C"]), 2),
                "h": round(float(row["H"]), 2),
            })

        palettes.append({
            "name": bc["name"],
            "core_hex": bc["hex"],
            "colors": colors,
        })

    return palettes


# ============================================================
# 格式 1: Tokens Studio (W3C Design Tokens) 格式
#
# 这是 Figma 最主流的导入格式，使用 Tokens Studio for Figma 插件
# 即可直接导入。
#
# 结构:
# {
#   "color": {
#     "brand": {
#       "red": {
#         "c10": { "value": "#...", "type": "color" },
#         ...
#       }
#     }
#   }
# }
# ============================================================

def export_tokens_studio(palettes):
    """导出 Tokens Studio (W3C Design Tokens) 格式。"""

    tokens = {"color": {"brand": {}}}

    for palette in palettes:
        name_key = palette["name"].lower().replace(" ", "_")
        tokens["color"]["brand"][name_key] = {}

        for color in palette["colors"]:
            level_key = color["level"].lower()
            tokens["color"]["brand"][name_key][level_key] = {
                "value": color["hex"],
                "type": "color",
            }

    # 添加语义化别名 (Semantic Tokens)
    # 将 Brand/C6 定义为 primary
    tokens["color"]["semantic"] = {
        "primary": {
            "value": "{color.brand.brand.c6}",
            "type": "color",
        },
        "primaryHover": {
            "value": "{color.brand.brand.c5}",
            "type": "color",
        },
        "primaryActive": {
            "value": "{color.brand.brand.c7}",
            "type": "color",
        },
    }

    return tokens


# ============================================================
# 格式 2: Figma Color Styles 简单格式
#
# 适用于各种 Figma 颜色样式导入插件
#
# 结构:
# {
#   "colors": [
#     { "name": "Brand/Red/C10", "value": "#..." },
#     ...
#   ]
# }
# ============================================================

def export_color_styles(palettes):
    """导出 Figma Color Styles 简单格式。"""

    colors = []

    for palette in palettes:
        for color in palette["colors"]:
            colors.append({
                "name": f"Brand/{palette['name']}/{color['level']}",
                "value": color["hex"],
            })

    return {"colors": colors}


# ============================================================
# 主函数
# ============================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("正在生成色板...")
    palettes = generate_all_palettes()

    total_colors = sum(len(p["colors"]) for p in palettes)
    print(f"  ✓ 共生成 {len(palettes)} 组色板，{total_colors} 个颜色")

    # --- Tokens Studio 格式 ---
    tokens = export_tokens_studio(palettes)
    tokens_path = OUTPUT_DIR / "figma_palette_tokens.json"
    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Tokens Studio 格式已保存: {tokens_path}")

    # --- Color Styles 简单格式 ---
    styles = export_color_styles(palettes)
    styles_path = OUTPUT_DIR / "figma_palette_styles.json"
    with open(styles_path, "w", encoding="utf-8") as f:
        json.dump(styles, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Color Styles 格式已保存: {styles_path}")

    # --- 打印摘要 ---
    print("\n色板摘要:")
    print("-" * 50)
    for palette in palettes:
        print(f"  {palette['name']:10s} (核心: {palette['core_hex']})")
        for color in palette["colors"]:
            marker = " ← 核心" if color["hex"].upper() == palette["core_hex"].upper() else ""
            print(f"    {color['level']}: {color['hex']}{marker}")
    print("-" * 50)
    print(f"\n导入方法:")
    print(f"  1. Tokens Studio 格式: 在 Figma 中安装 'Tokens Studio for Figma' 插件")
    print(f"     → Apply → Import → 选择 figma_palette_tokens.json")
    print(f"  2. Color Styles 格式: 在 Figma 中安装颜色样式导入插件")
    print(f"     → 导入 figma_palette_styles.json")


if __name__ == "__main__":
    main()
