






import os
import json
import sqlite3
import urllib.request
import urllib.error
from contextlib import contextmanager
from datetime import datetime

import streamlit as st


# =========================================================
# ORBIT AI | Configuration
# =========================================================
APP_TITLE = "ORBIT AI"
DB_PATH = os.environ.get("ORBIT_DB_PATH", "orbit_memory.db")
DEFAULT_MODEL = "openrouter/free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

SYSTEM_PROMPT = """
تو ORBIT AI هستی؛ یک دستیار هوش مصنوعی حرفه‌ای و خوش‌بیان.

- زبان پیش‌فرض پاسخ‌ها فارسی معیار، روان و طبیعی است.
- بی‌دلیل فارسی و انگلیسی را ترکیب نکن.
- متن‌ها را خوانا، منظم و با پاراگراف‌های کوتاه بنویس.
- برای مراحل از شماره‌گذاری استفاده کن.
- نام سرویس‌ها، مدل‌ها و کدها را تغییر نده.
- اگر اطلاعات کافی نداری، صادقانه بیان کن.
- یادداشت‌های حافظه را فقط در صورت مرتبط بودن به کار ببر.
- اگر کاربر زبان دیگری خواست، به همان زبان پاسخ بده.
"""


# =========================================================
# Database
# =========================================================
@contextmanager
def database():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def timestamp():
    return datetime.now().isoformat(timespec="seconds")


def init_db():
    with database() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
                ON DELETE CASCADE
        );
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]

        if count == 0:
            db.execute(
                "INSERT INTO projects(name, created_at) VALUES (?, ?)",
                ("پروژه اصلی ORBIT", timestamp()),
            )


def fetch_all(sql, params=()):
    with database() as db:
        return db.execute(sql, params).fetchall()


def fetch_one(sql, params=()):
    with database() as db:
        return db.execute(sql, params).fetchone()


def execute(sql, params=()):
    with database() as db:
        cursor = db.execute(sql, params)
        return cursor.lastrowid


init_db()


# =========================================================
# API configuration
# =========================================================
def get_setting(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value is not None and str(value).strip():
            return str(value).strip()
    except Exception:
        pass

    return str(os.environ.get(name, default)).strip()


def get_api_config():
    api_key = get_setting("OPENROUTER_API_KEY")
    model = get_setting("OPENROUTER_MODEL", DEFAULT_MODEL)

    if model.startswith(("http://", "https://")):
        model = DEFAULT_MODEL

    return api_key, model or DEFAULT_MODEL


def ask_openrouter(messages):
    api_key, model = get_api_config()

    if not api_key:
        return None, (
            "کلید OPENROUTER_API_KEY تنظیم نشده است. "
            "تنظیمات Secrets را بررسی کن."
        )

    system_parts = [SYSTEM_PROMPT]
    conversation = []

    for item in messages:
        role = item.get("role")
        content = item.get("content", "")

        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            conversation.append({
                "role": role,
                "content": content,
            })

    api_messages = [{
        "role": "system",
        "content": "\n\n".join(system_parts),
    }] + conversation

    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": 0.5,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(
            payload, ensure_ascii=False
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": APP_TITLE,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=60
        ) as response:
            data = json.loads(
                response.read().decode(
                    "utf-8", errors="replace"
                )
            )

        choices = data.get("choices", [])
        if not choices:
            return None, "سرویس پاسخ قابل‌استفاده‌ای برنگرداند."

        content = choices[0].get(
            "message", {}
        ).get("content", "")

        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
                and part.get("type") == "text"
            )

        if not str(content).strip():
            return None, "پاسخ متنی دریافت نشد."

        return str(content).strip(), None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8", errors="replace"
        )
        try:
            parsed = json.loads(body)
            error = parsed.get("error", {})
            detail = error.get("message", body)
            code = error.get("code", exc.code)
        except Exception:
            detail, code = body or str(exc), exc.code

        return None, (
            f"HTTP {exc.code} | کد: {code}\n"
            f"مدل: {model}\n{str(detail)[:1200]}"
        )

    except urllib.error.URLError as exc:
        return None, f"خطای اتصال: {exc.reason}"

    except Exception as exc:
        return None, (
            f"خطای {type(exc).__name__}: {str(exc)[:800]}"
        )


