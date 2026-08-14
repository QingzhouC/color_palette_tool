from pathlib import Path
import math
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from skimage.color import rgb2lab, lab2rgb


# ============================================================
# 1. 输入品牌色
# ============================================================

BRAND_COLOR = "#005aeb"

CORE_LEVEL = "C6"

LEVELS = [
    "C10",
    "C9",
    "C8",
    "C7",
    "C6",
    "C5",
    "C4",
    "C3",
    "C2",
    "C1",
]


# ============================================================
# 2. Hue-Adaptive 参数
# ============================================================

# Hue 影响范围
#
# 越小：
# 越接近附近色相自己的曲线
#
# 越大：
# 不同色相之间融合更多
#
HUE_SIGMA = 35.0


# Hue-Adaptive 强度
#
# 0.0 = 完全使用多组色卡的通用模型
# 1.0 = 完全根据 Hue 自适应
#
# 建议先使用 0.75
ADAPT_STRENGTH = 0.75


# 如果品牌色 Hue 距离某个训练核心色非常接近，
# 直接使用该训练色卡的模型。
#
# 这样 #105CF4 可以最大程度还原原蓝色色阶。
ANCHOR_HUE_TOLERANCE = 1.0


# ============================================================
# 3. 训练色卡（从数据库读取）
#
# 全部按照 C10 → C1
#
# 色卡数据存储在 palettes.db 中，
# 运行 init_palette_db.py 初始化数据库。
# ============================================================

DB_PATH = Path(__file__).parent / "palettes.db"


