


import os
import sys
from io import BytesIO

import streamlit as st
from PIL import Image, ImageEnhance, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "orbit-ai"))

from core.planner import create_plan

st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #0b1020, #111827);
}
[data-testid="stSidebar"] {
    background: #101827;
    border-right: 1px solid #293449;
}
.stButton > button,
.stDownloadButton > button {
    border-radius: 12px;
    min-height: 42px;
}
div[data-testid="stMetric"] {
    background: #182235;
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "خانه"
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.markdown("# 🌌 ORBIT AI")
st.sidebar.caption("دستیار هوشمند چندمنظوره")
st.sidebar.divider()

pages = [
    "خانه",
    "دستیار و برنامه‌ریز",
    "ویرایش عکس",
    "ابزارهای ویدئو",
    "ساخت تصویر",
    "پروژه‌های ذخیره‌شده",
]

for item in pages:
    if st.sidebar.button(item, use_container_width=True):
        st.session_state.page = item

st.sidebar.divider()
st.sidebar.caption("ORBIT AI · V1.1")
page = st.session_state.page

if page == "خانه":
    st.title("🌌 ORBIT AI")
    st.subheader("چه کاری می‌خواهی انجام بدهی؟")
    st.write("برنامه‌ریزی، ویرایش عکس و ابزارهای رسانه‌ای در یک محیط.")

    c1, c2, c3 = st.columns(3)
    c1.metric("ابزارهای اصلی", "4")
    c2.metric("برنامه‌های این نشست", len(st.session_state.history))
    c3.metric("برنامه‌ریز", "آفلاین")

    st.divider()
    left, right = st.columns(2)

    with left:
        if st.button("🧠 دستیار و برنامه‌ریز", use_container_width=True):
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
        placeholder="مثلاً یک برنامه ۳۰ روزه برای یادگیری پایتون بساز.",
    )

    if st.button("ساخت برنامه", type="primary"):
        if not goal.strip():
            st.warning("ابتدا هدفت را وارد کن.")
        else:
            try:
                result = create_plan(goal.strip())
                st.session_state.history.insert(
                    0, {"goal": goal.strip(), "result": result}
                )
                st.success("برنامه آماده شد.")
                st.write("حالت اجرا:", result.get("mode", "offline"))

                if result.get("category"):
                    st.write("دسته‌بندی:", result["category"])
                if result.get("duration"):
                    st.write("مدت‌زمان:", result["duration"])

                for i, step in enumerate(result.get("steps", []), 1):
                    st.write(f"{i}. {step}")

                if result.get("plan"):
                    st.write(result["plan"])
                if result.get("message"):
                    st.info(result["message"])

            except Exception as error:
                st.error(f"خطا در ساخت برنامه: {error}")

