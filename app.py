
import os
import sys
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps

# -----------------------------
# ORBIT AI - Main application
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "orbit-ai"))

from core.planner import create_plan
from video_tools import render_video_tools

st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: #0b1020;
    color: #edf2ff;
}
[data-testid="stSidebar"] {
    background: #10182b;
    border-right: 1px solid #26334f;
}
.block-container {
    max-width: 1150px;
    padding-top: 2rem;
}
.orbit-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: 2px;
}
.orbit-subtitle {
    color: #9baac9;
    font-size: 1rem;
}
.orbit-card {
    padding: 18px;
    border-radius: 16px;
    background: #131d33;
    border: 1px solid #283653;
    margin-bottom: 12px;
}
div.stButton > button {
    border-radius: 10px;
    min-height: 42px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Session state
# -----------------------------
if "orbit_page" not in st.session_state:
    st.session_state.orbit_page = "خانه"

if "orbit_history" not in st.session_state:
    st.session_state.orbit_history = []

if "orbit_last_plan" not in st.session_state:
    st.session_state.orbit_last_plan = None


# -----------------------------
# Sidebar navigation
# -----------------------------
st.sidebar.markdown("## 🌌 ORBIT AI")
st.sidebar.caption("Your personal AI workspace")

page = st.sidebar.radio(
    "منوی اصلی",
    [
        "خانه",
        "دستیار و برنامه‌ریز",
        "ویرایش عکس",
        "ابزارهای ویدئو",
        "ساخت تصویر",
        "پروژه‌های ذخیره‌شده",
    ],
    key="orbit_page",
)

st.sidebar.divider()
st.sidebar.caption("ORBIT AI • Personal Workspace")


# -----------------------------
# Home
# -----------------------------
if page == "خانه":
    st.markdown(
        '<div class="orbit-title">🌌 ORBIT AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="orbit-subtitle">'
        'یک فضای ساده برای برنامه‌ریزی، تولید محتوا و ویرایش رسانه'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            '<div class="orbit-card"><h3>🧠 دستیار</h3>'
            '<p>ساخت برنامه و تقسیم کارها به مراحل کوچک</p></div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            '<div class="orbit-card"><h3>🖼️ تصویر</h3>'
            '<p>تنظیم نور، رنگ، کادر و خروجی عکس</p></div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            '<div class="orbit-card"><h3>🎬 ویدئو</h3>'
            '<p>برش ویدئو و آماده‌سازی فایل MP4</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("شروع سریع")
    left, middle, right = st.columns(3)

    with left:
        if st.button("🧠 بازکردن دستیار", use_container_width=True):
            st.session_state.orbit_page = "دستیار و برنامه‌ریز"
            st.rerun()

    with middle:
        if st.button("🖼️ ویرایش عکس", use_container_width=True):
            st.session_state.orbit_page = "ویرایش عکس"
            st.rerun()

    with right:
        if st.button("🎬 ویرایش ویدئو", use_container_width=True):
            st.session_state.orbit_page = "ابزارهای ویدئو"
            st.rerun()

    st.info(
        "توجه: برنامه‌ریز فعلاً آفلاین است. "
        "ساخت تصویر با هوش مصنوعی و حافظه دائمی هنوز به سرویس‌های "
        "مربوط متصل نشده‌اند."
    )


# -----------------------------
# Planner
# -----------------------------
elif page == "دستیار و برنامه‌ریز":
    st.title("🧠 دستیار و برنامه‌ریز")
    st.write("هدفت را بنویس تا یک برنامه مرحله‌ای دریافت کنی.")

    goal = st.text_area(
        "موضوع یا هدف",
        placeholder="مثلاً برای یادگیری پایتون یک برنامه ۳۰ روزه بساز",
        height=130,
    )

    duration = st.selectbox(
        "مدت برنامه",
        ["بدون تعیین مدت", "۷ روز", "۱۴ روز", "۳۰ روز", "۹۰ روز"],
    )

    if st.button("ساخت برنامه", type="primary"):
        if not goal.strip():
            st.warning("لطفاً ابتدا هدف خود را بنویس.")
        else:
            request = goal.strip()

            if duration != "بدون تعیین مدت":
                request += " برای " + duration

            try:
                with st.spinner("در حال ساخت برنامه..."):
                    result = create_plan(request)

                st.session_state.orbit_last_plan = {
                    "goal": goal.strip(),
                    "duration": duration,
                    "result": result,
                }
                st.session_state.orbit_history.append(
                    st.session_state.orbit_last_plan
                )

                st.success("برنامه آماده شد.")
                st.write(result)

            except Exception as exc:
                st.error("ساخت برنامه ناموفق بود.")
                st.code(str(exc))

    if st.session_state.orbit_last_plan:
        st.divider()
        st.subheader("آخرین برنامه")
        st.write(st.session_state.orbit_last_plan["goal"])


# -----------------------------
# Image editor
# -----------------------------
elif page == "ویرایش عکس":
    st.title("🖼️ ویرایش عکس")
    st.caption("تنظیم نور، کنتراست، رنگ، وضوح و نسبت تصویر")

    uploaded_image = st.file_uploader(
        "عکس را انتخاب کن",
        type=["jpg", "jpeg", "png", "webp"],
        key="orbit_image_upload",
    )

    if uploaded_image:
        original = Image.open(uploaded_image).convert("RGB")

        preset = st.selectbox(
            "فیلتر",
            ["طبیعی", "سیاه‌وسفید سینمایی", "گرم", "سرد"],
        )

        brightness = st.slider("روشنایی", 0.5, 1.8, 1.0, 0.05)
        contrast = st.slider("کنتراست", 0.5, 1.8, 1.0, 0.05)
        saturation = st.slider("اشباع رنگ", 0.0, 2.0, 1.0, 0.05)
        sharpness = st.slider("وضوح", 0.0, 2.0, 1.0, 0.05)
        rotation = st.selectbox(
            "چرخش",
            [0, 90, 180, 270],
        )

        aspect = st.selectbox(
            "نسبت تصویر",
            ["اصلی", "استوری 9:16", "پست 4:5", "مربع 1:1", "افقی 16:9"],
        )

        edited = original.copy()

        if preset == "سیاه‌وسفید سینمایی":
            edited = ImageOps.grayscale(edited).convert("RGB")
            edited = ImageEnhance.Contrast(edited).enhance(1.15)
        elif preset == "گرم":
            r, g, b = edited.split()
            edited = Image.merge(
                "RGB",
                (
                    r.point(lambda x: min(255, int(x * 1.06))),
                    g.point(lambda x: min(255, int(x * 1.02))),
                    b.point(lambda x: int(x * 0.94)),
                ),
            )
        elif preset == "سرد":
            r, g, b = edited.split()
            edited = Image.merge(
                "RGB",
                (
                    r.point(lambda x: int(x * 0.94)),
                    g,
                    b.point(lambda x: min(255, int(x * 1.06))),
                ),
            )

        edited = ImageEnhance.Brightness(edited).enhance(brightness)
        edited = ImageEnhance.Contrast(edited).enhance(contrast)
        edited = ImageEnhance.Color(edited).enhance(saturation)
        edited = ImageEnhance.Sharpness(edited).enhance(sharpness)

        if rotation:
            edited = edited.rotate(rotation, expand=True)

        ratios = {
            "استوری 9:16": (9, 16),
            "پست 4:5": (4, 5),
            "مربع 1:1": (1, 1),
            "افقی 16:9": (16, 9),
        }

        if aspect in ratios:
            edited = ImageOps.fit(
                edited,
                (
                    ratios[aspect][0] * 100,
                    ratios[aspect][1] * 100,
                ),
            )

        before, after = st.columns(2)

        with before:
            st.subheader("قبل")
            st.image(original, use_container_width=True)

        with after:
            st.subheader("بعد")
            st.image(edited, use_container_width=True)

        output_format = st.selectbox("فرمت خروجی", ["JPG", "PNG"])
        from io import BytesIO

        output = BytesIO()

        if output_format == "JPG":
            edited.save(output, format="JPEG", quality=95, optimize=True)
            mime = "image/jpeg"
            filename = "orbit_ai_edited.jpg"
        else:
            edited.save(output, format="PNG", optimize=True)
            mime = "image/png"
            filename = "orbit_ai_edited.png"

        st.download_button(
            "⬇️ دانلود عکس ویرایش‌شده",
            data=output.getvalue(),
            file_name=filename,
            mime=mime,
            use_container_width=True,
        )

    else:
        st.info("برای شروع، یک عکس بارگذاری کن.")


# -----------------------------
# Video tools
# -----------------------------
elif page == "ابزارهای ویدئو":
    try:
        render_video_tools()
    except Exception as exc:
        st.error("بخش ویدئو بارگذاری نشد.")
        st.code(str(exc))
        st.info(
            "بررسی کن که فایل video_tools.py در کنار app.py باشد "
            "و imageio-ffmpeg در requirements.txt ثبت شده باشد."
        )


# -----------------------------
# Image generation placeholder
# -----------------------------
elif page == "ساخت تصویر":
    st.title("✨ ساخت تصویر")
    st.write("شرح تصویر موردنظرت را بنویس.")

    prompt = st.text_area(
        "پرامپت تصویر",
        placeholder="مثلاً پرتره سینمایی با نورپردازی حرفه‌ای...",
        height=150,
    )

    if st.button("آماده‌سازی درخواست"):
        if prompt.strip():
            st.session_state["orbit_image_prompt"] = prompt.strip()
            st.success("پرامپت ذخیره شد.")
            st.code(prompt.strip())
            st.info(
                "برای تولید واقعی تصویر، باید یک مدل یا سرویس تولید تصویر "
                "به برنامه متصل شود."
            )
        else:
            st.warning("ابتدا شرح تصویر را بنویس.")


# -----------------------------
# Saved projects / session history
# -----------------------------
elif page == "پروژه‌های ذخیره‌شده":
    st.title("📁 پروژه‌های ذخیره‌شده")
    st.caption("این فهرست فعلاً فقط در نشست فعلی نگهداری می‌شود.")

    if not st.session_state.orbit_history:
        st.info("هنوز برنامه‌ای در این نشست ساخته نشده است.")
    else:
        for index, item in enumerate(
            reversed(st.session_state.orbit_history), start=1
        ):
            with st.expander(
                f"{index}. {item['goal'][:70]}"
            ):
                st.write("مدت:", item["duration"])
                st.write(item["result"])

    if st.session_state.orbit_history:
        if st.button("پاک‌کردن فهرست این نشست"):
            st.session_state.orbit_history = []
            st.session_state.orbit_last_plan = None
            st.rerun()
