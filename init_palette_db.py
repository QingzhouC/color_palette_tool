"""
初始化训练色卡数据库 (SQLite)

运行此脚本会创建 / 重建 palettes.db，
将所有参考色卡写入 reference_palettes 表。

包含 Light Mode 和 Dark Mode 两套训练色卡，
通过 mode 字段区分。

用法:
    python3 init_palette_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "palettes.db"

# ============================================================
# 训练色卡数据
#
# 全部按照 C10 → C1
# ============================================================

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
# Light Mode 训练色卡
#
# C10 = 最深, C1 = 最浅
# ============================================================

REFERENCE_PALETTES = {

    "blue": [
        "#001A4D",  # C10
        "#072567",  # C9
        "#0C399C",  # C8
        "#0E4FD4",  # C7
        "#105CF4",  # C6
        "#1274FE",  # C5
        "#6298FF",  # C4
        "#A0BFFF",  # C3
        "#D0E0FF",  # C2
        "#E8F0FF",  # C1
    ],

    "red": [
        "#4D0006",
        "#66080E",
        "#9B141D",
        "#D3202D",
        "#F42738",
        "#FF4858",
        "#FF7B84",
        "#FFADB3",
        "#FFD5D8",
        "#FFE8EA",
    ],

    "pink": [
        "#4D0040",
        "#660255",
        "#96057E",
        "#C908A9",
        "#E60FC2",
        "#EB47CE",
        "#F47DDD",
        "#FCAEED",
        "#FFD5F7",
        "#FFE8FB",
    ],

    "green": [
        "#004D12",
        "#035F17",
        "#01801F",
        "#00A426",
        "#00B82B",
        "#34C44D",
        "#6CD67D",
        "#A3EAAF",
        "#D1F9D9",
        "#E8FFED",
    ],

    "yellow": [
        "#4D4000",
        "#685702",
        "#9C8202",
        "#D4B000",
        "#F4CB00",
        "#F4D339",
        "#F8DF6F",
        "#FCECA4",
        "#FFF6D1",
        "#FFFBE8",
    ],

    "cyan": [
        "#00404D",
        "#035667",
        "#068199",
        "#07AECE",
        "#0FC8ED",
        "#4AD0EE",
        "#82DDF1",
        "#B2EBF8",
        "#D6F6FD",
        "#E8FBFF",
    ],

    "orange": [
        "#4D2700",
        "#683606",
        "#9C520A",
        "#D4700D",
        "#F48210",
        "#F69430",
        "#FDB063",
        "#FFCE9C",
        "#FFE8CE",
        "#FFF4E8",
    ],

    "light_blue": [
        "#00274D",
        "#083667",
        "#0B529C",
        "#0E70D4",
        "#1082F4",
        "#1E94FA",
        "#66B1FE",
        "#A2CFFF",
        "#D1E8FF",
        "#E8F4FF",
    ],
    
    "purple_blue": [
        "#00044D",
        "#141167",
        "#2E2A9B",
        "#4645D3",
        "#4E56F4",
        "#5F6CFC",
        "#898FFF",
        "#B4B7FF",
        "#D7D9FF",
        "#E8E9FF",
    ],

    "purple": [
        "#33004D",
        "#460268",
        "#6A069C",
        "#910BD4",
        "#A810F4",
        "#B840F8",
        "#CF75FD",
        "#E4AAFF",
        "#F2D4FF",
        "#F7E8FF",
    ],

    "yellow2": [
        "#4d3300",
        "#744e01",
        "#996600",
        "#c08002",
        "#e69900",
        "#ffbb33",
        "#ffcc66",
        "#ffdd99",
        "#ffe9bd",
        "#fff2d8",
    ],

    "green2": [
        "#003022",
        "#003526",
        "#004531",
        "#005e43",
        "#007855",
        "#009267",
        "#0dbd89",
        "#2fddaa",
        "#99f3d9",
        "#caffef",
    ],

    "green3": [
        "#003c04",
        "#004d09",
        "#027011",
        "#0c9919",
        "#14b822",
        "#39cb28",
        "#6bdd53",
        "#9aed85",
        "#c3f7b6",
        "#e1fadb",
    ],

    "yellow3": [
        "#574800",
        "#705d00",
        "#947b00",
        "#c2a100",
        "#e0bb00",
        "#f4cb00",
        "#f8d426",
        "#f9de58",
        "#fbe784",
        "#fdefb0",
    ],

     "green4": [
        "#032a07",
        "#042f07",
        "#043608",
        "#08550f",
        "#117019",
        "#26932f",
        "#39b844",
        "#4ddc59",
        "#9befa2",
        "#d0fcd4",
    ],
}


# ============================================================
# Dark Mode 训练色卡
#
# C10 = 最浅, C1 = 最深
# 与 Light Mode 的亮度趋势相反
# ============================================================

DARK_REFERENCE_PALETTES = {

    "dark_green": [
        "#E8FFED",  # C10
        "#CAF7D3",  # C9
        "#92E6A2",  # C8
        "#52D16E",  # C7
        "#27C44C",  # C6
        "#24B443",  # C5
        "#1C9635",  # C4
        "#127625",  # C3
        "#075B19",  # C2
        "#004D12",  # C1
    ],

    "dark_cyan": [
        "#E8FBFF",  # C10
        "#D1F5FD",  # C9
        "#A3E8F7",  # C8
        "#6ADBF2",  # C7
        "#3ED2F0",  # C6
        "#35BEDA",  # C5
        "#269AB1",  # C4
        "#177185",  # C3
        "#075160",  # C2
        "#00404D",  # C1
    ],

    "dark_light_blue": [
        "#E8F4FF",  # C10
        "#CCE6FF",  # C9
        "#94C8FE",  # C8
        "#54A9FA",  # C7
        "#3695F5",  # C6
        "#3385DE",  # C5
        "#2969B4",  # C4
        "#194B86",  # C3
        "#0A3260",  # C2
        "#00264D",  # C1
    ],

    "dark_blue": [
        "#E8F0FF",  # C10
        "#CBDDFF",  # C9
        "#92B7FF",  # C8
        "#518FFD",  # C7
        "#3676F5",  # C6
        "#3668DE",  # C5
        "#2C51B3",  # C4
        "#1D3885",  # C3
        "#0D245F",  # C2
        "#001A4D",  # C1
    ],

    "dark_violet": [
        "#E8E9FF",  # C10
        "#D6D7FF",  # C9
        "#B0B3FF",  # C8
        "#8790FB",  # C7
        "#737AF5",  # C6
        "#6A69DD",  # C5
        "#504BB3",  # C4
        "#322B85",  # C3
        "#151260",  # C2
        "#00044D",  # C1
    ],

    "dark_purple": [
        "#F7E8FF",  # C10
        "#F0CDFF",  # C9
        "#DD99FF",  # C8
        "#C65FFA",  # C7
        "#B536F5",  # C6
        "#A32EDE",  # C5
        "#8220B4",  # C4
        "#5E1186",  # C3
        "#410560",  # C2
        "#33004D",  # C1
    ],

    "dark_pink": [
        "#FFE8FB",  # C10
        "#FFCFF6",  # C9
        "#FA9DE9",  # C8
        "#F262D9",  # C7
        "#EB34CC",  # C6
        "#D62CB9",  # C5
        "#AE1F96",  # C4
        "#83106F",  # C3
        "#5F044F",  # C2
        "#4D0040",  # C1
    ],

    "dark_red": [
        "#FFE8EA",  # C10
        "#FFD0D4",  # C9
        "#FFA0A8",  # C8
        "#FE6C79",  # C7
        "#F54C5A",  # C6
        "#DD434C",  # C5
        "#B33137",  # C4
        "#851D21",  # C3
        "#5F0B0F",  # C2
        "#4D0006",  # C1
    ],

    "dark_orange": [
        "#FFF4E8",  # C10
        "#FFE5C8",  # C9
        "#FFC78E",  # C8
        "#F9A855",  # C7
        "#F59536",  # C6
        "#DE852F",  # C5
        "#B56A22",  # C4
        "#864B15",  # C3
        "#603309",  # C2
        "#4D2600",  # C1
    ],

    "dark_yellow": [
        "#FFFBE8",  # C10
        "#FFF5CA",  # C9
        "#FCE994",  # C8
        "#F6DD59",  # C7
        "#F5D431",  # C6
        "#DEBF29",  # C5
        "#B59B1D",  # C4
        "#877210",  # C3
        "#605105",  # C2
        "#4D4000",  # C1
    ],
}


def init_database():
    """创建 / 重建 palettes.db"""

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE reference_palettes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            level     TEXT    NOT NULL,
            hex       TEXT    NOT NULL,
            position  INTEGER NOT NULL,
            mode      TEXT    NOT NULL DEFAULT 'light',
            UNIQUE(name, level, mode)
        )
        """
    )

    rows = []

    # Light Mode 色卡
    for name, colors in REFERENCE_PALETTES.items():

        for position, (level, hex_color) in enumerate(
            zip(LEVELS, colors)
        ):

            rows.append(
                (name, level, hex_color, position, "light")
            )

    # Dark Mode 色卡
    for name, colors in DARK_REFERENCE_PALETTES.items():

        for position, (level, hex_color) in enumerate(
            zip(LEVELS, colors)
        ):

            rows.append(
                (name, level, hex_color, position, "dark")
            )

    cursor.executemany(
        """
        INSERT INTO reference_palettes
            (name, level, hex, position, mode)
        VALUES
            (?, ?, ?, ?, ?)
        """,
        rows,
    )

    conn.commit()

    # --------------------------------------------------------
    # 打印摘要
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT mode, name, COUNT(*) AS count
        FROM reference_palettes
        GROUP BY mode, name
        ORDER BY mode, name
        """
    )

    print(
        "Database created:"
    )

    print(
        DB_PATH
    )

    print(
        "\nPalettes:"
    )

    for mode, name, count in cursor.fetchall():

        print(
            f"  [{mode:5s}] "
            f"{name:20s}"
            f" : "
            f"{count} colors"
        )

    conn.close()


if __name__ == "__main__":
    init_database()