def load_reference_palettes(mode="light"):
    """从 palettes.db 读取参考色卡。

    参数:
        mode: "light" 或 "dark"，选择对应模式的训练色卡

    返回格式与原来的 REFERENCE_PALETTES 字典一致:
        {
            "blue": ["#001A4D", ...],
            "red":  ["#4D0006", ...],
            ...
        }
    """

    if not DB_PATH.exists():

        raise FileNotFoundError(
            "palettes.db 不存在，请先运行 init_palette_db.py"
        )

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, level, hex
        FROM reference_palettes
        WHERE mode = ?
        ORDER BY name, position
        """,
        (mode,),
    )

    palettes = {}

    for name, level, hex_color in cursor.fetchall():

        if name not in palettes:
            palettes[name] = []

        palettes[name].append(hex_color)

    conn.close()

    return palettes


# ============================================================
# 4. 输出
# ============================================================

OUTPUT_FOLDER = Path("results")
OUTPUT_FOLDER.mkdir(exist_ok=True)

IMAGE_FOLDER = OUTPUT_FOLDER / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)


def get_next_output_paths():

    existing = sorted(
        OUTPUT_FOLDER.glob(
            "brand_palette*.csv"
        )
    )

    max_num = 0

    for f in existing:

        stem = f.stem

        try:

            num = int(
                stem.replace(
                    "brand_palette",
                    ""
                )
            )

            max_num = max(
                max_num,
                num
            )

        except ValueError:
            continue

    next_num = (
        max_num + 1
    )

    name = (
        f"brand_palette"
        f"{next_num:03d}"
    )

    csv_path = (
        OUTPUT_FOLDER
        /
        f"{name}.csv"
    )

    image_path = (
        IMAGE_FOLDER
        /
        f"{name}.png"
    )

    return (
        csv_path,
        image_path
    )


# ============================================================
# 5. HEX ↔ RGB
# ============================================================

def hex_to_rgb(hex_color):

    hex_color = (
        hex_color
        .strip()
        .lstrip("#")
    )

    return np.array([
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    ]) / 255.0


def rgb_to_hex(rgb):

    rgb = np.clip(
        rgb,
        0,
        1
    )

    values = np.round(
        rgb * 255
    ).astype(int)

    return "#{:02X}{:02X}{:02X}".format(
        values[0],
        values[1],
        values[2]
    )


# ============================================================
# 5b. HSB / HSV 转换
#
# 仅用于 Dark Mode 锚点计算
# ============================================================

def rgb_to_hsb(rgb):

    r, g, b = rgb

    mx = max(r, g, b)
    mn = min(r, g, b)
    delta = mx - mn

    # Value
    v = mx

    # Saturation
    s = 0.0 if mx == 0 else delta / mx

    # Hue
    if delta == 0:
        h = 0.0
    elif mx == r:
        h = 60.0 * (((g - b) / delta) % 6)
    elif mx == g:
        h = 60.0 * (((b - r) / delta) + 2)
    else:
        h = 60.0 * (((r - g) / delta) + 4)

    if h < 0:
        h += 360

    return np.array([h, s * 100, v * 100])


def hsb_to_rgb(hsb):

    h, s, v = hsb

    s = s / 100.0
    v = v / 100.0

    c = v * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = v - c

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return np.array([r + m, g + m, b + m])


def hex_to_hsb(hex_color):

    rgb = hex_to_rgb(hex_color)
    return rgb_to_hsb(rgb)


def hsb_to_hex(h, s, v):

    rgb = hsb_to_rgb(np.array([h, s, v]))
    return rgb_to_hex(rgb)


# ============================================================
# 6. Lab ↔ LCH
# ============================================================

def lab_to_lch(lab):

    L, a, b = lab

    C = math.sqrt(
        a ** 2
        +
        b ** 2
    )

    H = math.degrees(
        math.atan2(
            b,
            a
        )
    )

    if H < 0:
        H += 360

    return np.array([
        L,
        C,
        H
    ])


def lch_to_lab(lch):

    L, C, H = lch

    H_rad = math.radians(
        H
    )

    a = (
        C
        *
        math.cos(
            H_rad
        )
    )

    b = (
        C
        *
        math.sin(
            H_rad
        )
    )

    return np.array([
        L,
        a,
        b
    ])


# ============================================================
# 7. HEX → LCH
# ============================================================

def hex_to_lch(hex_color):

    rgb = hex_to_rgb(
        hex_color
    )

    rgb_image = rgb.reshape(
        1,
        1,
        3
    )

    lab = rgb2lab(
        rgb_image
    )[0, 0]

    return lab_to_lch(
        lab
    )


# ============================================================
# 8. LCH → RGB / HEX
# ============================================================

def lab_to_raw_rgb(lab):

    lab_image = lab.reshape(
        1,
        1,
        3
    )

    return lab2rgb(
        lab_image
    )[0, 0]


def lch_to_hex_gamut_safe(lch):

    L, C, H = lch

    current_C = C

    for _ in range(100):

        lab = lch_to_lab([
            L,
            current_C,
            H
        ])

        rgb = lab_to_raw_rgb(
            lab
        )

        if (
            np.all(rgb >= 0)
            and
            np.all(rgb <= 1)
        ):

            return (
                rgb_to_hex(
                    rgb
                ),

                np.array([
                    L,
                    current_C,
                    H
                ])
            )

        current_C *= 0.97

    rgb = np.clip(
        rgb,
        0,
        1
    )

    return (
        rgb_to_hex(
            rgb
        ),

        np.array([
            L,
            current_C,
            H
        ])
    )


# ============================================================
# 9. Hue 圆形计算
# ============================================================

def hue_difference(
    hue,
    reference_hue
):

    return (
        (
            hue
            -
            reference_hue
            +
            180
        )
        %
        360
        -
        180
    )


def hue_distance(
    hue1,
    hue2
):

    return abs(
        hue_difference(
            hue1,
            hue2
        )
    )


# ============================================================
# 10. Cubic Bezier
# ============================================================

def cubic_bezier(
    t,
    p0,
    p1,
    p2,
    p3
):

    return (

        ((1 - t) ** 3)
        *
        p0

        +

        3
        *
        ((1 - t) ** 2)
        *
        t
        *
        p1

        +

        3
        *
        (1 - t)
        *
        (t ** 2)
        *
        p2

        +

        (t ** 3)
        *
        p3

    )


# ============================================================
# 11. Cubic Bezier 拟合
# ============================================================

def fit_scalar_bezier(
    values,
    t_values
):

    values = np.array(
        values,
        dtype=float
    )

    p0 = values[0]
    p3 = values[-1]

    A = []
    Y = []

    for t, value in zip(
        t_values,
        values
    ):

        b1 = (
            3
            *
            ((1 - t) ** 2)
            *
            t
        )

        b2 = (
            3
            *
            (1 - t)
            *
            (t ** 2)
        )

        known = (
            ((1 - t) ** 3)
            *
            p0

            +

            (t ** 3)
            *
            p3
        )

        A.append([
            b1,
            b2
        ])

        Y.append(
            value
            -
            known
        )

    A = np.array(
        A
    )

    Y = np.array(
        Y
    )

    solution, _, _, _ = (
        np.linalg.lstsq(
            A,
            Y,
            rcond=None
        )
    )

    return (
        float(p0),
        float(solution[0]),
        float(solution[1]),
        float(p3)
    )


# ============================================================
# 12. 单套 Palette 倒推 Bezier
#
# 完全保留你第一版的逻辑
# ============================================================

def build_single_palette_model(
    colors,
    mode="light"
):

    reference_lch = np.array([
        hex_to_lch(
            color
        )
        for color
        in colors
    ])

    # C6 = index 4
    core = (
        reference_lch[4]
    )

    core_L = core[0]
    core_C = core[1]
    core_H = core[2]

    # ========================================================
    # Dark
    # ========================================================

    dark = (
        reference_lch[:5]
    )

    # --------------------------------------------------------
    # L 明度归一化（区分 Light / Dark Mode）
    #
    # Light Mode：C10 → C6 为深色 → 核心色
    #     使用 ratio = L / core_L
    #
    # Dark Mode ：C10 → C6 为浅色 → 核心色
    #     使用 progress = (L - core_L) / (100 - core_L)
    # --------------------------------------------------------
    if mode == "dark":
        dark_L = (
            (
                dark[:, 0]
                -
                core_L
            )
            /
            (
                100
                -
                core_L
            )
        )
    else:
        dark_L = (
            dark[:, 0]
            /
            core_L
        )

    dark_C = (
        dark[:, 1]
        /
        core_C
    )

    dark_H = np.array([
        hue_difference(
            hue,
            core_H
        )

        for hue
        in dark[:, 2]
    ])

    # ========================================================
    # Light
    # ========================================================

    light = (
        reference_lch[4:]
    )

    # --------------------------------------------------------
    # L 明度归一化（区分 Light / Dark Mode）
    #
    # Light Mode：C6 → C1 为核心色 → 浅色
    #     使用 progress = (L - core_L) / (100 - core_L)
    #
    # Dark Mode ：C6 → C1 为核心色 → 深色
    #     使用 ratio = L / core_L
    # --------------------------------------------------------
    if mode == "dark":
        light_L = (
            light[:, 0]
            /
            core_L
        )
    else:
        light_L = (
            (
                light[:, 0]
                -
                core_L
            )
            /
            (
                100
                -
                core_L
            )
        )

    light_C = (
        light[:, 1]
        /
        core_C
    )

    light_H = np.array([
        hue_difference(
            hue,
            core_H
        )

        for hue
        in light[:, 2]
    ])

    dark_t = np.linspace(
        0,
        1,
        5
    )

    light_t = np.linspace(
        0,
        1,
        6
    )

    return {

        "core_H":
            float(
                core_H
            ),

        "dark_L":
            fit_scalar_bezier(
                dark_L,
                dark_t
            ),

        "dark_C":
            fit_scalar_bezier(
                dark_C,
                dark_t
            ),

        "dark_H":
            fit_scalar_bezier(
                dark_H,
                dark_t
            ),

        "light_L":
            fit_scalar_bezier(
                light_L,
                light_t
            ),

        "light_C":
            fit_scalar_bezier(
                light_C,
                light_t
            ),

        "light_H":
            fit_scalar_bezier(
                light_H,
                light_t
            ),
    }


# ============================================================
# 13. 建立所有 Hue Anchor 模型
# ============================================================

MODEL_KEYS = [
    "dark_L",
    "dark_C",
    "dark_H",
    "light_L",
    "light_C",
    "light_H",
]


def build_anchor_models(mode="light"):

    reference_palettes = load_reference_palettes(mode)

    models = {}

    for (
        name,
        colors
    ) in (
        reference_palettes.items()
    ):

        models[name] = (
            build_single_palette_model(
                colors,
                mode=mode
            )
        )

    return models


# ============================================================
# 14. 建立通用 Median 模型
#
# 作为 Hue Adaptive 的稳定底座。
# ============================================================

def build_universal_model(
    anchor_models
):

    universal = {}

    for key in MODEL_KEYS:

        controls = np.array([
            model[key]
            for model
            in anchor_models.values()
        ])

        universal[key] = tuple(
            np.median(
                controls,
                axis=0
            )
        )

    return universal


# ============================================================
# 15. Hue 权重
#
# 每套模型的权重由：
#
# 当前 Brand Hue
# 和
# 参考 Palette C6 Hue
#
# 的圆形距离决定。
#
# 不是硬切换。
# ============================================================

def calculate_hue_weights(
    brand_H,
    anchor_models
):

    distances = {}

    # --------------------------------------------------------
    # 先检查是否接近某个 Anchor
    # --------------------------------------------------------

    for (
        name,
        model
    ) in anchor_models.items():

        distance = hue_distance(
            brand_H,
            model[
                "core_H"
            ]
        )

        distances[name] = (
            distance
        )

        if (
            distance
            <=
            ANCHOR_HUE_TOLERANCE
        ):

            weights = {
                n: 0.0
                for n
                in anchor_models
            }

            weights[name] = 1.0

            return (
                weights,
                True
            )

    # --------------------------------------------------------
    # Gaussian 连续权重
    # --------------------------------------------------------

    raw = {}

    for (
        name,
        distance
    ) in distances.items():

        raw[name] = math.exp(

            -

            (
                distance ** 2
            )

            /

            (
                2
                *
                HUE_SIGMA ** 2
            )
        )

    total = sum(
        raw.values()
    )

    if total == 0:

        count = len(
            raw
        )

        return (
            {
                name:
                    1 / count
                for name
                in raw
            },
            False
        )

    weights = {

        name:
            value / total

        for (
            name,
            value
        ) in raw.items()
    }

    return (
        weights,
        False
    )


# ============================================================
# 16. 根据 Hue 连续生成 Bezier 控制点
# ============================================================

def build_reference_model(
    brand_color,
    mode="light"
):

    brand_lch = (
        hex_to_lch(
            brand_color
        )
    )

    brand_H = (
        brand_lch[2]
    )

    anchor_models = (
        build_anchor_models(mode)
    )

    universal_model = (
        build_universal_model(
            anchor_models
        )
    )

    (
        weights,
        exact_anchor
    ) = (
        calculate_hue_weights(
            brand_H,
            anchor_models
        )
    )

    # ========================================================
    # 如果正好命中一个 Anchor
    #
    # 直接使用该 Palette 倒推模型
    # ========================================================

    if exact_anchor:

        anchor_name = max(
            weights,
            key=weights.get
        )

        selected = (
            anchor_models[
                anchor_name
            ]
        )

        model = {
            key:
                selected[key]
            for key
            in MODEL_KEYS
        }

        print(
            "\nExact Hue Anchor:"
        )

        print(
            anchor_name
        )

        return model

    # ========================================================
    # Hue Adaptive Model
    # ========================================================

    local_model = {}

    for key in MODEL_KEYS:

        blended = np.zeros(
            4,
            dtype=float
        )

        for (
            name,
            anchor_model
        ) in (
            anchor_models.items()
        ):

            blended += (
                np.array(
                    anchor_model[key]
                )
                *
                weights[name]
            )

        local_model[key] = tuple(
            blended
        )

    # ========================================================
    # Adaptive + Universal
    #
    # 避免只有 5 个训练 Hue 时曲线过度摆动
    # ========================================================

    model = {}

    for key in MODEL_KEYS:

        local = np.array(
            local_model[key]
        )

        universal = np.array(
            universal_model[key]
        )

        final = (
            ADAPT_STRENGTH
            *
            local

            +

            (
                1
                -
                ADAPT_STRENGTH
            )
            *
            universal
        )

        model[key] = tuple(
            final
        )

    # ========================================================
    # 输出当前 Hue 权重
    # ========================================================

    print(
        "\nHue-Adaptive Model"
    )

    print(
        "-" * 60
    )

    print(
        f"Brand Hue: "
        f"{brand_H:.2f}°"
    )

    print(
        "\nHue Weights:"
    )

    sorted_weights = sorted(
        weights.items(),
        key=lambda x:
            x[1],
        reverse=True
    )

    for (
        name,
        weight
    ) in sorted_weights:

        print(
            f"{name:12s}"
            f" : "
            f"{weight:.2%}"
        )

    print(
        "\nAdaptive Strength:"
    )

    print(
        ADAPT_STRENGTH
    )

    print(
        "\nGenerated Bezier:"
    )

    for key in MODEL_KEYS:

        print(
            key,
            "=",
            np.round(
                model[key],
                4
            )
        )

    return model


# ============================================================
# 16b. Dark Mode C6 锚点计算
#
# H 不变
# S 按区间偏移
# B / V 不变
# ============================================================

# Dark Mode C6 手动覆盖映射
#
# key   = Light Mode 品牌色 HEX（大写）
# value = 用户指定的 Dark Mode C6 HEX
#
DARK_C6_OVERRIDES = {
    "#A010F9": "#AE37F9",  # Purple
    "#E92B3B": "#E94D5A",  # Red
    "#14B822": "#30B83B",  # Green
}


def compute_dark_c6(light_c6_hex):
    """根据浅色模式 C6 计算深色模式 C6。

    规则:
        1. 如果品牌色在 DARK_C6_OVERRIDES 中，直接使用用户指定的值
        2. 否则使用算法:
           H_dark = H_light
           S_dark = S_light - offset
               H   0°- 49° → offset = 15
               H  50°-190° → offset = 20
               H 191°-360° → offset = 15
           B_dark = B_light  (Value 不变)

    返回: (dark_c6_hex, hsb_light, hsb_dark)
    """

    hsb_light = hex_to_hsb(light_c6_hex)

    # --------------------------------------------------------
    # 检查是否在手动覆盖映射中
    # --------------------------------------------------------

    override_key = light_c6_hex.strip().upper()

    if override_key in DARK_C6_OVERRIDES:

        dark_c6_hex = DARK_C6_OVERRIDES[override_key]

        hsb_dark = hex_to_hsb(dark_c6_hex)

        return dark_c6_hex, hsb_light, hsb_dark

    # --------------------------------------------------------
    # 算法计算
    # --------------------------------------------------------

    h_light = float(hsb_light[0])
    s_light = float(hsb_light[1])
    b_light = float(hsb_light[2])

    # H 不变
    h_dark = h_light

    # S 按区间偏移
    if 0 <= h_light <= 49:
        s_offset = 15.0
    elif 50 <= h_light <= 190:
        s_offset = 20.0
    else:
        s_offset = 15.0

    s_dark = max(0.0, min(100.0, s_light - s_offset))

    # B / V 不变
    b_dark = b_light

    dark_c6_hex = hsb_to_hex(h_dark, s_dark, b_dark)

    hsb_dark = np.array([h_dark, s_dark, b_dark])

    return dark_c6_hex, hsb_light, hsb_dark


# ============================================================
# 17. 根据品牌色生成 Palette
#
# 这一部分保持你喜欢的第一版逻辑。
#
# mode="light": 使用品牌色直接作为 C6 锚点（现有逻辑）
# mode="dark":  先计算 Dark C6，再以 Dark C6 为锚点
# ============================================================

def generate_palette(
    brand_color,
    mode="light"
):

    # --------------------------------------------------------
    # Dark Mode: 先计算 Dark C6，再以 Dark C6 为锚点
    # Light Mode: 直接使用品牌色作为 C6
    # --------------------------------------------------------

    if mode == "dark":

        c6_color, _, _ = compute_dark_c6(
            brand_color
        )

    else:

        c6_color = brand_color

    model = (
        build_reference_model(
            c6_color,
            mode
        )
    )

    brand_lch = (
        hex_to_lch(
            c6_color
        )
    )

    brand_L = (
        brand_lch[0]
    )

    brand_C = (
        brand_lch[1]
    )

    brand_H = (
        brand_lch[2]
    )

    rows = []

    # ========================================================
    # Dark C10 → C6
    # ========================================================

    dark_levels = [
        "C10",
        "C9",
        "C8",
        "C7",
        "C6",
    ]

    dark_t_values = np.linspace(
        0,
        1,
        5
    )

    for (
        level,
        t
    ) in zip(
        dark_levels,
        dark_t_values
    ):

        L_param = cubic_bezier(
            t,
            *model[
                "dark_L"
            ]
        )

        C_ratio = cubic_bezier(
            t,
            *model[
                "dark_C"
            ]
        )

        H_delta = cubic_bezier(
            t,
            *model[
                "dark_H"
            ]
        )

        # ------------------------------------------------
        # L 重建公式（区分 Light / Dark Mode）
        #
        # Light Mode：C10 → C6 为深色 → 核心色
        #     L = brand_L * L_ratio
        #
        # Dark Mode：C10 → C6 为浅色 → 核心色
        #     L = brand_L + L_progress * (100 - brand_L)
        #
        # 对参数做 clip，防止 Bezier overshoot
        # ------------------------------------------------
        if mode == "dark":

            # Dark Mode：C10 → C6 为浅色 → 核心色
            L_progress = float(
                np.clip(
                    L_param,
                    0.0,
                    0.98
                )
            )

            L = (
                brand_L
                +
                L_progress
                *
                (
                    100
                    -
                    brand_L
                )
            )

        else:

            L_ratio = float(
                np.clip(
                    L_param,
                    0.0,
                    1.0
                )
            )

            L = (
                brand_L
                *
                L_ratio
            )

        C = (
            brand_C
            *
            C_ratio
        )

        H = (
            brand_H
            +
            H_delta
        ) % 360

        if level == "C6":

            final_hex = (
                c6_color
                .upper()
            )

            final_lch = (
                brand_lch
                .copy()
            )

        else:

            # 防止 Bezier overshoot 导致 L 接近 100（纯白）
            L = float(
                np.clip(
                    L,
                    1.0,
                    98.0
                )
            )

            (
                final_hex,
                final_lch
            ) = (
                lch_to_hex_gamut_safe([
                    L,
                    C,
                    H
                ])
            )

        rows.append({

            "Level":
                level,

            "HEX":
                final_hex,

            "L":
                round(
                    final_lch[0],
                    4
                ),

            "C":
                round(
                    final_lch[1],
                    4
                ),

            "H":
                round(
                    final_lch[2]
                    %
                    360,
                    4
                ),

        })

    # ========================================================
    # Light C6 → C1
    # ========================================================

    light_levels = [
        "C6",
        "C5",
        "C4",
        "C3",
        "C2",
        "C1",
    ]

    light_t_values = np.linspace(
        0,
        1,
        6
    )

    for (
        level,
        t
    ) in zip(
        light_levels[1:],
        light_t_values[1:]
    ):

        L_param = cubic_bezier(
            t,
            *model[
                "light_L"
            ]
        )

        C_ratio = cubic_bezier(
            t,
            *model[
                "light_C"
            ]
        )

        H_delta = cubic_bezier(
            t,
            *model[
                "light_H"
            ]
        )

        # ------------------------------------------------
        # L 重建公式（区分 Light / Dark Mode）
        #
        # Light Mode：C6 → C1 为核心色 → 浅色
        #     L = brand_L + L_progress * (100 - brand_L)
        #
        # Dark Mode：C6 → C1 为核心色 → 深色
        #     L = brand_L * L_ratio
        #
        # 对参数做 clip，防止 Bezier overshoot
        # ------------------------------------------------
        if mode == "dark":

            # Dark Mode：C6 → C1 为核心色 → 深色
            L_ratio = float(
                np.clip(
                    L_param,
                    0.0,
                    1.0
                )
            )

            L = (
                brand_L
                *
                L_ratio
            )

        else:

            L_progress = float(
                np.clip(
                    L_param,
                    0.0,
                    0.98
                )
            )

            L = (
                brand_L

                +

                L_progress
                *
                (
                    100
                    -
                    brand_L
                )
            )

        C = (
            brand_C
            *
            C_ratio
        )

        H = (
            brand_H
            +
            H_delta
        ) % 360

        # 防止 Bezier overshoot 导致 L 接近 100（纯白）
        L = float(
            np.clip(
                L,
                1.0,
                98.0
            )
        )

        (
            final_hex,
            final_lch
        ) = (
            lch_to_hex_gamut_safe([
                L,
                C,
                H
            ])
        )

        rows.append({

            "Level":
                level,

            "HEX":
                final_hex,

            "L":
                round(
                    final_lch[0],
                    4
                ),

            "C":
                round(
                    final_lch[1],
                    4
                ),

            "H":
                round(
                    final_lch[2]
                    %
                    360,
                    4
                ),

        })

    return pd.DataFrame(
        rows
    )


# ============================================================
# 17b. 同时生成 Light + Dark Palette
# ============================================================

def generate_palettes(
    brand_color
):
    """一次生成 Light Palette 和 Dark Palette。

    返回: (df_light, df_dark)
    """

    df_light = generate_palette(
        brand_color,
        mode="light"
    )

    df_dark = generate_palette(
        brand_color,
        mode="dark"
    )

    return df_light, df_dark


# ============================================================
# 18. 生成色卡图片
# ============================================================

def create_palette_image(
    df,
    image_path,
    title=None
):

    fig_height = 6 if title else 5

    fig, ax = plt.subplots(
        figsize=(
            15,
            fig_height
        )
    )

    if title:

        fig.suptitle(
            title,
            fontsize=16,
            fontweight="bold",
            y=0.98
        )

    ax.set_xlim(
        0,
        10
    )

    ax.set_ylim(
        0,
        1
    )

    ax.axis(
        "off"
    )

    for i, row in df.iterrows():

        color = (
            row[
                "HEX"
            ]
        )

        rgb = (
            hex_to_rgb(
                color
            )
        )

        luminance = (
            0.2126
            *
            rgb[0]

            +

            0.7152
            *
            rgb[1]

            +

            0.0722
            *
            rgb[2]
        )

        text_color = (
            "white"
            if luminance < 0.55
            else
            "black"
        )

        ax.add_patch(

            plt.Rectangle(

                (
                    i,
                    0
                ),

                1,
                1,

                facecolor=color

            )

        )

        ax.text(
            i + 0.5,
            0.61,
            row["Level"],
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color=text_color
        )

        ax.text(
            i + 0.5,
            0.47,
            color,
            ha="center",
            va="center",
            fontsize=9,
            color=text_color
        )

        ax.text(
            i + 0.5,
            0.33,
            f"L {row['L']:.1f}",
            ha="center",
            va="center",
            fontsize=7,
            color=text_color
        )

        ax.text(
            i + 0.5,
            0.25,
            f"C {row['C']:.1f}",
            ha="center",
            va="center",
            fontsize=7,
            color=text_color
        )

        ax.text(
            i + 0.5,
            0.17,
            f"H {row['H']:.1f}",
            ha="center",
            va="center",
            fontsize=7,
            color=text_color
        )

    plt.tight_layout()

    plt.savefig(
        image_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 19. Main
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "HUE-ADAPTIVE BRAND PALETTE GENERATOR"
        " (Light + Dark Mode)"
    )

    print(
        "=" * 70
    )

    print(
        "\nInput Brand Colour:"
    )

    print(
        BRAND_COLOR
    )

    brand_lch = (
        hex_to_lch(
            BRAND_COLOR
        )
    )

    print(
        "\nBrand LCH:"
    )

    print(
        f"L = "
        f"{brand_lch[0]:.4f}"
    )

    print(
        f"C = "
        f"{brand_lch[1]:.4f}"
    )

    print(
        f"H = "
        f"{brand_lch[2]:.4f}"
    )

    # ========================================================
    # 生成 Light / Dark Palette
    # ========================================================

    df_light = generate_palette(
        BRAND_COLOR,
        mode="light"
    )

    df_dark = generate_palette(
        BRAND_COLOR,
        mode="dark"
    )

    # ========================================================
    # C6 (6号基准色) HSB 对比
    # ========================================================

    (
        dark_c6_hex,
        hsb_light,
        hsb_dark,
    ) = compute_dark_c6(
        BRAND_COLOR
    )

    light_c6_hex = (
        BRAND_COLOR.upper()
    )

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "C6 6号基准色 HSB"
    )

    print(
        "=" * 70
    )

    print(
        "\nLight Mode C6:"
    )

    print(
        f"  HEX: {light_c6_hex}"
    )

    print(
        f"  HSB: "
        f"H={hsb_light[0]:.2f}°  "
        f"S={hsb_light[1]:.2f}%  "
        f"B={hsb_light[2]:.2f}%"
    )

    print(
        "\nDark Mode C6:"
    )

    print(
        f"  HEX: {dark_c6_hex}"
    )

    print(
        f"  HSB: "
        f"H={hsb_dark[0]:.2f}°  "
        f"S={hsb_dark[1]:.2f}%  "
        f"B={hsb_dark[2]:.2f}%"
    )

    print(
        "\nH / S / B 变化值:"
    )

    print(
        f"  ΔH = "
        f"{hsb_dark[0] - hsb_light[0]:.2f}°"
    )

    print(
        f"  ΔS = "
        f"{hsb_dark[1] - hsb_light[1]:.2f}%"
    )

    print(
        f"  ΔB = "
        f"{hsb_dark[2] - hsb_light[2]:.2f}%"
    )

    # ========================================================
    # 输出色板
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "LIGHT MODE PALETTE"
    )

    print(
        "=" * 70
    )

    print(
        df_light.to_string(
            index=False
        )
    )

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "DARK MODE PALETTE"
    )

    print(
        "=" * 70
    )

    print(
        df_dark.to_string(
            index=False
        )
    )

    # ========================================================
    # 保存 CSV
    # ========================================================

    csv_path, base_image_path = (
        get_next_output_paths()
    )

    df_light_out = df_light.copy()
    df_light_out["Mode"] = "Light"

    df_dark_out = df_dark.copy()
    df_dark_out["Mode"] = "Dark"

    df_combined = pd.concat(
        [df_light_out, df_dark_out],
        ignore_index=True
    )

    df_combined.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # 生成色卡 PNG
    # ========================================================

    light_image_path = (
        IMAGE_FOLDER
        /
        (base_image_path.stem + "_light.png")
    )

    dark_image_path = (
        IMAGE_FOLDER
        /
        (base_image_path.stem + "_dark.png")
    )

    create_palette_image(
        df_light,
        light_image_path,
        title="Light Mode"
    )

    create_palette_image(
        df_dark,
        dark_image_path,
        title="Dark Mode"
    )

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "OUTPUT"
    )

    print(
        "=" * 70
    )

    print(
        f"\nCSV:        {csv_path}"
    )

    print(
        f"Light PNG:  {light_image_path}"
    )

    print(
        f"Dark PNG:   {dark_image_path}"
    )


if __name__ == "__main__":
    main()
