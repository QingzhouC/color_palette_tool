"""
导出 Figma Variables 扁平格式 JSON

用法:
    python3 export_figma_variables.py

输出:
    results/figma_variables.json

格式:
{
  "light/brand-1": { "hex": "#e8f0fe", "rgba": { "r": 232, "g": 240, "b": 254, "a": 1 } },
  "light/brand-2": { "hex": "#d0dffc", "rgba": { ... } },
  ...
  "light/gray-0": { "hex": "#ffffff", "rgba": { ... } },
  ...
}

说明:
  - 品牌色 (brand, red, pink, purple, violet, blue, cyan, green, yellow, orange)
    使用 generate_brand_palette.py 生成的色板数据
  - 灰色 (gray) 使用预设的标准灰色色阶
"""

import json
from pathlib import Path

# ============================================================
# 路径
# ============================================================

DATA_PATH = Path(__file__).parent / "docs" / "data" / "brand_palette.json"
OUTPUT_PATH = Path(__file__).parent / "results" / "figma_variables.json"

# ============================================================
# 灰色色阶 (预设标准值，不随品牌色变化)
# ============================================================

GRAY_PALETTE = [
    ("gray-0",  "#ffffff"),
    ("gray-1",  "#f8f8f9"),
    ("gray-2",  "#f4f4f5"),
    ("gray-3",  "#ecedef"),
    ("gray-4",  "#d6d8dc"),
    ("gray-5",  "#c8cbd1"),
    ("gray-6",  "#a8adb6"),
    ("gray-7",  "#878e9b"),
    ("gray-8",  "#6d7585"),
    ("gray-9",  "#4f5766"),
    ("gray-10", "#4c515c"),
    ("gray-11", "#040506"),
]


# ============================================================
# 工具函数
# ============================================================

def hex_to_rgba(hex_color):
    """将 #RRGGBB 转换为 {r, g, b, a}"""
    h = hex_color.strip().lstrip("#")
    return {
        "r": int(h[0:2], 16),
        "g": int(h[2:4], 16),
        "b": int(h[4:6], 16),
        "a": 1,
    }


def make_entry(hex_color):
    """生成单个颜色条目"""
    return {
        "hex": hex_color.lower(),
        "rgba": hex_to_rgba(hex_color),
    }


def level_to_number(level):
    """C1 → 1, C2 → 2, ..., C10 → 10"""
    return int(level.replace("C", ""))


# ============================================================
# 主函数
# ============================================================

def main():
    # 读取色板数据
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = {}

    # --- 品牌色 (使用我们生成的色板) ---
    # 按 brand → gray → green → red → orange → blue → yellow → pink → purple → violet → cyan 排列

    # 定义输出顺序
    GROUP_ORDER = [
        "brand", "green", "red", "orange", "blue",
        "yellow", "pink", "purple", "violet", "cyan",
    ]

    # 从 brand_palette.json 读取并按组组织
    group_colors = {}
    for group in data["groups"]:
        name_key = group["name"].lower()
        group_colors[name_key] = {}
        for color in group["colors"]:
            num = level_to_number(color["level"])
            group_colors[name_key][num] = color["hex"]

    # 按顺序输出品牌色 (1 → 10)
    for group_name in GROUP_ORDER:
        if group_name not in group_colors:
            continue
        colors = group_colors[group_name]
        for num in range(1, 11):
            hex_val = colors.get(num)
            if hex_val:
                key = f"light/{group_name}-{num}"
                output[key] = make_entry(hex_val)

    # --- 灰色 (使用预设值) ---
    for gray_name, gray_hex in GRAY_PALETTE:
        key = f"light/{gray_name}"
        output[key] = make_entry(gray_hex)

    # 写入文件
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    total = len(output)
    print(f"✓ Figma Variables JSON 已保存: {OUTPUT_PATH}")
    print(f"  共 {total} 个颜色变量")

    # 打印摘要
    print("\n变量列表:")
    print("-" * 60)
    current_group = ""
    for key, val in output.items():
        group = key.split("/")[1].split("-")[0]
        if group != current_group:
            current_group = group
            print(f"\n  {group}:")
        print(f"    {key:25s} → {val['hex']}")
    print("-" * 60)


if __name__ == "__main__":
    main()
