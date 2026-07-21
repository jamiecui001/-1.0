
# app.py
# Streamlit 前端 - 调用本地 paipan.py 命理排盘核心

import streamlit as st
import datetime
import pandas as pd

import paipan


st.set_page_config(
    page_title="盲派命理排盘系统",
    page_icon="☯",
    layout="wide"
)


def run_paipan(year, month, day, hour, minute, city, gender):
    """调用 paipan.py 核心逻辑"""

    lat, lon = paipan.地名转经纬度(city)

    if lat is None:
        raise ValueError("未找到该城市，请使用 paipan.py 中已有城市名称")

    solar = datetime.datetime(
        year,
        month,
        day,
        hour,
        minute
    )

    初始 = paipan.查万年历(year, month, day)

    年柱 = 初始["年柱"]
    月柱 = 初始["月柱"]
    日柱 = 初始["日柱"]

    年干 = 年柱[0]

    校正月, 调整节令 = paipan.校正月柱(
        year,
        month,
        day,
        lat,
        年干
    )

    校正时 = paipan.校正时柱(
        lon,
        lat,
        year,
        month,
        day,
        hour,
        minute,
        年干
    )

    最终日柱, _ = paipan.子时换日(
        校正时,
        日柱,
        year,
        month,
        day
    )

    月干 = 校正月[0]
    月支 = 校正月[1]
    时支 = 校正时[1]

    胎宫 = paipan.计算胎宫(月干, 月支)

    命宫地支 = paipan.计算命宫(
        月支,
        时支
    )

    身宫地支 = paipan.计算身宫(
        月支,
        时支
    )

    命宫 = (
        paipan.计算命宫天干(
            年干,
            命宫地支
        )
        +
        命宫地支
    )

    身宫 = (
        paipan.计算身宫天干(
            年干,
            身宫地支
        )
        +
        身宫地支
    )

    七柱 = {
        "年柱": 年柱,
        "月柱": 校正月,
        "日柱": 最终日柱,
        "时柱": 校正时,
        "胎宫": 胎宫,
        "命宫": 命宫,
        "身宫": 身宫
    }

    rows = []

    for name, value in 七柱.items():

        tg = value[0]
        dz = value[1]

        rows.append({
            "柱位": name,
            "天干": tg,
            "天干十神": paipan.计算十神(
                最终日柱[0],
                tg
            ),
            "天干压运": paipan.计算天干串宫压运神(
                最终日柱[0],
                tg
            ),
            "地支": dz,
            "地支十神": paipan.计算地支十神(
                最终日柱[0],
                dz
            ),
            "地支压运": paipan.计算串宫压运神(
                最终日柱[0],
                dz
            ),
            "纳音": paipan.计算纳音(
                tg,
                dz
            )
        })

    return pd.DataFrame(rows)


st.title("☯ 盲派命理排盘系统")

st.write(
    "Streamlit 界面版，调用本地 paipan.py 排盘核心"
)


with st.form("paipan_form"):

    c1, c2, c3 = st.columns(3)

    with c1:
        year = st.number_input(
            "出生年份",
            1900,
            2100,
            1995
        )

        month = st.number_input(
            "出生月份",
            1,
            12,
            1
        )

        day = st.number_input(
            "出生日期",
            1,
            31,
            1
        )

    with c2:

        hour = st.number_input(
            "小时",
            0,
            23,
            12
        )

        minute = st.number_input(
            "分钟",
            0,
            59,
            0
        )

        gender = st.selectbox(
            "性别",
            ["男", "女"]
        )

    with c3:

        city = st.text_input(
            "出生城市",
            "北京"
        )


    submit = st.form_submit_button(
        "开始排盘"
    )


if submit:

    try:

        result = run_paipan(
            year,
            month,
            day,
            hour,
            minute,
            city,
            gender
        )

        st.success(
            "排盘完成"
        )

        st.dataframe(
            result,
            use_container_width=True
        )

    except Exception as e:

        st.error(
            f"排盘失败：{e}"
        )

        st.info(
            "请确认 paipan.py 与 app.py 在同一目录，并安装依赖。"
        )
