


import os
import sqlite3
from datetime import datetime

import requests
import streamlit as st

APP_TITLE = "ORBIT AI"
DB_PATH = "orbit_memory.db"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Database ----------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
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
                ("پروژه اصلی ORBIT", datetime.now().isoformat(timespec="seconds")),
            )


def query_all(sql, params=()):
    with get_db() as db:
        return db.execute(sql, params).fetchall()


def query_one(sql, params=()):
    with get_db() as db:
        return db.execute(sql, params).fetchone()


def execute(sql, params=()):
    with get_db() as db:
        cur = db.execute(sql, params)
        return cur.lastrowid


def now():
    return datetime.now().isoformat(timespec="seconds")


init_db()


# ---------- OpenRouter ----------
def get_secret(name, default=""):
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return os.getenv(name, default).strip()


def ask_openrouter(messages):
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    if not api_key:
        return None, (
            "کلید OPENROUTER_API_KEY تنظیم نشده است. "
            "آن را در بخش Secrets برنامه Streamlit وارد کن."
        )

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": "ORBIT AI",
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )

        if response.status_code != 200:
            try:
                details = response.json().get("error", {}).get(
                    "message", response.text
                )
            except Exception:
                details = response.text

            return None, (
                f"خطای OpenRouter ({response.status_code}): {details}"
            )

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        if isinstance(answer, list):
            answer = "\n".join(
                str(item.get("text", ""))
                for item in answer
                if isinstance(item, dict)
            )

        if not answer:
            return None, "پاسخ خالی از OpenRouter دریافت شد."

        return str(answer), None

    except requests.Timeout:
        return None, "زمان پاسخ‌گویی تمام شد. دوباره امتحان کن."
    except Exception as exc:
        return None, f"اتصال به OpenRouter ناموفق بود: {exc}"


# ---------- Offline mode ----------
def offline_answer(prompt):
    text = prompt.strip()
    lower = text.lower()

    if any(word in lower for word in ["سلام", "درود", "hello", "hi"]):
        return (
            "سلام! به ORBIT AI خوش آمدی 🌌\n\n"
            "در حال حاضر پاسخ آفلاین ارائه می‌دهم. "
            "برای گفت‌وگوی هوش مصنوعی آنلاین، کلید OpenRouter را تنظیم کن."
        )

    if any(word in lower for word in ["برنامه", "هدف", "plan", "هدفم"]):
        return (
            "برای شروع، هدفت را به مراحل کوچک تقسیم کن:\n\n"
            "۱. هدف نهایی را دقیق بنویس.\n"
            "۲. سه اقدام مهم را مشخص کن.\n"
            "۳. اولین اقدام را امروز انجام بده.\n"
            "۴. هر هفته نتیجه را بررسی کن.\n\n"
            "این پاسخ آفلاین و عمومی است؛ برای برنامه شخصی‌تر، "
            "جزئیات هدف را بنویس."
        )

    return (
        "حالت آفلاین ORBIT AI فعال است.\n\n"
        "در این حالت امکانات پایه در دسترس‌اند، اما پاسخ‌های هوشمند "
        "آنلاین فعال نیستند. برای فعال‌کردن آن، در Streamlit Secrets "
        "کلید OPENROUTER_API_KEY و نام مدل را تنظیم کن.\n\n"
        f"پیام تو: {text}"
    )


