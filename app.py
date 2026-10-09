

import streamlit as st
import os
import sys
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "orbit-ai")
)

from core.planner import create_plan

st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #0b1020, #111827);
    color: #f8fafc;
}
[data-testid="stSidebar"] {
    background: #101827;
    border-right: 1px solid #293449;
}
h1, h2, h3 {
    color: #e2e8f0;
}
.stButton > button {
    border-radius: 12px;
    min-height: 44px;
    border: 1px solid #334155;
}
div[data-testid="stMetric"] {
    background: #182235;
    padding: 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "خانه"

st.sidebar.markdown("# 🌌 ORBIT AI")
st.sidebar.caption("دستیار هوشمند چندمنظوره")
st.sidebar.divider()

pages = [
    "خانه",
    "دستیار و برنامه‌ریز",
    "ویرایش عکس",
    "ابزارهای ویدئو",
    "ساخت تصویر",
    "پروژه‌های ذخیره‌شده"
]

for name in pages:
    if st.sidebar.button(name, use_container_width=True):
        st.session_state.page = name

st.sidebar.divider()
st.sidebar.caption("ORBIT AI · نسخه 1.0")

page = st.session_state.page

if page == "خانه":
    st.title("🌌 ORBIT AI")
    st.subheader("چه کاری می‌خواهی انجام بدهی؟")
    st.write(
        "یک محیط یکپارچه برای برنامه‌ریزی، "
        "ویرایش رسانه و تولید محتوا."
    )

    a, b, c = st.columns(3)
    a.metric("ابزارهای اصلی", "4")
    b.metric("برنامه‌های ثبت‌شده", len(st.session_state.history))
    c.metric("حالت فعلی", "آفلاین")

    st.divider()
    left, right = st.columns(2)

    with left:
        if st.button("🧠 شروع برنامه‌ریزی", use_container_width=True):
            st.session_state.page = "دستیار و برنامه‌ریز"
            st.rerun()

        if st.button("🖼️ ویرایش عکس", use_container_width=True):
            st.session_state.page = "ویرایش عکس"
            st.rerun()

    with right:
        if st.button("🎬 ابزارهای ویدئو", use_container_width=True):
            st.session_state.page = "ابزارهای ویدئو"
            st.rerun()

        if st.button("✨ ساخت تصویر", use_container_width=True):
            st.session_state.page = "ساخت تصویر"
            st.rerun()

elif page == "دستیار و برنامه‌ریز":
    st.title("🧠 دستیار و برنامه‌ریز")
    goal = st.text_area(
        "هدفت را بنویس",
        placeholder="مثلاً یک برنامه ۳۰ روزه برای یادگیری پایتون بساز."
    )

    if st.button("ساخت برنامه", type="primary"):
        if goal.strip():
            with st.spinner("در حال ساخت برنامه..."):
                result = create_plan(goal)

            st.session_state.history.insert(
                0, {"goal": goal, "result": result}
            )
            st.success("برنامه آماده شد.")

            st.write("حالت اجرا:", result.get("mode", "offline"))
            for i, step in enumerate(result.get("steps", []), 1):
                st.write(f"{i}. {step}")

            if result.get("plan"):
                st.write(result["plan"])

            st.info(result.get("message", ""))
        else:
            st.warning("ابتدا هدفت را وارد کن.")

elif page == "ویرایش عکس":
    st.title("🖼️ ویرایش عکس")
    uploaded = st.file_uploader(
        "عکس را انتخاب کن",
        type=["png", "jpg", "jpeg", "webp"]
    )

    if uploaded:
        original = Image.open(uploaded).convert("RGB")

        brightness = st.slider("روشنایی", 0.3, 2.0, 1.0, 0.1)
        contrast = st.slider("کنتراست", 0.3, 2.0, 1.0, 0.1)
        saturation = st.slider("اشباع رنگ", 0.0, 2.0, 1.0, 0.1)
        sharpness = st.slider("وضوح", 0.0, 3.0, 1.0, 0.1)

        edited = ImageEnhance.Brightness(original).enhance(brightness)
        edited = ImageEnhance.Contrast(edited).enhance(contrast)
        edited = ImageEnhance.Color(edited).enhance(saturation)
        edited = ImageEnhance.Sharpness(edited).enhance(sharpness)

        col1, col2 = st.columns(2)
        col1.image(original, caption="عکس اصلی", use_container_width=True)
        col2.image(edited, caption="عکس ویرایش‌شده", use_container_width=True)

        output = BytesIO()
        edited.save(output, format="JPEG", quality=95)

        st.download_button(
            "⬇️ ذخیره عکس ویرایش‌شده",
            data=output.getvalue(),
            file_name="orbit_edited.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

elif page == "ابزارهای ویدئو":
    st.title("🎬 ابزارهای ویدئو")
    st.write("یک فایل ویدئویی انتخاب کن.")
    video = st.file_uploader(
        "بارگذاری ویدئو",
        type=["mp4", "mov", "avi", "webm"]
    )

    if video:
        st.video(video)
        st.info(
            "پیش‌نمایش ویدئو فعال است. "
            "برای برش، اتصال و خروجی‌گیری باید FFmpeg "
            "به محیط اجرا اضافه شود."
        )

elif page == "ساخت تصویر":
    st.title("✨ ساخت تصویر")
    st.write(
        "این بخش برای اتصال به مدل تولید تصویر آماده شده است."
    )
    prompt = st.text_area(
        "توصیف تصویر",
        placeholder="مثلاً یک خیابان سینمایی در تهران دهه ۱۹۸۰..."
    )
    st.caption(
        "تولید واقعی تصویر هنوز به مدل تصویر و منابع پردازشی "
        "نیاز دارد؛ این بخش در حال حاضر تصویر تولید نمی‌کند."
    )

elif page == "پروژه‌های ذخیره‌شده":
    st.title("📁 پروژه‌های ذخیره‌شده")

    if not st.session_state.history:
        st.info("هنوز برنامه‌ای در این نشست ذخیره نشده است.")
    else:
        for item in st.session_state.history:
            with st.expander(item["goal"]):
                st.json(item["result"])

st.divider()
st.caption(
    "ORBIT AI V1.0 · ابزارهای پایه محلی، "
    "تولید تصویر و تدوین پیشرفته در انتظار اتصال موتورهای مربوطه."
)