elif page == "ویرایش عکس":
    st.title("🖼️ ویرایش حرفه‌ای عکس")
    st.caption("فیلتر، تنظیم نور و رنگ، چرخش، برش و ذخیره")

    uploaded = st.file_uploader(
        "عکس را انتخاب کن",
        type=["png", "jpg", "jpeg", "webp"],
        key="orbit_photo_v11",
    )

    if uploaded:
        try:
            original = ImageOps.exif_transpose(
                Image.open(uploaded)
            ).convert("RGB")

            preset = st.selectbox(
                "فیلتر آماده",
                [
                    "طبیعی",
                    "سیاه‌وسفید سینمایی",
                    "سینمایی گرم",
                    "سینمایی سرد",
                ],
            )

            a, b = st.columns(2)
            with a:
                brightness = st.slider("روشنایی", 0.3, 2.0, 1.0, 0.1)
                contrast = st.slider("کنتراست", 0.3, 2.0, 1.0, 0.1)
            with b:
                saturation = st.slider("اشباع رنگ", 0.0, 2.0, 1.0, 0.1)
                sharpness = st.slider("وضوح", 0.0, 3.0, 1.0, 0.1)

            rotation = st.slider("چرخش", -180, 180, 0, 1)

            ratio_name = st.selectbox(
                "ابعاد خروجی",
                [
                    "بدون برش",
                    "استوری و ریلز 9:16",
                    "پست عمودی 4:5",
                    "مربع 1:1",
                    "افقی 16:9",
                ],
            )

            edited = original.rotate(
                rotation,
                resample=Image.Resampling.BICUBIC,
                expand=True,
            )

            if preset == "سیاه‌وسفید سینمایی":
                edited = ImageOps.grayscale(edited).convert("RGB")
                edited = ImageEnhance.Contrast(edited).enhance(1.2)
            elif preset == "سینمایی گرم":
                overlay = Image.new("RGB", edited.size, (255, 190, 120))
                edited = Image.blend(edited, overlay, 0.10)
                edited = ImageEnhance.Contrast(edited).enhance(1.08)
            elif preset == "سینمایی سرد":
                overlay = Image.new("RGB", edited.size, (110, 165, 220))
                edited = Image.blend(edited, overlay, 0.08)
                edited = ImageEnhance.Contrast(edited).enhance(1.08)

            edited = ImageEnhance.Brightness(edited).enhance(brightness)
            edited = ImageEnhance.Contrast(edited).enhance(contrast)
            edited = ImageEnhance.Color(edited).enhance(saturation)
            edited = ImageEnhance.Sharpness(edited).enhance(sharpness)

            ratios = {
                "استوری و ریلز 9:16": 9 / 16,
                "پست عمودی 4:5": 4 / 5,
                "مربع 1:1": 1.0,
                "افقی 16:9": 16 / 9,
            }

            if ratio_name != "بدون برش":
                target = ratios[ratio_name]
                width, height = edited.size

                if width / height > target:
                    new_width = int(height * target)
                    left = (width - new_width) // 2
                    edited = edited.crop((left, 0, left + new_width, height))
                else:
                    new_height = int(width / target)
                    top = (height - new_height) // 2
                    edited = edited.crop((0, top, width, top + new_height))

            st.divider()
            st.subheader("مقایسه قبل و بعد")
            col1, col2 = st.columns(2)
            col1.image(original, caption="عکس اصلی", use_container_width=True)
            col2.image(edited, caption="عکس ویرایش‌شده", use_container_width=True)
            st.caption(f"ابعاد نهایی: {edited.width} × {edited.height}")

            jpg = BytesIO()
            edited.save(jpg, format="JPEG", quality=95)

            png = BytesIO()
            edited.save(png, format="PNG")

            d1, d2 = st.columns(2)
            d1.download_button(
                "⬇️ ذخیره JPG",
                data=jpg.getvalue(),
                file_name="orbit_edited.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )
            d2.download_button(
                "⬇️ ذخیره PNG",
                data=png.getvalue(),
                file_name="orbit_edited.png",
                mime="image/png",
                use_container_width=True,
            )

            st.info("این ابزار نور، رنگ و کادر را تغییر می‌دهد؛ چهره را با هوش مصنوعی بازسازی نمی‌کند.")

        except Exception as error:
            st.error(f"ویرایش عکس با خطا روبه‌رو شد: {error}")

elif page == "ابزارهای ویدئو":
    st.title("🎬 ابزارهای ویدئو")
    video = st.file_uploader(
        "ویدئو را انتخاب کن",
        type=["mp4", "mov", "avi", "webm"],
    )

    if video:
        st.video(video)
        st.info(
            "پیش‌نمایش ویدئو فعال است. برش و خروجی MP4 هنوز "
            "به موتور پردازش ویدئو مانند FFmpeg نیاز دارد."
        )

elif page == "ساخت تصویر":
    st.title("✨ ساخت تصویر")
    prompt = st.text_area(
        "توصیف تصویر",
        placeholder="مثلاً یک خیابان سینمایی در تهران دهه ۱۹۸۰...",
    )
    st.info(
        "این بخش هنوز به مدل تولید تصویر متصل نیست؛ "
        "واردکردن توضیح به‌تنهایی تصویر تولید نمی‌کند."
    )

elif page == "پروژه‌های ذخیره‌شده":
    st.title("📁 برنامه‌های این نشست")

    if not st.session_state.history:
        st.info("هنوز برنامه‌ای ثبت نشده است.")
    else:
        for item in st.session_state.history:
            with st.expander(item["goal"]):
                st.json(item["result"])

st.divider()
st.caption(
    "ORBIT AI V1.1 · ویرایش عکس و برنامه‌ریزی فعال؛ "
    "تدوین پیشرفته و تولید تصویر نیازمند موتورهای مربوطه هستند."
)
