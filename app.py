from flask import Flask, render_template, request, jsonify
import webbrowser
from threading import Timer

from generate_brand_palette import generate_palette

app = Flask(__name__)


# ============================================================
# 10 主品牌色（#005AEB 为主品牌色，其余由其衍生）
#
# 顺序: Red → Pink → Purple → Violet → Brand → Blue → Cyan → Green → Yellow → Orange
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


# ============================================================
# WCAG 可访问性（对比度）计算
# ============================================================

def _hex_to_rgb_int(hex_color):
    h = hex_color.strip().lstrip("#")
    return (
        int(h[0:2], 16),
        int(h[2:4], 16),
        int(h[4:6], 16),
    )


def _relative_luminance(hex_color):
    """WCAG 相对亮度 (0~1)。"""
    r, g, b = _hex_to_rgb_int(hex_color)

    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(hex_a, hex_b):
    """计算两个颜色之间的 WCAG 对比度 (1.0~21.0)。"""
    la = _relative_luminance(hex_a)
    lb = _relative_luminance(hex_b)
    lighter = max(la, lb)
    darker = min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def accessibility_for(hex_color):
    """返回该颜色在白底 / 黑底下的 WCAG 可访问性结果。

    等级标注规则：
      ratio >= 7  → "AAA"
      ratio >= 4.5 → "AA"
      ratio >= 3  → "AA Large" (大字号 AA)
      ratio < 3   → "Fail"
    """
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
        return {
            "ratio": round(ratio, 2),
            "level": label,
        }

    return {
        "on_white": grade(ratio_white),
        "on_black": grade(ratio_black),
    }


# ============================================================
# 路由
# ============================================================

@app.route("/")
def landing():
    """简约大气的入口页，选择进入色板工具或品牌色色板。"""
    return render_template("landing.html")


@app.route("/palette-tool")
def palette_tool():
    """原色板工具页面。"""
    return render_template("index.html")


@app.route("/brand-palette")
def brand_palette_page():
    """完整品牌色色板页面。"""
    return render_template("brand_palette.html", brand_colors=BRAND_COLORS)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """根据品牌色 (C6) 生成一整套色板。

    请求体 JSON: { "color": "#005AEB" }
    响应 JSON:   { "palette": ["#...", "#...", ...] }  (C10 → C1, 共 10 个)
    """
    data = request.get_json(silent=True) or {}
    color = (data.get("color") or "").strip()

    if not color or not color.startswith("#") or len(color) != 7:
        return jsonify({"error": "请提供合法的 #RRGGBB 颜色"}), 400

    try:
        df = generate_palette(color)
    except Exception as e:
        return jsonify({"error": f"生成失败: {e}"}), 500

    # df 的行顺序是 C10 → C1，提取 HEX
    palette = df["HEX"].tolist()
    levels = df["Level"].tolist()

    return jsonify({"palette": palette, "levels": levels})


@app.route("/api/brand-palette", methods=["GET"])
def api_brand_palette():
    """生成完整品牌色色板。

    对 10 个主品牌色逐一调用 generate_palette，
    拼成 10×10 的完整色板，并附带可访问性测试结果。

    响应 JSON:
    {
      "groups": [
        {
          "name": "Red",
          "core_hex": "#E92B3B",
          "colors": [
            {
              "level":"C10","hex":"#...",
              "accessibility": {
                "on_white": {"ratio":..,"aa_normal":bool,...},
                "on_black": {...}
              }
            }, ...
          ]
        }, ...
      ]
    }
    """
    groups = []

    for bc in BRAND_COLORS:
        try:
            df = generate_palette(bc["hex"])
        except Exception as e:
            return jsonify({"error": f"生成 {bc['name']} 失败: {e}"}), 500

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

    return jsonify({"groups": groups})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