# ---------- Sidebar and projects ----------
st.markdown(
    """
    <style>
    .stApp { max-width: 1200px; margin: auto; }
    [data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        padding: 12px; border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌌 ORBIT AI")
st.caption("دستیار هوشمند برای گفت‌وگو، پروژه‌ها، برنامه‌ریزی و یادداشت‌ها")

projects = query_all("SELECT * FROM projects ORDER BY id DESC")

with st.sidebar:
    st.header("📁 پروژه‌ها")

    project_options = {
        row["name"]: row["id"] for row in projects
    }

    if not project_options:
        st.error("پروژه‌ای وجود ندارد.")
        st.stop()

    current_project_name = st.selectbox(
        "پروژه فعال",
        list(project_options.keys()),
    )
    project_id = project_options[current_project_name]

    with st.expander("➕ ساخت پروژه جدید"):
        with st.form("new_project_form", clear_on_submit=True):
            new_project_name = st.text_input("نام پروژه")
            create_project = st.form_submit_button("ساخت پروژه")

        if create_project and new_project_name.strip():
            execute(
                "INSERT INTO projects(name, created_at) VALUES (?, ?)",
                (new_project_name.strip(), now()),
            )
            st.rerun()

    st.divider()
    st.caption("وضعیت اتصال")

    if get_secret("OPENROUTER_API_KEY"):
        st.success("کلید API تنظیم شده")
    else:
        st.warning("حالت آفلاین؛ کلید API تنظیم نشده")

    st.caption("کلید API را در کد برنامه قرار نده.")


# ---------- Main tabs ----------
chat_tab, planner_tab, text_tab, memory_tab = st.tabs(
    ["💬 گفت‌وگو", "📋 برنامه‌ریز", "📝 تحلیل متن", "🧠 حافظه"]
)


# ---------- Chat ----------
with chat_tab:
    st.subheader(f"گفت‌وگو — {current_project_name}")

    history = query_all(
        """SELECT role, content FROM messages
           WHERE project_id = ?
           ORDER BY id ASC""",
        (project_id,),
    )

    if not history:
        st.info("گفت‌وگو را با نوشتن اولین پیام شروع کن.")

    for item in history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    if st.button("🗑️ پاک‌کردن تاریخچه این پروژه", key="clear_chat"):
        execute("DELETE FROM messages WHERE project_id = ?", (project_id,))
        st.rerun()

    user_prompt = st.chat_input("پیامت را برای ORBIT AI بنویس...")

    if user_prompt:
        execute(
            """INSERT INTO messages(project_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (project_id, "user", user_prompt, now()),
        )

        memory_notes = query_all(
            "SELECT content FROM notes WHERE project_id = ? ORDER BY id DESC LIMIT 10",
            (project_id,),
        )

        memory_text = "\n".join(
            f"- {row['content']}" for row in memory_notes
        ) or "هنوز یادداشت ذخیره‌شده‌ای وجود ندارد."

        system_prompt = (
            "تو ORBIT AI هستی؛ دستیار مفید، دقیق و خوش‌برخورد. "
            "به زبان کاربر پاسخ بده. اگر مطمئن نیستی، صادقانه بگو. "
            "اطلاعات حافظه پروژه را فقط به‌عنوان زمینه مرتبط استفاده کن.\n\n"
            f"نام پروژه: {current_project_name}\n"
            f"یادداشت‌های حافظه این پروژه:\n{memory_text}"
        )

        recent = query_all(
            """SELECT role, content FROM messages
               WHERE project_id = ?
               ORDER BY id DESC LIMIT 16""",
            (project_id,),
        )
        recent = list(reversed(recent))

        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(
            {"role": row["role"], "content": row["content"]}
            for row in recent
            if row["role"] in ("user", "assistant")
        )

        with st.spinner("ORBIT AI در حال پاسخ‌گویی است..."):
            answer, error = ask_openrouter(api_messages)

        if answer is None:
            answer = offline_answer(user_prompt)
            st.warning(
                "پاسخ آنلاین دریافت نشد؛ پاسخ پایه آفلاین نمایش داده می‌شود."
            )
            if error:
                with st.expander("جزئیات اتصال"):
                    st.code(error)

        execute(
            """INSERT INTO messages(project_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (project_id, "assistant", answer, now()),
        )
        st.rerun()


# ---------- Planner ----------
with planner_tab:
    st.subheader("📋 برنامه‌ریز اهداف")
    st.write("هدفت را به کارهای قابل انجام تبدیل کن.")

    with st.form("planner_form", clear_on_submit=True):
        goal = st.text_input("هدف تو چیست؟")
        add_goal = st.form_submit_button("افزودن هدف")

    if add_goal and goal.strip():
        execute(
            """INSERT INTO tasks(project_id, task, done, created_at)
               VALUES (?, ?, 0, ?)""",
            (project_id, goal.strip(), now()),
        )
        st.success("هدف ذخیره شد.")

    tasks = query_all(
        "SELECT * FROM tasks WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )

    if tasks:
        st.write("### کارهای این پروژه")
        for task in tasks:
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

            if col2.button("حذف", key=f"delete_task_{task['id']}"):
                execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
                st.rerun()
    else:
        st.info("هنوز هدفی اضافه نشده است.")


# ---------- Text analysis ----------
with text_tab:
    st.subheader("📝 تحلیل متن")

    input_text = st.text_area(
        "متن موردنظر را وارد کن",
        height=220,
        placeholder="متن را اینجا وارد کن...",
    )

    analysis_type = st.selectbox(
        "نوع تحلیل",
        [
            "خلاصه‌سازی",
            "بازنویسی و بهبود",
            "استخراج نکات کلیدی",
            "ترجمه به انگلیسی",
            "ترجمه به فارسی",
        ],
    )

    if st.button("تحلیل متن", key="analyze_text"):
        if not input_text.strip():
            st.warning("اول یک متن وارد کن.")
        else:
            instruction = (
                f"لطفاً متن زیر را با این روش پردازش کن: {analysis_type}.\n\n"
                f"متن:\n{input_text}"
            )

            result, error = ask_openrouter([
                {
                    "role": "system",
                    "content": "تو دستیار حرفه‌ای تحلیل و ویرایش متن هستی.",
                },
                {"role": "user", "content": instruction},
            ])

            if result:
                st.markdown("### نتیجه")
                st.markdown(result)
            else:
                st.warning("تحلیل آنلاین انجام نشد.")
                if error:
                    st.caption(error)
                st.markdown("### متن ورودی")
                st.write(input_text)
                st.info(
                    "برای تحلیل هوشمند، کلید API و نام مدل را بررسی کن."
                )


# ---------- Memory ----------
with memory_tab:
    st.subheader("🧠 حافظه پروژه")
    st.write(
        "یادداشت‌هایی ذخیره کن تا ORBIT AI بتواند در گفت‌وگوهای بعدی "
        "همین پروژه از آن‌ها به‌عنوان زمینه استفاده کند."
    )

    with st.form("memory_form", clear_on_submit=True):
        note_content = st.text_area(
            "یادداشت جدید",
            placeholder="مثلاً: هدف این پروژه ساخت یک دستیار شخصی است.",
        )
        save_note = st.form_submit_button("ذخیره در حافظه")

    if save_note and note_content.strip():
        execute(
            """INSERT INTO notes(project_id, content, created_at)
               VALUES (?, ?, ?)""",
            (project_id, note_content.strip(), now()),
        )
        st.success("یادداشت ذخیره شد.")
        st.rerun()

    notes = query_all(
        "SELECT * FROM notes WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )

    if notes:
        for note in notes:
            with st.container(border=True):
                st.write(note["content"])
                st.caption(note["created_at"])
                if st.button("حذف یادداشت", key=f"note_{note['id']}"):
                    execute("DELETE FROM notes WHERE id = ?", (note["id"],))
                    st.rerun()
    else:
        st.info("حافظه این پروژه هنوز خالی است.")


# ---------- Footer ----------
st.divider()
st.caption(
    "ORBIT AI • حالت آنلاین از OpenRouter استفاده می‌کند؛ "
    "حالت آفلاین امکانات پایه دارد."
)