def offline_answer(prompt):
    if any(word in prompt.lower() for word in [
        "سلام", "درود", "hello", "hi"
    ]):
        return (
            "سلام! به ORBIT AI خوش آمدی. 🌌\n\n"
            "در حال حاضر پاسخ آفلاین ارائه می‌شود."
        )

    return (
        "در حال حاضر پاسخ آنلاین دریافت نشد.\n\n"
        "بخش «اتصال و تنظیمات» را باز کن و وضعیت OpenRouter "
        "را بررسی کن."
    )


# =========================================================
# Modern responsive design
# =========================================================
st.markdown("""
<style>
:root {
    color-scheme: dark;
}

.stApp {
    background:
        radial-gradient(ellipse at 8% 0%,
            rgba(88, 70, 190, .19), transparent 34%),
        radial-gradient(ellipse at 95% 18%,
            rgba(27, 133, 190, .12), transparent 30%),
        #0b0d16;
    color: #edf0ff;
}

.block-container {
    max-width: 1440px;
    padding: 2rem clamp(1rem, 3vw, 3rem) 3rem;
}

h1, h2, h3, h4, p, label, li {
    text-align: right;
}

h1 {
    letter-spacing: -.5px;
    font-weight: 800 !important;
}

h2, h3 {
    font-weight: 700 !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg, #111426 0%, #0e111d 100%
    );
    border-left: 1px solid rgba(160, 170, 255, .12);
    border-right: 0;
}

[data-testid="stSidebar"] * {
    text-align: right;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #b9c1de;
}

.orbit-hero {
    position: relative;
    overflow: hidden;
    padding: clamp(1.5rem, 4vw, 3rem);
    margin: .4rem 0 1.5rem;
    border: 1px solid rgba(154, 139, 255, .26);
    border-radius: 28px;
    background:
        radial-gradient(circle at 12% 12%,
            rgba(93, 90, 235, .28), transparent 40%),
        linear-gradient(125deg,
            rgba(31, 35, 65, .98),
            rgba(15, 22, 39, .98));
    box-shadow: 0 20px 70px rgba(0, 0, 0, .2);
    direction: rtl;
    text-align: right;
}

.orbit-kicker {
    display: inline-block;
    padding: 6px 11px;
    margin-bottom: 14px;
    border: 1px solid rgba(155, 144, 255, .35);
    border-radius: 100px;
    color: #c6c0ff;
    background: rgba(116, 103, 245, .12);
    font-size: 12px;
    letter-spacing: 1px;
}

.orbit-hero h1 {
    margin: 0 0 12px;
    font-size: clamp(2rem, 5vw, 3.3rem);
    line-height: 1.3;
    background: linear-gradient(90deg, #fff, #bcb8ff, #89dcff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.orbit-hero p {
    max-width: 700px;
    color: #c0c8e1;
    line-height: 1.9;
    margin-bottom: 0;
}

.orbit-section {
    padding: 1.2rem 1.35rem;
    margin: 1rem 0;
    border: 1px solid rgba(153, 166, 218, .15);
    border-radius: 20px;
    background: linear-gradient(
        145deg,
        rgba(25, 29, 49, .88),
        rgba(17, 20, 34, .92)
    );
}

.orbit-section h3 {
    margin-top: 0;
}

.orbit-muted {
    color: #a6b0cf;
    font-size: .9rem;
    line-height: 1.8;
}

.orbit-chip {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 100px;
    background: rgba(111, 100, 239, .14);
    border: 1px solid rgba(142, 132, 255, .2);
    color: #c9c4ff;
    font-size: .82rem;
    margin: 3px;
}

div[data-testid="stMetric"] {
    background: rgba(26, 31, 53, .85);
    border: 1px solid rgba(147, 161, 219, .15);
    padding: 16px;
    border-radius: 18px;
}

div[data-testid="stMetricLabel"] {
    color: #b2bddb;
}

div[data-testid="stMetricValue"] {
    color: #f0efff;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(145, 158, 214, .18) !important;
    border-radius: 18px !important;
    background: rgba(22, 26, 44, .62);
}

div[data-testid="stChatMessage"] {
    border: 1px solid rgba(140, 153, 210, .13);
    border-radius: 18px;
    background: rgba(24, 28, 47, .75);
    direction: rtl;
    text-align: right;
}

div[data-testid="stChatMessage"] p {
    line-height: 1.95;
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {
    background-color: #14182a !important;
    border-color: #343b5a !important;
    border-radius: 12px !important;
    color: #f0f2ff !important;
    direction: rtl;
    text-align: right;
}

.stButton > button,
.stFormSubmitButton > button {
    min-height: 43px;
    border-radius: 12px;
    border: 1px solid rgba(149, 137, 255, .3);
    background: linear-gradient(
        115deg, #5c52d9, #387fba
    );
    color: white;
    font-weight: 650;
    transition: all .18s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: #aaa0ff;
    color: white;
    filter: brightness(1.12);
}

div[data-testid="stRadio"] label,
div[data-testid="stCheckbox"] label {
    direction: rtl;
}

hr {
    border-color: rgba(143, 155, 208, .16);
}

[data-testid="stCaptionContainer"] {
    color: #929dbc;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1rem .85rem 2rem;
    }

    .orbit-hero {
        padding: 1.35rem 1.1rem;
        border-radius: 20px;
        margin-top: .2rem;
    }

    .orbit-hero h1 {
        font-size: 2rem;
    }

    .orbit-section {
        padding: 1rem;
        border-radius: 16px;
    }

    div[data-testid="stMetric"] {
        padding: 10px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.35rem;
    }

    [data-testid="stChatMessage"] {
        padding: .7rem;
    }
}
</style>
""", unsafe_allow_html=True)


