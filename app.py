import streamlit as st
import pandas as pd
import sys
from io import StringIO
import datetime
from astral.sun import sun
from astral import LocationInfo

# 导入本地 paipan.py 的所有功能
import paipan as core

# ===================== 用 astral 替换 ephem 的日出日落 =====================
def 获取日出日落_astral(经度, 纬度, 年, 月, 日):
    try:
        地点 = LocationInfo()
        地点.longitude = 经度
        地点.latitude = 纬度
        地点.timezone = "Asia/Shanghai"
        日期 = datetime.date(年, 月, 日)
        日出 = sun(地点.observer, date=日期, tzinfo=地点.timezone)['sunrise']
        日落 = sun(地点.observer, date=日期, tzinfo=地点.timezone)['sunset']
        return (日出, 日落)
    except:
        return None, None

# 替换 core 中的获取日出日落
core.获取日出日落 = 获取日出日落_astral

# ===================== 重定向 print 捕获日志 =====================
日志缓冲区 = StringIO()
原_stdout = sys.stdout
sys.stdout = 日志缓冲区

def 排盘_捕获日志(年, 月, 日, 时, 分, 地名, 性别):
    日志缓冲区.seek(0)
    日志缓冲区.truncate()
    try:
        结果, 错误 = core.排盘(年, 月, 日, 时, 分, 地名, 性别)
        日志内容 = 日志缓冲区.getvalue()
        if isinstance(结果, dict):
            结果['日志'] = 日志内容
        return 结果, 错误, 日志内容
    except Exception as e:
        日志内容 = 日志缓冲区.getvalue()
        return None, str(e), 日志内容

# 恢复 stdout（其实不需要，但为了以防万一，我们可以保持重定向）
# 不需要恢复，因为 Streamlit 运行期间持续捕获

# ===================== Streamlit UI =====================
st.set_page_config(
    page_title="盲派命理排盘系统",
    page_icon="🧧",
    layout="wide"
)

st.title("🧧 盲派命理排盘系统")
st.markdown("支持公历/农历输入，真太阳时校正")

st.markdown("---")
st.subheader("📋 输入出生信息")

col1, col2, col3 = st.columns(3)
with col1:
    历法 = st.radio("选择历法", ["公历", "农历"], horizontal=True)

if 历法 == "公历":
    col1, col2, col3 = st.columns(3)
    with col1:
        年 = st.number_input("年份", min_value=1900, max_value=2100, value=1995)
    with col2:
        月 = st.number_input("月份", min_value=1, max_value=12, value=12)
    with col3:
        日 = st.number_input("日期", min_value=1, max_value=31, value=4)
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        年 = st.number_input("农历年份", min_value=1900, max_value=2100, value=1995)
    with col2:
        月 = st.number_input("农历月份", min_value=1, max_value=12, value=12)
    with col3:
        日 = st.number_input("农历日期", min_value=1, max_value=30, value=4)
    闰月 = st.checkbox("闰月")
    if st.button("农历转公历"):
        公历日期 = core.农历转公历(年, 月, 日, 闰月)
        if 公历日期:
            st.success(f"✅ 公历：{公历日期.strftime('%Y年%m月%d日')}")
        else:
            st.error("转换失败，请检查输入")

col1, col2, col3 = st.columns(3)
with col1:
    时输入 = st.text_input("出生时辰（如 6、6:25、6.25）", value="6")
    时, 分 = core.解析时辰(时输入)
    st.caption(f"解析结果：{时}点{分}分")
with col2:
    地名 = st.text_input("出生地（如 北京、广州、泉州）", value="泉州")
with col3:
    性别 = st.radio("性别", ["男", "女"], horizontal=True)

if st.button("🧧 开始排盘", type="primary", use_container_width=True):
    with st.spinner("排盘中..."):
        if 历法 == "农历":
            公历日期 = core.农历转公历(年, 月, 日, 闰月)
            if 公历日期:
                年, 月, 日 = 公历日期.year, 公历日期.month, 公历日期.day
                st.success(f"✅ 农历转公历：{公历日期.strftime('%Y-%m-%d')}")
            else:
                st.error("农历转换失败，请检查输入")
                st.stop()
        结果, 错误, 日志 = 排盘_捕获日志(年, 月, 日, 时, 分, 地名, 性别)
        if 错误:
            st.error(错误)
            st.stop()

        st.markdown("---")
        st.subheader("📊 七柱汇总表")
        df = pd.DataFrame(结果['七柱表格'])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("🚀 大运流年表")
        st.caption(f"起运岁数：{结果['起运岁数']} 岁，起运年份：{结果['起运年份']} 年")
        df_da = pd.DataFrame(结果['大运表格'])
        st.dataframe(df_da, use_container_width=True, hide_index=True)

        # 展开查看计算过程
        with st.expander("📋 查看详细计算过程"):
            if 日志:
                st.text(日志)
            else:
                st.info("暂无详细日志")

        csv1 = df.to_csv(index=False).encode('utf-8-sig')
        csv2 = df_da.to_csv(index=False).encode('utf-8-sig')
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载七柱表 (CSV)",
                data=csv1,
                file_name=f"七柱表_{年}_{月}_{日}.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="📥 下载大运表 (CSV)",
                data=csv2,
                file_name=f"大运表_{年}_{月}_{日}.csv",
                mime="text/csv"
            )
        st.success("✅ 排盘完成！")
