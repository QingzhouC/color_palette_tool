#!/usr/bin/env python3
"""
从网页品牌色完整色板界面（/api/brand-palette）获取实时生成的色板数据，
导出为 Light.tokens.json 格式。
gray 色板保留 Light.tokens.json 原有数据不动，其余颜色组用网页生成的数据替换。
"""

import json
import sys

# 导入 app.py 中的品牌色定义和生成函数
sys.path.insert(0, '.')
from generate_brand_palette import generate_palette, compute_dark_c6

# 品牌色定义（与 app.py 中 BRAND_COLORS 一致）
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

# 品牌色组名 -> tokens 组名前缀
GROUP_NAME_MAP = {
    'Red': 'red',
    'Pink': 'pink',
    'Purple': 'purple',
    'Violet': 'violet',
    'Brand': 'brand',
    'Blue': 'blue',
    'Cyan': 'cyan',
    'Green': 'green',
    'Yellow': 'yellow',
    'Orange': 'orange',
}


def hex_to_components(hex_str):
    """将 hex 颜色字符串转换为 sRGB 0-1 范围的 components 数组。"""
    h = hex_str.lstrip('#')
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return [r, g, b]


def generate_brand_palette_data():
    """复现 app.py 中 /api/brand-palette 的逻辑，生成完整品牌色板。"""
    result = {'light': {}, 'dark': {}}

    for bc in BRAND_COLORS:
        df_light = generate_palette(bc["hex"], mode="light")
        df_dark = generate_palette(bc["hex"], mode="dark")

        token_prefix = GROUP_NAME_MAP[bc["name"]]

        # Light: levels C1-C10, C1 最浅 → token -1, C10 最深 → token -10
        for _, row in df_light.iterrows():
            level = row["Level"]      # e.g. "C1"
            hex_val = row["HEX"]
            num = int(level[1:])      # 1 -> 1
            token_key = f'{token_prefix}-{num}'
            result['light'][token_key] = hex_val

        # Dark: levels C1-C10, C1 最深 → token -1, C10 最浅 → token -10
        for _, row in df_dark.iterrows():
            level = row["Level"]
            hex_val = row["HEX"]
            num = int(level[1:])
            token_key = f'{token_prefix}-{num}'
            result['dark'][token_key] = hex_val

    return result


def main():
    # 读取原始 tokens 文件（作为模板，保留 gray 和 $extensions）
    with open('Light.tokens.json', 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    # 生成网页上的品牌色板数据
    print('正在生成品牌色板数据（调用 generate_palette）...')
    palette_data = generate_brand_palette_data()

    # 用生成的色板数据替换非 gray 颜色
    for mode in ['light', 'dark']:
        for token_key, hex_val in palette_data[mode].items():
            if token_key not in tokens[mode]:
                print(f'Warning: {token_key} not found in {mode} mode, skipping')
                continue

            components = hex_to_components(hex_val)

            # 保留原有结构，只替换 $value 中的颜色相关字段
            entry = tokens[mode][token_key]
            entry['$value']['colorSpace'] = 'srgb'
            entry['$value']['components'] = components
            entry['$value']['alpha'] = 1
            entry['$value']['hex'] = hex_val.upper()

    # 输出文件
    output_path = 'My.tokens.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f'已导出: {output_path}')

    # 验证
    with open(output_path, 'r', encoding='utf-8') as f:
        result = json.load(f)

    print(f'\n验证:')
    for mode in ['light', 'dark']:
        gray_count = sum(1 for k in result[mode] if k.startswith('gray-'))
        non_gray_count = sum(1 for k in result[mode] if not k.startswith('gray-'))
        print(f'  {mode}: gray={gray_count}, non-gray={non_gray_count}, total={len(result[mode])}')

    # 验证 gray 未被修改（与原文件一致）
    print('\nGray 全量验证 (应与原文件一致):')
    gray_ok = True
    for mode in ['light', 'dark']:
        for i in range(0, 12):
            key = f'gray-{i}'
            orig_hex = tokens[mode][key]['$value']['hex']
            result_hex = result[mode][key]['$value']['hex']
            if orig_hex != result_hex:
                print(f'  FAIL {mode}.{key}: {result_hex} != {orig_hex}')
                gray_ok = False
    if gray_ok:
        print('  全部一致 OK')

    # 验证非 gray 已被替换为生成数据
    print('\n非 Gray 全量验证 (应与生成的色板一致):')
    all_ok = True
    for mode in ['light', 'dark']:
        for token_key, expected_hex in palette_data[mode].items():
            result_hex = result[mode][token_key]['$value']['hex'].upper()
            expected = expected_hex.upper()
            if result_hex != expected:
                print(f'  MISMATCH {mode}.{token_key}: result={result_hex} expected={expected}')
                all_ok = False
    if all_ok:
        print('  全部匹配 OK')

    # 验证 components 与 hex 一致
    print('\nComponents 与 hex 一致性验证:')
    comp_ok = True
    for mode in ['light', 'dark']:
        for key, entry in result[mode].items():
            if key.startswith('gray-'):
                continue
            hex_val = entry['$value']['hex'].lstrip('#')
            r = int(hex_val[0:2], 16) / 255.0
            g = int(hex_val[2:4], 16) / 255.0
            b = int(hex_val[4:6], 16) / 255.0
            comps = entry['$value']['components']
            if abs(comps[0] - r) > 0.001 or abs(comps[1] - g) > 0.001 or abs(comps[2] - b) > 0.001:
                print(f'  MISMATCH {mode}.{key}: components={comps} vs hex={hex_val}')
                comp_ok = False
    if comp_ok:
        print('  全部一致 OK')

    # 打印完整色板供用户核对
    print('\n=== 导出的完整色板 ===')
    for mode in ['light', 'dark']:
        print(f'\n--- {mode.upper()} ---')
        for group_name in ['red', 'pink', 'purple', 'violet', 'brand', 'blue', 'cyan', 'green', 'yellow', 'orange']:
            hexes = [result[mode][f'{group_name}-{i}']['$value']['hex'] for i in range(1, 11)]
            print(f'  {group_name}: {", ".join(hexes)}')


if __name__ == '__main__':
    main()
