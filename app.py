import streamlit as st

st.title("🧧 盲派命理排盘系统")
st.write("测试部署成功！")

年 = st.number_input("年份", value=1995)
月 = st.number_input("月份", value=12)
日 = st.number_input("日期", value=4)

if st.button("排盘"):
    st.write(f"你输入的日期是：{年}年{月}月{日}日")
