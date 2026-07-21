
import streamlit as st
import pandas as pd
import datetime
import io
import contextlib

import paipan


st.set_page_config(
    page_title="能掐会算 - 命理排盘",
    page_icon="☯",
    layout="wide"
)


def capture_output(func, *args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args)
    return result, buffer.getvalue()


def convert_lunar(year, month, day, leap):
    result = paipan.农历转公历(year, month, day, leap)
    if result is None:
        raise ValueError("农历日期转换失败")
    return result


def calculate(data):

    year = data["year"]
    month = data["month"]
    day = data["day"]
    hour = data["hour"]
    minute = data["minute"]
    city = data["city"]
    gender = data["gender"]

    lat, lon = paipan.地名转经纬度(city)

    if lat is None:
        raise ValueError("城市不存在")

    base = paipan.查万年历(year, month, day)

    year_pillar = base["年柱"]
    day_pillar = base["日柱"]

    year_gan = year_pillar[0]

    month_pillar, month_log = capture_output(
        paipan.校正月柱,
        year,
        month,
        day,
        lat,
        year_gan
    )

    time_pillar, time_log = capture_output(
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


    day_pillar, day_change_log = capture_output(
        paipan.子时换日,
        time_pillar,
        day_pillar,
        year,
        month,
        day
    )


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
        + ming_zhi
    )

    shen = (
        paipan.计算身宫天干(
            year_gan,
            shen_zhi
        )
        + shen_zhi
    )


    columns = []

    seven = [
        ("年柱", year_pillar),
        ("月柱", month_pillar),
        ("日柱", day_pillar),
        ("时柱", time_pillar),
        ("胎宫", tai),
        ("命宫", ming),
        ("身宫", shen)
    ]


    for name, value in seven:

        tg = value[0]
        dz = value[1]

        columns.append({
            "柱位": name,
            "天干": tg,
            "天干十神": paipan.计算十神(day_pillar[0], tg),
            "天干串宫": paipan.计算天干串宫压运神(day_pillar[0], tg),
            "地支": dz,
            "地支十神": paipan.计算地支十神(day_pillar[0], dz),
            "地支串宫": paipan.计算串宫压运神(day_pillar[0], dz),
            "纳音": paipan.计算纳音(tg, dz)
        })


    big_yun = paipan.计算大运(
        month_pillar,
        gender,
        year_gan
    )


    return {
        "table": pd.DataFrame(columns),
        "大运": big_yun,
        "过程": month_log + "\n" + time_log + "\n" + day_change_log
    }



st.title("☯ 能掐会算 - Streamlit排盘系统")


with st.form("form"):

    calendar_type = st.radio(
        "出生历法",
        ["公历", "农历"],
        horizontal=True
    )


    c1,c2,c3 = st.columns(3)

    with c1:
        year = st.number_input("年份",1900,2100,1990)
        month = st.number_input("月份",1,12,1)
        day = st.number_input("日期",1,30,1)


    with c2:
        hour = st.number_input("小时",0,23,12)
        minute = st.number_input("分钟",0,59,0)
        gender = st.selectbox("性别",["男","女"])


    with c3:
        city = st.text_input(
            "出生城市",
            "北京"
        )

        leap = False

        if calendar_type == "农历":
            leap = st.checkbox("闰月")


    submit = st.form_submit_button(
        "开始排盘"
    )


if submit:

    try:

        if calendar_type == "农历":

            solar = convert_lunar(
                year,
                month,
                day,
                leap
            )

            year = solar.year
            month = solar.month
            day = solar.day


        result = calculate({
            "year":year,
            "month":month,
            "day":day,
            "hour":hour,
            "minute":minute,
            "city":city,
            "gender":gender
        })


        tab1,tab2,tab3 = st.tabs(
            [
                "七柱排盘",
                "大运",
                "计算公式"
            ]
        )


        with tab1:

            st.subheader("七柱")

            st.dataframe(
                result["table"],
                use_container_width=True
            )


        with tab2:

            st.subheader("大运")

            yun = []

            for i,x in enumerate(result["大运"]):
                yun.append({
                    "序号":i+1,
                    "大运":x
                })

            st.table(
                pd.DataFrame(yun)
            )


        with tab3:

            st.subheader("计算过程")

            st.text(
                result["过程"]
            )


    except Exception as e:

        st.error(
            f"排盘失败: {e}"
        )