def section_heading(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(
            f'<p class="orbit-muted">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def save_message(project_id, role, content):
    execute(
        """INSERT INTO messages
           (project_id, role, content, created_at)
           VALUES (?, ?, ?, ?)""",
        (project_id, role, content, timestamp()),
    )


# =========================================================
# Sidebar and projects
# =========================================================
with st.sidebar:
    st.markdown("## 🌌 ORBIT AI")
    st.caption("دستیار هوشمند شخصی")
    st.divider()

    api_key, selected_model = get_api_config()

    if api_key:
        st.success("اتصال: کلید تنظیم شده")
    else:
        st.warning("کلید OpenRouter تنظیم نشده")

    st.caption(f"مدل: {selected_model}")

    st.divider()
    st.markdown("### 🧭 فضای کاری")

    pages = [
        "🏠 خانه",
        "💬 دستیار هوشمند",
        "📋 برنامه‌ریز",
        "📝 تحلیل متن",
        "🧠 حافظه",
        "📁 پروژه‌ها",
        "🔧 اتصال و تنظیمات",
    ]

    if "orbit_page" not in st.session_state:
        st.session_state.orbit_page = pages[0]

    page = st.radio(
        "انتخاب بخش",
        pages,
        key="orbit_page",
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### 📁 پروژهٔ فعال")

    projects = fetch_all(
        "SELECT * FROM projects ORDER BY id DESC"
    )

    project_map = {
        row["name"]: row["id"] for row in projects
    }

    if not project_map:
        st.error("پروژه‌ای وجود ندارد.")
        st.stop()

    project_names = list(project_map.keys())

    if (
        "orbit_project_name" not in st.session_state
        or st.session_state.orbit_project_name not in project_map
    ):
        st.session_state.orbit_project_name = project_names[0]

    active_name = st.selectbox(
        "پروژه",
        project_names,
        key="orbit_project_name",
        label_visibility="collapsed",
    )
    project_id = project_map[active_name]

    with st.expander("➕ ساخت پروژه"):
        with st.form("sidebar_create_project", clear_on_submit=True):
            new_name = st.text_input("نام پروژه")
            create_project = st.form_submit_button(
                "ایجاد پروژه", use_container_width=True
            )

        if create_project:
            name = new_name.strip()
            if name:
                execute(
                    """INSERT INTO projects(name, created_at)
                       VALUES (?, ?)""",
                    (name, timestamp()),
                )
                st.session_state.orbit_project_name = name
                st.rerun()
            else:
                st.warning("نام پروژه را وارد کن.")

    st.divider()
    st.caption("طراحی واکنش‌گرا · نسخهٔ وب")


# =========================================================
# Home
# =========================================================
if page == "🏠 خانه":
    st.markdown("""
    <div class="orbit-hero">
        <div class="orbit-kicker">YOUR PERSONAL AI WORKSPACE</div>
        <h1>به ORBIT AI خوش آمدی 🌌</h1>
        <p>
            یک فضای یکپارچه برای گفت‌وگو با هوش مصنوعی،
            مدیریت پروژه‌ها، برنامه‌ریزی اهداف و سازمان‌دهی یادداشت‌ها.
        </p>
    </div>
    """, unsafe_allow_html=True)

    all_projects = fetch_all("SELECT id FROM projects")
    total_tasks = fetch_one(
        "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
        (project_id,),
    )[0]
    total_notes = fetch_one(
        "SELECT COUNT(*) FROM notes WHERE project_id = ?",
        (project_id,),
    )[0]
    total_messages = fetch_one(
        "SELECT COUNT(*) FROM messages WHERE project_id = ?",
        (project_id,),
    )[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("پروژه‌ها", len(all_projects))
    c2.metric("کارهای این پروژه", total_tasks)
    c3.metric("یادداشت‌های این پروژه", total_notes)

    st.markdown("")
    section_heading(
        "فضای کاری تو",
        "برای شروع، یکی از بخش‌های زیر را انتخاب کن.",
    )

    cards = [
        ("💬", "دستیار هوشمند",
         "گفت‌وگو با هوش مصنوعی و مشاهدهٔ تاریخچه.",
         "💬 دستیار هوشمند"),
        ("📋", "برنامه‌ریز",
         "ثبت کارها، پیگیری و علامت‌گذاری انجام‌شده‌ها.",
         "📋 برنامه‌ریز"),
        ("📝", "تحلیل متن",
         "اصلاح نگارش، خلاصه‌سازی، بازنویسی و ترجمه.",
         "📝 تحلیل متن"),
        ("🧠", "حافظه",
         "ذخیرهٔ یادداشت‌های مرتبط با پروژه.",
         "🧠 حافظه"),
        ("📁", "پروژه‌ها",
         "انتخاب پروژه و ساخت فضای کاری جدید.",
         "📁 پروژه‌ها"),
        ("🔧", "اتصال",
         "بررسی تنظیمات و آزمایش اتصال هوش مصنوعی.",
         "🔧 اتصال و تنظیمات"),
    ]

    for start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, item in zip(cols, cards[start:start + 3]):
            emoji, title, description, target = item
            with col:
                with st.container(border=True):
                    st.markdown(f"### {emoji} {title}")
                    st.markdown(
                        f'<p class="orbit-muted">{description}</p>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "ورود به بخش ←",
                        key=f"home_{title}",
                        use_container_width=True,
                    ):
                        st.session_state.orbit_page = target
                        st.rerun()

    st.markdown("")
    st.caption(
        f"پروژهٔ فعال: {active_name} · "
        f"پیام‌های ذخیره‌شده: {total_messages}"
    )


# =========================================================
# Chat
# =========================================================
elif page == "💬 دستیار هوشمند":
    section_heading(
        "💬 دستیار هوشمند",
        f"گفت‌وگو در فضای کاری «{active_name}»",
    )

    left, right = st.columns([3, 1])
    with left:
        st.markdown(
            '<span class="orbit-chip">پاسخ فارسی</span>'
            '<span class="orbit-chip">حافظهٔ پروژه</span>'
            '<span class="orbit-chip">OpenRouter</span>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("🗑️ پاک‌کردن گفت‌وگو", use_container_width=True):
            execute(
                "DELETE FROM messages WHERE project_id = ?",
                (project_id,),
            )
            st.rerun()

    history = fetch_all(
        """SELECT role, content FROM messages
           WHERE project_id = ? ORDER BY id ASC""",
        (project_id,),
    )

    if not history:
        with st.container(border=True):
            st.markdown("### ✨ از کجا شروع کنیم؟")
            st.write(
                "سؤالت را در کادر پایین بنویس. می‌توانی دربارهٔ "
                "یادگیری، برنامه‌ریزی، نوشتن یا ایده‌پردازی کمک بگیری."
            )

    for item in history:
        if item["role"] not in ("user", "assistant"):
            continue
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("پیامت را اینجا بنویس...")

    if prompt:
        save_message(project_id, "user", prompt)

        notes = fetch_all(
            """SELECT content FROM notes WHERE project_id = ?
               ORDER BY id DESC LIMIT 10""",
            (project_id,),
        )
        memory_text = "\n".join(
            "- " + row["content"] for row in notes
        ) or "یادداشتی ذخیره نشده است."

        recent = fetch_all(
            """SELECT role, content FROM messages
               WHERE project_id = ?
               ORDER BY id DESC LIMIT 16""",
            (project_id,),
        )
        recent = list(reversed(recent))

        api_messages = [{
            "role": "system",
            "content": (
                f"پروژهٔ فعال: {active_name}\n"
                f"یادداشت‌های مرتبط:\n{memory_text}\n"
                "یادداشت‌ها را فقط در صورت ارتباط با درخواست استفاده کن."
            ),
        }]

        api_messages.extend(
            {"role": row["role"], "content": row["content"]}
            for row in recent
            if row["role"] in ("user", "assistant")
        )

        with st.spinner("در حال آماده‌سازی پاسخ..."):
            answer, error = ask_openrouter(api_messages)

        if answer is None:
            st.error("پاسخ آنلاین دریافت نشد.")
            st.code(error or "علت خطا مشخص نیست.")
            answer = offline_answer(prompt)

        save_message(project_id, "assistant", answer)
        st.rerun()


# =========================================================
# Planner
# =========================================================
elif page == "📋 برنامه‌ریز":
    section_heading(
        "📋 برنامه‌ریز اهداف",
        "کارهای پروژه را ثبت کن و پیشرفت خودت را دنبال کن.",
    )

    tasks = fetch_all(
        "SELECT * FROM tasks WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )
    completed = sum(int(task["done"]) for task in tasks)
    total = len(tasks)

    a, b, c = st.columns(3)
    a.metric("کل کارها", total)
    b.metric("انجام‌شده", completed)
    c.metric("باقی‌مانده", total - completed)

    if total:
        st.progress(completed / total)

    with st.container(border=True):
        st.markdown("### ➕ افزودن کار جدید")
        with st.form("add_task_form", clear_on_submit=True):
            task_text = st.text_input(
                "عنوان کار",
                placeholder="مثلاً مطالعهٔ روزانه",
            )
            add_task = st.form_submit_button(
                "افزودن به برنامه",
                use_container_width=True,
            )

        if add_task:
            if task_text.strip():
                execute(
                    """INSERT INTO tasks
                       (project_id, task, done, created_at)
                       VALUES (?, ?, 0, ?)""",
                    (project_id, task_text.strip(), timestamp()),
                )
                st.rerun()
            else:
                st.warning("عنوان کار را وارد کن.")

    st.markdown("### فهرست کارها")

    if not tasks:
        st.info("هنوز کاری ثبت نکرده‌ای.")
    else:
        for task in tasks:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                checked = col1.checkbox(
                    task["task"],
                    value=bool(task["done"]),
                    key=f"task_{task['id']}",
                )

                if int(checked) != int(task["done"]):
                    execute(
                        "UPDATE tasks SET done = ? WHERE id = ?",
                        (int(checked), task["id"]),
                    )
                    st.rerun()

                if col2.button(
                    "حذف",
                    key=f"delete_task_{task['id']}",
                    use_container_width=True,
                ):
                    execute(
                        "DELETE FROM tasks WHERE id = ?",
                        (task["id"],),
                    )
                    st.rerun()

                st.caption(
                    "انجام‌شده" if task["done"] else "در انتظار انجام"
                )


# =========================================================
# Text analysis
# =========================================================
elif page == "📝 تحلیل متن":
    section_heading(
        "📝 آزمایشگاه متن",
        "متن را وارد کن و نوع پردازش موردنیازت را انتخاب کن.",
    )

    with st.container(border=True):
        text_input = st.text_area(
            "متن موردنظر",
            height=240,
            placeholder="متن را اینجا وارد کن...",
        )

        analysis_kind = st.selectbox(
            "نوع پردازش",
            [
                "اصلاح نگارش و روان‌سازی",
                "خلاصه‌سازی",
                "بازنویسی حرفه‌ای",
                "استخراج نکات کلیدی",
                "ترجمه به انگلیسی",
                "ترجمه به فارسی",
            ],
        )

        if st.button(
            "✨ پردازش متن",
            use_container_width=True,
        ):
            if not text_input.strip():
                st.warning("ابتدا متن را وارد کن.")
            else:
                instructions = {
                    "اصلاح نگارش و روان‌سازی":
                        "متن را با حفظ معنا روان و درست کن.",
                    "خلاصه‌سازی":
                        "متن را دقیق و منظم خلاصه کن.",
                    "بازنویسی حرفه‌ای":
                        "متن را حرفه‌ای و طبیعی بازنویسی کن.",
                    "استخراج نکات کلیدی":
                        "نکات اصلی را به شکل فهرست ارائه کن.",
                    "ترجمه به انگلیسی":
                        "متن را به انگلیسی طبیعی ترجمه کن.",
                    "ترجمه به فارسی":
                        "متن را به فارسی معیار و طبیعی ترجمه کن.",
                }

                with st.spinner("در حال پردازش..."):
                    result, error = ask_openrouter([
                        {
                            "role": "system",
                            "content": instructions[analysis_kind],
                        },
                        {
                            "role": "user",
                            "content": text_input,
                        },
                    ])

                if result:
                    st.markdown("### نتیجه")
                    with st.container(border=True):
                        st.markdown(result)
                        st.download_button(
                            "دانلود نتیجهٔ متنی",
                            data=result,
                            file_name="orbit_result.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                else:
                    st.error("پردازش آنلاین انجام نشد.")
                    st.code(error or "علت خطا مشخص نیست.")


# =========================================================
# Memory
# =========================================================
elif page == "🧠 حافظه":
    section_heading(
        "🧠 حافظهٔ پروژه",
        "یادداشت‌هایی ذخیره کن که در گفت‌وگوهای مرتبط به کار بیایند.",
    )

    notes = fetch_all(
        "SELECT * FROM notes WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )
    st.metric("یادداشت‌های ذخیره‌شده", len(notes))

    with st.container(border=True):
        st.markdown("### ✍️ یادداشت جدید")
        with st.form("add_note_form", clear_on_submit=True):
            note_text = st.text_area(
                "متن یادداشت",
                placeholder="اطلاعاتی که می‌خواهی برای این پروژه نگه داری...",
            )
            save_note = st.form_submit_button(
                "ذخیرهٔ یادداشت",
                use_container_width=True,
            )

        if save_note:
            if note_text.strip():
                execute(
                    """INSERT INTO notes(project_id, content, created_at)
                       VALUES (?, ?, ?)""",
                    (project_id, note_text.strip(), timestamp()),
                )
                st.rerun()
            else:
                st.warning("متن یادداشت را وارد کن.")

    st.markdown("### یادداشت‌های قبلی")

    if not notes:
        st.info("حافظهٔ این پروژه هنوز خالی است.")
    else:
        for note in notes:
            with st.container(border=True):
                st.write(note["content"])
                st.caption(f"تاریخ ثبت: {note['created_at']}")

                if st.button(
                    "حذف یادداشت",
                    key=f"delete_note_{note['id']}",
                    use_container_width=True,
                ):
                    execute(
                        "DELETE FROM notes WHERE id = ?",
                        (note["id"],),
                    )
                    st.rerun()


# =========================================================
# Projects
# =========================================================
elif page == "📁 پروژه‌ها":
    section_heading(
        "📁 مدیریت پروژه‌ها",
        "برای هر هدف، فضای کاری و حافظهٔ جداگانه داشته باش.",
    )

    projects = fetch_all(
        "SELECT * FROM projects ORDER BY id DESC"
    )

    with st.container(border=True):
        st.markdown("### ➕ ایجاد پروژه")
        with st.form("project_page_form", clear_on_submit=True):
            project_name_input = st.text_input(
                "نام پروژهٔ جدید",
                placeholder="مثلاً پروژهٔ بازاریابی",
            )
            submit_project = st.form_submit_button(
                "ساخت پروژه",
                use_container_width=True,
            )

        if submit_project:
            name = project_name_input.strip()
            if name:
                exists = fetch_one(
                    "SELECT id FROM projects WHERE name = ?",
                    (name,),
                )
                if exists:
                    st.warning("پروژه‌ای با این نام وجود دارد.")
                else:
                    execute(
                        "INSERT INTO projects(name, created_at) VALUES (?, ?)",
                        (name, timestamp()),
                    )
                    st.session_state.orbit_project_name = name
                    st.success("پروژه ساخته شد.")
                    st.rerun()
            else:
                st.warning("نام پروژه را وارد کن.")

    st.markdown("### پروژه‌های موجود")

    for project in projects:
        with st.container(border=True):
            st.markdown(f"#### 📂 {project['name']}")
            st.caption(f"تاریخ ایجاد: {project['created_at']}")

            p1, p2 = st.columns(2)
            if p1.button(
                "انتخاب پروژه",
                key=f"select_project_{project['id']}",
                use_container_width=True,
            ):
                st.session_state.orbit_project_name = project["name"]
                st.session_state.orbit_page = "🏠 خانه"
                st.rerun()

            if p2.button(
                "حذف پروژه",
                key=f"remove_project_{project['id']}",
                use_container_width=True,
                disabled=len(projects) <= 1,
            ):
                st.session_state[f"confirm_delete_{project['id']}"] = True

            if st.session_state.get(
                f"confirm_delete_{project['id']}", False
            ):
                st.warning(
                    "حذف پروژه، پیام‌ها، یادداشت‌ها و کارهای "
                    "ذخیره‌شدهٔ آن را نیز حذف می‌کند."
                )
                yes, no = st.columns(2)

                if yes.button(
                    "تأیید حذف",
                    key=f"yes_delete_{project['id']}",
                    use_container_width=True,
                ):
                    execute(
                        "DELETE FROM projects WHERE id = ?",
                        (project["id"],),
                    )
                    st.session_state.pop(
                        f"confirm_delete_{project['id']}", None
                    )
                    st.rerun()

                if no.button(
                    "انصراف",
                    key=f"no_delete_{project['id']}",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        f"confirm_delete_{project['id']}", None
                    )
                    st.rerun()


# =========================================================
# Connection and settings
# =========================================================
elif page == "🔧 اتصال و تنظیمات":
    section_heading(
        "🔧 اتصال و تنظیمات",
        "وضعیت سرویس هوش مصنوعی را بررسی کن.",
    )

    api_key, selected_model = get_api_config()

    with st.container(border=True):
        st.markdown("### وضعیت OpenRouter")

        if api_key:
            st.success("کلید API تنظیم شده است.")
        else:
            st.error("کلید API تنظیم نشده است.")

        st.write("مدل فعال:", selected_model)
        st.write("نشانی سرویس:", API_URL)

        if st.button(
            "🧪 آزمایش اتصال",
            use_container_width=True,
        ):
            with st.spinner("در حال بررسی اتصال..."):
                answer, error = ask_openrouter([
                    {
                        "role": "user",
                        "content": (
                            "فقط با یک جملهٔ کوتاه و به فارسی روان "
                            "بگو اتصال برقرار است."
                        ),
                    }
                ])

            if answer:
                st.success("اتصال آنلاین موفق بود.")
                st.write(answer)
            else:
                st.error("اتصال ناموفق بود.")
                st.code(error or "علت خطا مشخص نیست.")

    with st.container(border=True):
        st.markdown("### راهنمای تنظیم کلید")

        st.write(
            "در Streamlit Cloud، وارد تنظیمات برنامه و بخش "
            "Secrets شو. این دو مقدار باید تنظیم شده باشند:"
        )

        st.code(
            'OPENROUTER_API_KEY = "کلید واقعی تو"\n'
            'OPENROUTER_MODEL = "openrouter/free"',
            language="toml",
        )

        st.warning(
            "کلید واقعی را در فایل app.py یا مخزن عمومی GitHub "
            "قرار نده و برای دیگران ارسال نکن."
        )


# =========================================================
# Footer
# =========================================================
st.divider()
st.markdown(
    '<p style="text-align:center;color:#858fb1;'
    'font-size:.82rem;">🌌 ORBIT AI · فضای کاری هوشمند</p>',
    unsafe_allow_html=True,
)
