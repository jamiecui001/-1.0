import streamlit as st
import pandas as pd
import sys
import io
from contextlib import redirect_stdout
from paipan import 排盘, 地名转经纬度, 解析时辰, 农历转公历

st.set_page_config(
    page_title="盲派命理排盘系统",
    page_icon="🧧",
    layout="wide"
)

st.title("🧧 盲派命理排盘系统")
st.markdown("支持公历/农历输入，真太阳时校正")

# ===== 包装排盘函数，捕获 print 输出作为日志 =====
def 排盘_带日志(年, 月, 日, 时, 分, 地名, 性别):
    # 创建一个 StringIO 对象来捕获 print 输出
    日志缓冲区 = io.StringIO()
    with redirect_stdout(日志缓冲区):
        结果, 错误 = 排盘(年, 月, 日, 时, 分, 地名, 性别)
    日志内容 = 日志缓冲区.getvalue()
    
    if 结果 is not None:
        结果['日志'] = 日志内容
    return 结果, 错误

st.markdown("---")
st.subheader("📋 输入出生信息")

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
        公历日期 = 农历转公历(年, 月, 日, 闰月)
        if 公历日期:
            st.success(f"✅ 公历：{公历日期.strftime('%Y年%m月%d日')}")
        else:
            st.error("转换失败，请检查输入")

col1, col2, col3 = st.columns(3)
with col1:
    时输入 = st.text_input("出生时辰（如 6、6:25、6.25）", value="6")
    时, 分 = 解析时辰(时输入)
    st.caption(f"解析结果：{时}点{分}分")
with col2:
    地名 = st.text_input("出生地（如 北京、广州、泉州）", value="泉州")
with col3:
    性别 = st.radio("性别", ["男", "女"], horizontal=True)

if st.button("🧧 开始排盘", type="primary", use_container_width=True):
    with st.spinner("排盘中..."):
        if 历法 == "农历":
            公历日期 = 农历转公历(年, 月, 日, 闰月)
            if 公历日期:
                年, 月, 日 = 公历日期.year, 公历日期.month, 公历日期.day
                st.success(f"✅ 农历转公历：{公历日期.strftime('%Y-%m-%d')}")
            else:
                st.error("农历转换失败，请检查输入")
                st.stop()

        # ===== 使用带日志的包装函数 =====
        结果, 错误 = 排盘_带日志(年, 月, 日, 时, 分, 地名, 性别)

        if 错误:
            st.error(错误)
            st.stop()

        st.markdown("---")

        if '原始四柱' in 结果:
            st.subheader("📜 原始四柱（校正前）")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("年柱", 结果['原始四柱']['年柱'])
            with col2:
                st.metric("月柱", 结果['原始四柱']['月柱'])
            with col3:
                st.metric("日柱", 结果['原始四柱']['日柱'])
            with col4:
                st.metric("时柱", 结果['原始四柱']['时柱'])
            st.caption(f"北京时间：{时}点{分}分")

        if '校正后' in 结果:
            st.subheader("🔄 校正后四柱 + 胎命身三垣")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("月柱（校正）", 结果['校正后']['月柱'])
            with col2:
                st.metric("时柱（校正）", 结果['校正后']['时柱'])
            with col3:
                st.metric("日柱（校正）", 结果['校正后']['日柱'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("胎宫", 结果['校正后']['胎宫'])
            with col2:
                st.metric("命宫", 结果['校正后']['命宫'])
            with col3:
                st.metric("身宫", 结果['校正后']['身宫'])

        st.subheader("📊 七柱汇总表")
        df = pd.DataFrame(结果['七柱表格'])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("🚀 大运流年表")
        st.caption(f"起运岁数：{结果['起运岁数']} 岁，起运年份：{结果['起运年份']} 年")
        df_da = pd.DataFrame(结果['大运表格'])
        st.dataframe(df_da, use_container_width=True, hide_index=True)

        with st.expander("📋 查看详细计算过程"):
            if 结果.get('日志'):
                st.text(结果['日志'])
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
