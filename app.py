import streamlit as st

st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 ORBIT AI")
st.subheader("Open-World AI — V0.1")

st.write(
    "من ORBIT هستم؛ یک هوش مصنوعی قابل توسعه "
    "برای تحقیق، برنامه‌ریزی، ساخت و اجرای پروژه‌ها."
)

goal = st.text_area(
    "🎯 هدف خود را به ORBIT بده",
    placeholder="مثلاً: یک ایده کسب‌وکار اینترنتی برای من پیدا کن."
)

if st.button("🚀 Start ORBIT"):
    if goal.strip():
        st.success("هدف دریافت شد.")
        st.write("هدف شما:")
        st.write(goal)
    else:
        st.warning("لطفاً ابتدا یک هدف وارد کنید.")
