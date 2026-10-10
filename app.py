







import os
import sqlite3
import requests
import streamlit as st
from datetime import datetime

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "orbit_memory.db"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# -------------------- DATABASE --------------------
def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                done INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

def get_projects():
    with db() as conn:
        rows = conn.execute(
            "SELECT name FROM projects ORDER BY id DESC"
        ).fetchall()
    return [r[0] for r in rows]

def create_project(name):
    name = name.strip()
    if name:
        with db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (name, created_at) VALUES (?, ?)",
                (name, datetime.now().isoformat())
            )

def get_messages(project):
    with db() as conn:
        rows = conn.execute(
            """SELECT role, content FROM messages
               WHERE project = ? ORDER BY id""",
            (project,)
        ).fetchall()
    return [{"role": r, "content": c} for r, c in rows]

def save_message(project, role, content):
    with db() as conn:
        conn.execute(
            """INSERT INTO messages
               (project, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (project, role, content, datetime.now().isoformat())
        )

def get_notes():
    with db() as conn:
        return conn.execute(
            "SELECT id, content FROM notes ORDER BY id DESC"
        ).fetchall()

def add_note(content):
    with db() as conn:
        conn.execute(
            "INSERT INTO notes (content, created_at) VALUES (?, ?)",
            (content, datetime.now().isoformat())
        )

def get_tasks():
    with db() as conn:
        return conn.execute(
            "SELECT id, content, done FROM tasks ORDER BY id DESC"
        ).fetchall()

def add_task(content):
    with db() as conn:
        conn.execute(
            "INSERT INTO tasks (content, created_at) VALUES (?, ?)",
            (content, datetime.now().isoformat())
        )

def update_task(task_id, done):
    with db() as conn:
        conn.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(done), task_id)
        )

def delete_task(task_id):
    with db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

def delete_note(note_id):
    with db() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

init_db()

# -------------------- API CONFIG --------------------
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.environ.get(name, default)

API_KEY = get_secret("OPENROUTER_API_KEY", "")
MODEL = get_secret("OPENROUTER_MODEL", "openai/gpt-4o-mini")

def ask_ai(history, user_text):
    if not API_KEY:
        return (
            "کلید OpenRouter تنظیم نشده است.\n\n"
            "در Streamlit وارد Settings → Secrets شو و "
            "OPENROUTER_API_KEY را تنظیم کن."
        )

    notes = get_notes()
    memory_text = "\n".join(n[1] for n in notes[-20:])

    system_prompt = (
        "You are ORBIT AI, a helpful, intelligent assistant. "
        "Respond naturally in the user's language, especially Persian. "
        "Be clear, practical, accurate, and friendly. "
        "Do not claim to perform actions you did not perform.\n\n"
        f"User memory notes, when relevant:\n{memory_text}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_text})

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://orbit-ai.streamlit.app",
                "X-Title": "ORBIT AI"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.5
            },
            timeout=60
        )

        if response.status_code != 200:
            return (
                f"خطای اتصال به هوش مصنوعی "
                f"({response.status_code}):\n"
                f"{response.text[:1200]}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.Timeout:
        return "زمان پاسخ‌گویی تمام شد. دوباره تلاش کن."
    except Exception as exc:
        return f"خطا در ارتباط با هوش مصنوعی: {exc}"

# -------------------- DESIGN --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Vazirmatn', sans-serif;
}
.stApp {
    background:
        radial-gradient(ellipse at top right, #20224a 0%, transparent 40%),
        linear-gradient(145deg, #090d19 0%, #101426 55%, #0a1020 100%);
    color: #f3f4ff;
}
[data-testid="stSidebar"] {
    background: #0c1120;
    border-right: 1px solid #272d46;
}
h1, h2, h3, p, label {
    color: #f3f4ff;
}
.orbit-hero {
    padding: 28px 24px;
    border: 1px solid #353b66;
    border-radius: 24px;
    background: linear-gradient(125deg, #20264b, #17182e 65%, #251b42);
    margin-bottom: 22px;
}
.orbit-kicker {
    color: #b7baff;
    font-size: 13px;
    letter-spacing: 2px;
}
.orbit-title {
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    margin: 6px 0;
}
.orbit-subtitle {
    color: #c3c8df;
    font-size: 15px;
}
.orbit-card {
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #2c3450;
    background: rgba(22, 29, 51, .85);
    margin-bottom: 12px;
}
.orbit-muted {
    color: #aab2ce;
    font-size: 13px;
}
.stButton > button {
    border-radius: 12px;
    min-height: 42px;
    border: 1px solid #484f80;
    background: #252c50;
    color: white;
}
.stButton > button:hover {
    background: #343d70;
    border-color: #8188ff;
    color: white;
}
.stTextInput input, .stTextArea textarea {
    background: #11182b;
    color: white;
    border: 1px solid #343c59;
    border-radius: 12px;
}
[data-testid="stChatMessage"] {
    background: rgba(26, 33, 57, .85);
    border: 1px solid #303957;
    border-radius: 16px;
    padding: 12px;
}
hr {
    border-color: #2a314a;
}
@media (max-width: 640px) {
    .orbit-hero { padding: 20px 16px; border-radius: 18px; }
    .orbit-title { font-size: 31px; }
}
</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## 🌌 ORBIT AI")
    st.caption("Your personal AI workspace")
    st.divider()

    page = st.radio(
        "منوی اصلی",
        [
            "خانه",
            "گفت‌وگوی هوشمند",
            "برنامه‌ریز",
            "تحلیل متن",
            "حافظه",
            "پروژه‌ها",
            "تنظیمات و اتصال"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("ORBIT AI · Personal Workspace")

# -------------------- HERO --------------------
def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="orbit-hero">
            <div class="orbit-kicker">ORBIT AI · INTELLIGENT WORKSPACE</div>
            <div class="orbit-title">{title}</div>
            <div class="orbit-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------- HOME --------------------
if page == "خانه":
    hero("فضای هوشمند تو", "ایده‌ها را به برنامه تبدیل کن؛ با کمک هوش مصنوعی.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="orbit-card"><h3>💬 گفت‌وگو</h3>'
            '<p class="orbit-muted">پرسش، ایده‌پردازی و حل مسئله</p></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            '<div class="orbit-card"><h3>🗓️ برنامه‌ریز</h3>'
            '<p class="orbit-muted">مدیریت وظایف روزانه</p></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            '<div class="orbit-card"><h3>🧠 حافظه</h3>'
            '<p class="orbit-muted">یادداشت‌های مهم تو</p></div>',
            unsafe_allow_html=True
        )

    st.subheader("شروع سریع")
    prompt = st.text_input(
        "چه کاری می‌خواهی انجام بدهی؟",
        placeholder="مثلاً برای امروز یک برنامه دقیق بساز..."
    )
    if st.button("شروع گفت‌وگو", use_container_width=True):
        if prompt.strip():
            st.session_state["quick_prompt"] = prompt
            st.rerun()

    if st.session_state.get("quick_prompt"):
        st.info("پیامت آماده است. از منوی کناری وارد «گفت‌وگوی هوشمند» شو.")

# -------------------- CHAT --------------------
elif page == "گفت‌وگوی هوشمند":
    hero("گفت‌وگوی هوشمند", "با ORBIT AI درباره ایده‌ها و کارهایت گفت‌وگو کن.")

    projects = get_projects()
    if not projects:
        create_project("گفت‌وگوی من")
        projects = get_projects()

    selected_project = st.selectbox("انتخاب پروژه", projects)
    history = get_messages(selected_project)

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    quick_prompt = st.session_state.pop("quick_prompt", "")
    user_text = st.chat_input("پیامت را اینجا بنویس...")
    if quick_prompt and not user_text:
        user_text = quick_prompt

    if user_text:
        save_message(selected_project, "user", user_text)
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("ORBIT در حال فکر کردن است..."):
                answer = ask_ai(history, user_text)
            st.markdown(answer)

        save_message(selected_project, "assistant", answer)
        st.rerun()

    if st.button("پاک‌کردن تاریخچه این پروژه"):
        with db() as conn:
            conn.execute(
                "DELETE FROM messages WHERE project = ?",
                (selected_project,)
            )
        st.rerun()

# -------------------- PLANNER --------------------
elif page == "برنامه‌ریز":
    hero("برنامه‌ریز شخصی", "کارهایت را ثبت کن و پیشرفتت را دنبال کن.")

    with st.form("task_form", clear_on_submit=True):
        task = st.text_input("کار جدید", placeholder="مثلاً ۳۰ دقیقه مطالعه")
        submitted = st.form_submit_button("افزودن کار")

    if submitted and task.strip():
        add_task(task.strip())
        st.rerun()

    tasks = get_tasks()
    done_count = sum(1 for t in tasks if t[2])
    if tasks:
        st.progress(done_count / len(tasks))
        st.caption(f"{done_count} از {len(tasks)} کار انجام شده")

    for task_id, content, done in tasks:
        c1, c2 = st.columns([5, 1])
        with c1:
            checked = st.checkbox(
                content,
                value=bool(done),
                key=f"task_{task_id}"
            )
            if int(checked) != int(done):
                update_task(task_id, checked)
                st.rerun()
        with c2:
            if st.button("حذف", key=f"delete_{task_id}"):
                delete_task(task_id)
                st.rerun()

# -------------------- TEXT ANALYSIS --------------------
elif page == "تحلیل متن":
    hero("تحلیل متن", "متن را وارد کن و از هوش مصنوعی برای بررسی آن کمک بگیر.")

    text_input = st.text_area(
        "متن موردنظر",
        height=220,
        placeholder="متن خود را اینجا وارد کن..."
    )
    mode = st.selectbox(
        "نوع تحلیل",
        [
            "خلاصه‌سازی",
            "تحلیل و بررسی",
            "اصلاح نگارش",
            "ترجمه به انگلیسی",
            "استخراج نکات کلیدی"
        ]
    )

    if st.button("تحلیل متن", use_container_width=True):
        if not text_input.strip():
            st.warning("ابتدا متن را وارد کن.")
        else:
            instruction = (
                f"لطفاً کار زیر را روی متن انجام بده: {mode}\n\n"
                f"متن:\n{text_input}"
            )
            with st.spinner("در حال پردازش..."):
                result = ask_ai([], instruction)
            st.markdown("### نتیجه")
            st.markdown(result)
            st.download_button(
                "دانلود نتیجه به‌صورت TXT",
                data=result,
                file_name="orbit_analysis.txt",
                mime="text/plain"
            )

# -------------------- MEMORY --------------------
elif page == "حافظه":
    hero("حافظه شخصی", "یادداشت‌هایی ثبت کن که در گفت‌وگوهای بعدی به پاسخ‌ها کمک کنند.")

    with st.form("note_form", clear_on_submit=True):
        note = st.text_area("یادداشت جدید", placeholder="نکته‌ای که می‌خواهی ذخیره شود...")
        save = st.form_submit_button("ذخیره یادداشت")

    if save and note.strip():
        add_note(note.strip())
        st.success("یادداشت ذخیره شد.")
        st.rerun()

    notes = get_notes()
    if not notes:
        st.info("هنوز یادداشتی ثبت نشده است.")

    for note_id, content in notes:
        with st.container(border=True):
            st.write(content)
            if st.button("حذف یادداشت", key=f"note_{note_id}"):
                delete_note(note_id)
                st.rerun()

# -------------------- PROJECTS --------------------
elif page == "پروژه‌ها":
    hero("مدیریت پروژه‌ها", "برای موضوعات مختلف فضای کاری جدا بساز.")

    with st.form("project_form", clear_on_submit=True):
        name = st.text_input("نام پروژه", placeholder="مثلاً ایده‌های جدید")
        create = st.form_submit_button("ساخت پروژه")

    if create and name.strip():
        create_project(name.strip())
        st.success("پروژه ثبت شد.")
        st.rerun()

    projects = get_projects()
    for project in projects:
        st.markdown(
            f'<div class="orbit-card">📁 {project}</div>',
            unsafe_allow_html=True
        )

    st.caption("تاریخچه گفت‌وگوها بر اساس پروژه جدا می‌شود.")

# -------------------- SETTINGS --------------------
elif page == "تنظیمات و اتصال":
    hero("تنظیمات سیستم", "وضعیت اتصال ORBIT AI را بررسی کن.")

    st.markdown("### اتصال به OpenRouter")
    if API_KEY:
        st.success("کلید API پیدا شد؛ تنظیم کلید در محیط برنامه موجود است.")
    else:
        st.error("کلید OPENROUTER_API_KEY پیدا نشد.")

    st.write(f"**مدل فعلی:** `{MODEL}`")

    st.markdown("### بررسی اتصال")
    if st.button("تست اتصال به هوش مصنوعی", use_container_width=True):
        with st.spinner("در حال بررسی اتصال..."):
            test = ask_ai([], "فقط بنویس: اتصال موفق است.")
        st.markdown("### نتیجه تست")
        st.write(test)

    st.divider()
    st.markdown("### نکات مهم")
    st.write(
        "- کلید API را در کد عمومی قرار نده.\n"
        "- کلید باید در تنظیمات Secrets برنامه میزبانی‌شده ثبت شده باشد.\n"
        "- پایگاه داده SQLite در این نسخه محلی است؛ "
        "ممکن است با راه‌اندازی مجدد یا استقرار مجدد در فضای ابری "
        "همه اطلاعات ماندگار نمانند."
    )

st.divider()
st.caption("ORBIT AI · Designed for ideas, focus and progress")
