
import streamlit as st
import pandas as pd
import datetime
import io
import contextlib

import paipan


st.set_page_config(
    page_title="能掐会算",
    page_icon="☯",
    layout="wide"
)


def capture_output(func, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args)
    return result, buffer.getvalue()


def lunar_to_solar(year, month, day, leap):
    result = paipan.农历转公历(year, month, day, leap)
    if result is None:
        raise Exception("农历转换失败")
    return result


def make_chart(year, month, day, hour, minute, city, gender):

    lat, lon = paipan.地名转经纬度(city)

    if lat is None:
        raise Exception("出生城市不存在")


    calendar = paipan.查万年历(
        year,
        month,
        day
    )


    year_pillar = calendar["年柱"]
    day_pillar = calendar["日柱"]

    year_gan = year_pillar[0]


    month_result, month_log = capture_output(
        paipan.校正月柱,
        year,
        month,
        day,
        lat,
        year_gan
    )

    # 修正：校正月柱返回(月柱, 节令)
    month_pillar = month_result[0]


    time_result, time_log = capture_output(
        paipan.校正时柱,
        lon,
        lat,
        year,
        month,
        day,
        hour,
        minute,
        year_gan
    )

    # 修正：校正时柱返回(时柱, 真太阳时)
    time_pillar = time_result[0]


    day_result, day_log = capture_output(
        paipan.子时换日,
        time_pillar,
        day_pillar,
        year,
        month,
        day
    )

    day_pillar = day_result[0]


    month_gan = month_pillar[0]
    month_zhi = month_pillar[1]
    time_zhi = time_pillar[1]


    tai = paipan.计算胎宫(
        month_gan,
        month_zhi
    )


    ming_zhi = paipan.计算命宫(
        month_zhi,
        time_zhi
    )

    shen_zhi = paipan.计算身宫(
        month_zhi,
        time_zhi
    )


    ming = (
        paipan.计算命宫天干(
            year_gan,
            ming_zhi
        )
        +
        ming_zhi
    )


    shen = (
        paipan.计算身宫天干(
            year_gan,
            shen_zhi
        )
        +
        shen_zhi
    )


    pillars = [
        ("年柱", year_pillar),
        ("月柱", month_pillar),
        ("日柱", day_pillar),
        ("时柱", time_pillar),
        ("胎宫", tai),
        ("命宫", ming),
        ("身宫", shen)
    ]


    rows = []

    for name, value in pillars:

        gan = value[0]
        zhi = value[1]

        rows.append({
            "柱位": name,
            "天干": gan,
            "天干十神": paipan.计算十神(
                day_pillar[0],
                gan
            ),
            "天干串宫压运": paipan.计算天干串宫压运神(
                day_pillar[0],
                gan
            ),
            "地支": zhi,
            "地支十神": paipan.计算地支十神(
                day_pillar[0],
                zhi
            ),
            "地支串宫压运": paipan.计算串宫压运神(
                day_pillar[0],
                zhi
            ),
            "纳音": paipan.计算纳音(
                gan,
                zhi
            )
        })


    dayun = paipan.计算大运(
        month_pillar,
        gender,
        year_gan
    )


    return {
        "table": pd.DataFrame(rows),
        "dayun": dayun,
        "formula":
            month_log
            + "\n"
            + time_log
            + "\n"
            + day_log
    }



st.title("☯ 能掐会算 - 命理排盘系统")


with st.form("paipan"):

    mode = st.radio(
        "出生历法",
        ["公历", "农历"],
        horizontal=True
    )


    c1, c2, c3 = st.columns(3)

    with c1:
        year = st.number_input("年份", 1900, 2100, 1990)
        month = st.number_input("月份", 1, 12, 1)
        day = st.number_input("日期", 1, 31, 1)

    with c2:
        hour = st.number_input("时", 0, 23, 12)
        minute = st.number_input("分", 0, 59, 0)
        gender = st.selectbox(
            "性别",
            ["男", "女"]
        )

    with c3:
        city = st.text_input(
            "出生城市",
            "北京"
        )

        leap = False

        if mode == "农历":
            leap = st.checkbox("闰月")


    submit = st.form_submit_button(
        "开始排盘"
    )


if submit:

    try:

        if mode == "农历":

            solar = lunar_to_solar(
                year,
                month,
                day,
                leap
            )

            year = solar.year
            month = solar.month
            day = solar.day


        result = make_chart(
            year,
            month,
            day,
            hour,
            minute,
            city,
            gender
        )


        tab1, tab2, tab3 = st.tabs(
            [
                "七柱排盘",
                "大运",
                "计算公式"
            ]
        )


        with tab1:
            st.dataframe(
                result["table"],
                use_container_width=True
            )


        with tab2:

            st.table(
                pd.DataFrame(
                    {
                        "序号": range(1, len(result["dayun"])+1),
                        "大运": result["dayun"]
                    }
                )
            )


        with tab3:

            st.text(
                result["formula"]
            )


    except Exception as e:

        st.error(
            f"排盘失败：{e}"
        )
