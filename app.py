

import os
import io
import sys
import json
from datetime import datetime

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps

# --------------------------------------------------
# ORBIT AI - Main Application
# --------------------------------------------------

APP_NAME = "ORBIT AI"

st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Allow imports from the existing project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "orbit-ai")

if os.path.isdir(CORE_DIR):
    sys.path.insert(0, CORE_DIR)

# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0d12;
        color: #f4f5f7;
    }
    [data-testid="stSidebar"] {
        background: #11141c;
        border-right: 1px solid #252a36;
    }
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero {
        padding: 28px;
        border-radius: 22px;
        background: linear-gradient(135deg, #171d2c, #11131b);
        border: 1px solid #2a3040;
        margin-bottom: 24px;
    }
    .hero h1 {
        font-size: 36px;
        margin-bottom: 8px;
    }
    .muted {
        color: #a6adbd;
    }
    div[data-testid="stMetric"] {
        background: #141823;
        border: 1px solid #292f3d;
        border-radius: 14px;
        padding: 16px;
    }
    .stButton button,
    .stDownloadButton button {
        border-radius: 10px;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Session state
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "خانه"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "saved_projects" not in st.session_state:
    st.session_state.saved_projects = []

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def show_header(title, description=""):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <div class="muted">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_to_bytes(image, fmt="PNG", quality=95):
    output = io.BytesIO()

    if fmt.upper() in ("JPG", "JPEG"):
        image = image.convert("RGB")
        image.save(
            output,
            format="JPEG",
            quality=quality,
            optimize=True,
        )
    else:
        image.save(output, format="PNG", optimize=True)

    return output.getvalue()


def crop_to_ratio(image, ratio_name):
    ratios = {
        "بدون برش": None,
        "استوری 9:16": 9 / 16,
        "پست عمودی 4:5": 4 / 5,
        "مربع 1:1": 1.0,
        "افقی 16:9": 16 / 9,
    }

    target = ratios.get(ratio_name)

    if target is None:
        return image

    width, height = image.size
    current = width / height

    if current > target:
        new_width = int(height * target)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    return image


def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "DejaVuSans.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def apply_image_edit(
    original,
    brightness,
    contrast,
    saturation,
    sharpness,
    filter_name,
    rotation,
    flip_horizontal,
    ratio_name,
    blur_amount,
    overlay_text,
    watermark,
):
    image = ImageOps.exif_transpose(original).convert("RGB")

    # Basic adjustments
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Sharpness(image).enhance(sharpness)

    # Presets
    if filter_name == "سیاه‌وسفید":
        image = ImageOps.grayscale(image).convert("RGB")

    elif filter_name == "سینمایی":
        image = ImageEnhance.Contrast(image).enhance(1.15)
        image = ImageEnhance.Color(image).enhance(0.75)

    elif filter_name == "گرم":
        r, g, b = image.split()
        r = r.point(lambda x: min(255, int(x * 1.08)))
        b = b.point(lambda x: int(x * 0.90))
        image = Image.merge("RGB", (r, g, b))

    elif filter_name == "سرد":
        r, g, b = image.split()
        r = r.point(lambda x: int(x * 0.91))
        b = b.point(lambda x: min(255, int(x * 1.08)))
        image = Image.merge("RGB", (r, g, b))

    elif filter_name == "وینتیج":
        r, g, b = image.split()
        r = r.point(lambda x: min(255, int(x * 1.04)))
        g = g.point(lambda x: min(255, int(x * 1.01)))
        b = b.point(lambda x: int(x * 0.90))
        image = Image.merge("RGB", (r, g, b))
        image = ImageEnhance.Color(image).enhance(0.75)

    # Rotation and flip
    if rotation:
        image = image.rotate(
            rotation,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

    if flip_horizontal:
        image = ImageOps.mirror(image)

    # Crop
    image = crop_to_ratio(image, ratio_name)

    # Blur
    if blur_amount > 0:
        image = image.filter(
            ImageFilter.GaussianBlur(radius=blur_amount)
        )

    # Text and watermark
    if overlay_text.strip() or watermark.strip():
        image = image.copy()
        draw = ImageDraw.Draw(image)
        width, height = image.size

        if overlay_text.strip():
            font = load_font(max(16, width // 24))
            bbox = draw.textbbox((0, 0), overlay_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = max(10, (width - text_width) // 2)
            y = max(10, height - text_height - 40)

            draw.text(
                (x + 2, y + 2),
                overlay_text,
                font=font,
                fill=(0, 0, 0),
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )
            draw.text(
                (x, y),
                overlay_text,
                font=font,
                fill=(255, 255, 255),
                stroke_width=1,
                stroke_fill=(30, 30, 30),
            )

        if watermark.strip():
            font = load_font(max(12, width // 45))
            margin = max(12, width // 40)
            bbox = draw.textbbox((0, 0), watermark, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            draw.text(
                (
                    width - text_width - margin,
                    height - text_height - margin,
                ),
                watermark,
                font=font,
                fill=(255, 255, 255),
                stroke_width=1,
                stroke_fill=(0, 0, 0),
            )

    return image


# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------

with st.sidebar:
    st.markdown("# 🚀 ORBIT AI")
    st.caption("Creative AI Workspace")
    st.divider()

    pages = {
        "🏠 خانه": "خانه",
        "💬 دستیار هوشمند": "دستیار هوشمند",
        "🧠 برنامه‌ریز": "برنامه‌ریز",
        "🖼️ ویرایش عکس": "ویرایش عکس",
        "🎬 ابزارهای ویدئو": "ابزارهای ویدئو",
        "✨ ساخت تصویر": "ساخت تصویر",
        "📁 پروژه‌های ذخیره‌شده": "پروژه‌های ذخیره‌شده",
    }

    for label, page_name in pages.items():
        if st.button(
            label,
            key=f"nav_{page_name}",
            use_container_width=True,
        ):
            st.session_state.page = page_name

    st.divider()
    st.caption("ORBIT AI · Personal Creative Studio")

page = st.session_state.page

# --------------------------------------------------
# HOME
# --------------------------------------------------

if page == "خانه":
    show_header(
        "ORBIT AI",
        "فضای کاری یکپارچه برای خلاقیت، عکس، ویدئو و برنامه‌ریزی",
    )

    st.markdown("### فضای کاری شما")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("پروژه‌های این نشست", len(st.session_state.saved_projects))

    with c2:
        st.metric("گفتگوها", len(st.session_state.chat_history))

    with c3:
        st.metric("ابزارهای اصلی", "6")

    st.markdown("### شروع سریع")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("🖼️ شروع ویرایش عکس", use_container_width=True):
            st.session_state.page = "ویرایش عکس"
            st.rerun()

        if st.button("💬 گفتگو با دستیار", use_container_width=True):
            st.session_state.page = "دستیار هوشمند"
            st.rerun()

    with c2:
        if st.button("🎬 ویرایش ویدئو", use_container_width=True):
            st.session_state.page = "ابزارهای ویدئو"
            st.rerun()

        if st.button("🧠 برنامه‌ریز هوشمند", use_container_width=True):
            st.session_state.page = "برنامه‌ریز"
            st.rerun()

    st.info(
        "برای ویرایش عکس، فایل خودت را بارگذاری کن و تنظیمات را تغییر بده. "
        "برای خروجی ویدئو، فایل video_tools.py نیز باید در مخزن موجود باشد."
    )

# --------------------------------------------------
# IMAGE EDITOR
# --------------------------------------------------

elif page == "ویرایش عکس":
    show_header(
        "ویرایش عکس",
        "تنظیم نور و رنگ، فیلتر، برش، وضوح، متن و واترمارک",
    )

    uploaded = st.file_uploader(
        "عکس را انتخاب کن",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_upload",
    )

    if uploaded:
        try:
            original = Image.open(uploaded)
            original = ImageOps.exif_transpose(original).convert("RGB")

            st.markdown("### تنظیمات ویرایش")

            with st.expander("💡 نور و رنگ", expanded=True):
                c1, c2 = st.columns(2)

                with c1:
                    brightness = st.slider(
                        "روشنایی",
                        0.2, 2.0, 1.0, 0.05,
                    )
                    contrast = st.slider(
                        "کنتراست",
                        0.2, 2.0, 1.0, 0.05,
                    )

                with c2:
                    saturation = st.slider(
                        "اشباع رنگ",
                        0.0, 2.0, 1.0, 0.05,
                    )
                    sharpness = st.slider(
                        "وضوح",
                        0.0, 3.0, 1.0, 0.1,
                    )

            c1, c2 = st.columns(2)

            with c1:
                filter_name = st.selectbox(
                    "فیلتر",
                    [
                        "طبیعی",
                        "سینمایی",
                        "سیاه‌وسفید",
                        "گرم",
                        "سرد",
                        "وینتیج",
                    ],
                )

                ratio_name = st.selectbox(
                    "ابعاد تصویر",
                    [
                        "بدون برش",
                        "استوری 9:16",
                        "پست عمودی 4:5",
                        "مربع 1:1",
                        "افقی 16:9",
                    ],
                )

            with c2:
                rotation = st.selectbox(
                    "چرخش",
                    [0, 90, 180, 270],
                    format_func=lambda x: f"{x} درجه",
                )

                flip_horizontal = st.checkbox("قرینه افقی")

                blur_amount = st.slider(
                    "محو کردن تصویر",
                    0.0, 10.0, 0.0, 0.5,
                )

            st.markdown("### متن و واترمارک")

            overlay_text = st.text_input(
                "متن روی عکس",
                placeholder="متن دلخواه...",
            )

            watermark = st.text_input(
                "واترمارک",
                placeholder="مثلاً ORBIT AI",
            )

            edited = apply_image_edit(
                original=original,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                sharpness=sharpness,
                filter_name=filter_name,
                rotation=rotation,
                flip_horizontal=flip_horizontal,
                ratio_name=ratio_name,
                blur_amount=blur_amount,
                overlay_text=overlay_text,
                watermark=watermark,
            )

            st.markdown("### پیش‌نمایش")

            left, right = st.columns(2)

            with left:
                st.caption("عکس اصلی")
                st.image(original, use_container_width=True)

            with right:
                st.caption("عکس ویرایش‌شده")
                st.image(edited, use_container_width=True)

            d1, d2 = st.columns(2)

            with d1:
                st.download_button(
                    "⬇️ دانلود PNG",
                    data=image_to_bytes(edited, "PNG"),
                    file_name="orbit_ai_edited.png",
                    mime="image/png",
                    use_container_width=True,
                )

            with d2:
                st.download_button(
                    "⬇️ دانلود JPG",
                    data=image_to_bytes(edited, "JPEG"),
                    file_name="orbit_ai_edited.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                )

            if st.button("📁 ذخیره نتیجه در پروژه‌های این نشست"):
                st.session_state.saved_projects.append({
                    "name": "ویرایش عکس",
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "details": f"خروجی تصویر {edited.width}×{edited.height}",
                    "image": image_to_bytes(edited, "PNG"),
                })
                st.success("نتیجه تا پایان نشست در فهرست پروژه‌ها ثبت شد.")

            st.caption(
                "توجه: این ابزارها ویرایش پایه انجام می‌دهند؛ "
                "قابلیت‌های پیشرفته‌ای مثل حذف هوشمند اشیا، ماسک و لایه‌های فتوشاپ "
                "در این نسخه پیاده‌سازی نشده‌اند."
            )

        except Exception as exc:
            st.error(f"بازکردن یا ویرایش عکس ناموفق بود: {exc}")

    else:
        st.info("برای شروع، یک عکس بارگذاری کن.")

# --------------------------------------------------
# VIDEO TOOLS
# --------------------------------------------------

elif page == "ابزارهای ویدئو":
    show_header(
        "ابزارهای ویدئو",
        "برش ویدئو، تغییر سرعت، تنظیم رنگ و خروجی MP4",
    )

    try:
        from video_tools import render_video_tools
        render_video_tools()

    except ImportError as exc:
        st.error(
            "فایل video_tools.py یا یکی از وابستگی‌های آن پیدا نشد."
        )
        st.code(str(exc))
        st.markdown(
            "بررسی کن فایل `video_tools.py` در کنار `app.py` باشد "
            "و وابستگی‌های آن در `requirements.txt` نصب شده باشند."
        )

    except Exception as exc:
        st.error(f"خطا در ابزارهای ویدئو: {exc}")

# --------------------------------------------------
# ASSISTANT
# --------------------------------------------------

elif page == "دستیار هوشمند":
    show_header(
        "دستیار هوشمند",
        "پرسش‌ها و ایده‌هایت را در این بخش بنویس",
    )

    st.warning(
        "این نسخه به‌صورت پیش‌فرض به مدل زبانی آنلاین متصل نیست؛ "
        "پاسخ‌های زیر راهنمای پایه هستند."
    )

    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("پیام خود را بنویس...")

    if prompt:
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
        })

        response = (
            "درخواستت دریافت شد.\n\n"
            "برای پاسخ هوشمند واقعی، باید یک مدل زبانی و API معتبر "
            "به ORBIT AI متصل شود. در این نسخه اتصال آنلاین فعال نیست.\n\n"
            f"**درخواست شما:** {prompt}"
        )

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
        })

        st.rerun()

    if st.button("پاک‌کردن تاریخچه گفتگو"):
        st.session_state.chat_history = []
        st.rerun()

# --------------------------------------------------
# PLANNER
# --------------------------------------------------

elif page == "برنامه‌ریز":
    show_header(
        "برنامه‌ریز",
        "ساخت یک برنامه اولیه برای کارها و پروژه‌ها",
    )

    task = st.text_area(
        "چه کاری می‌خواهی انجام بدهی؟",
        placeholder="مثلاً ساخت یک ویدئوی تبلیغاتی...",
    )

    deadline = st.selectbox(
        "زمان موردنظر",
        ["امروز", "این هفته", "این ماه", "بدون زمان مشخص"],
    )

    priority = st.select_slider(
        "اولویت",
        options=["کم", "متوسط", "زیاد"],
        value="متوسط",
    )

    if st.button("ساخت برنامه", use_container_width=True):
        if not task.strip():
            st.warning("ابتدا موضوع کار را بنویس.")
        else:
            try:
                from core.planner import create_plan

                plan = create_plan(task)

                st.markdown("### برنامه پیشنهادی")
                st.write(plan)

            except Exception:
                st.markdown("### برنامه پیشنهادی")

                st.markdown(
                    f"""
                    **هدف:** {task}

                    **مهلت:** {deadline}

                    **اولویت:** {priority}

                    1. هدف و نتیجه نهایی را مشخص کن.
                    2. کار را به چند مرحله کوچک تقسیم کن.
                    3. منابع و فایل‌های موردنیاز را آماده کن.
                    4. مرحله اول را انجام بده و نتیجه را بررسی کن.
                    5. خروجی نهایی را بازبینی و ذخیره کن.
                    """
                )

# --------------------------------------------------
# IMAGE GENERATION
# --------------------------------------------------

elif page == "ساخت تصویر":
    show_header(
        "ساخت تصویر",
        "آماده‌کردن توضیحات تصویر برای اتصال به مدل تولید تصویر",
    )

    prompt = st.text_area(
        "توضیح تصویری که می‌خواهی بسازی",
        placeholder=(
            "مثلاً: پرتره سینمایی، نورپردازی حرفه‌ای، "
            "پس‌زمینه تیره و جزئیات واقع‌گرایانه..."
        ),
        height=150,
    )

    style = st.selectbox(
        "سبک",
        [
            "واقع‌گرایانه",
            "سینمایی",
            "فشن",
            "دیجیتال آرت",
            "مینیمال",
        ],
    )

    aspect = st.selectbox(
        "نسبت تصویر",
        ["1:1", "4:5", "9:16", "16:9"],
    )

    if st.button("آماده‌سازی توضیحات تصویر", use_container_width=True):
        if not prompt.strip():
            st.warning("ابتدا توضیحات تصویر را وارد کن.")
        else:
            prepared_prompt = (
                f"Style: {style}\n"
                f"Aspect ratio: {aspect}\n"
                f"Prompt: {prompt.strip()}"
            )

            st.success("توضیحات آماده شد.")
            st.code(prepared_prompt)

            st.download_button(
                "دانلود توضیحات",
                data=prepared_prompt,
                file_name="orbit_ai_image_prompt.txt",
                mime="text/plain",
            )

    st.info(
        "ساخت واقعی تصویر در این بخش هنوز فعال نیست. "
        "برای تولید تصویر باید سرویس تولید تصویر به برنامه متصل شود."
    )

# --------------------------------------------------
# SAVED PROJECTS
# --------------------------------------------------

elif page == "پروژه‌های ذخیره‌شده":
    show_header(
        "پروژه‌های ذخیره‌شده",
        "نتایج ذخیره‌شده در نشست فعلی برنامه",
    )

    projects = st.session_state.saved_projects

    if not projects:
        st.info(
            "هنوز پروژه‌ای ذخیره نشده است. "
            "از بخش ویرایش عکس، نتیجه را ذخیره کن."
        )

    else:
        for index, project in enumerate(reversed(projects)):
            with st.expander(
                f"{project['name']} — {project['created']}"
            ):
                st.write(project["details"])

                if project.get("image"):
                    st.image(
                        project["image"],
                        use_container_width=True,
                    )

                    st.download_button(
                        "دانلود نتیجه",
                        data=project["image"],
                        file_name=f"orbit_project_{index + 1}.png",
                        mime="image/png",
                        key=f"download_project_{index}",
                    )

        if st.button("حذف فهرست پروژه‌های این نشست"):
            st.session_state.saved_projects = []
            st.rerun()

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.sidebar.divider()
st.sidebar.caption("ORBIT AI")
st.sidebar.caption("Creative tools in one workspace")
