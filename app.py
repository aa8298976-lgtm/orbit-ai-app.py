



import os
import json
import sqlite3
import urllib.request
import urllib.error
from contextlib import contextmanager
from datetime import datetime

import streamlit as st


# =========================
# ORBIT AI — Configuration
# =========================
APP_TITLE = "ORBIT AI"
DB_PATH = "orbit_memory.db"
DEFAULT_MODEL = "openrouter/free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌌",
    layout="wide",
)


# =========================
# Database
# =========================
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
                ("پروژه اصلی ORBIT", datetime.now().isoformat(timespec="seconds")),
            )


def fetch_all(sql, params=()):
    with database() as db:
        return db.execute(sql, params).fetchall()


def execute(sql, params=()):
    with database() as db:
        cur = db.execute(sql, params)
        return cur.lastrowid


def timestamp():
    return datetime.now().isoformat(timespec="seconds")


init_db()


# =========================
# Secrets
# =========================
def get_setting(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value is not None:
            return str(value).strip()
    except Exception:
        pass

    return os.environ.get(name, default).strip()


def get_api_config():
    api_key = get_setting("OPENROUTER_API_KEY")
    model = get_setting("OPENROUTER_MODEL", DEFAULT_MODEL)

    if model.startswith("http://") or model.startswith("https://"):
        model = DEFAULT_MODEL

    return api_key, model or DEFAULT_MODEL


# =========================
# OpenRouter connection
# =========================
def ask_openrouter(messages):
    api_key, model = get_api_config()

    if not api_key:
        return None, (
            "OPENROUTER_API_KEY پیدا نشد. "
            "در Streamlit Cloud وارد Settings > Secrets شو."
        )

    if api_key.lower() in {
        "your-api-key",
        "your_key",
        "کلید واقعی خودت",
    }:
        return None, "مقدار OPENROUTER_API_KEY نمونه است، نه کلید واقعی."

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }

    request_data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": APP_TITLE,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        choices = data.get("choices", [])
        if not choices:
            return None, (
                "پاسخ API شامل choices نبود: "
                + json.dumps(data, ensure_ascii=False)[:1200]
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
            content = "\n".join(parts)

        if not content or not str(content).strip():
            return None, (
                "مدل پاسخ متنی برنگرداند. "
                "یک مدل دیگر از فهرست رایگان OpenRouter انتخاب کن."
            )

        return str(content).strip(), None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")

        try:
            parsed = json.loads(body)
            details = parsed.get("error", {}).get("message", body)
            code = parsed.get("error", {}).get("code", exc.code)
        except Exception:
            details = body or str(exc)
            code = exc.code

        return None, (
            f"HTTP {exc.code} | کد خطا: {code}\n"
            f"مدل انتخاب‌شده: {model}\n"
            f"توضیحات سرویس: {str(details)[:1600]}"
        )

    except urllib.error.URLError as exc:
        return None, (
            "اتصال شبکه به OpenRouter برقرار نشد.\n"
            f"جزئیات: {exc.reason}"
        )

    except TimeoutError:
        return None, "مهلت اتصال تمام شد. دوباره تلاش کن."

    except Exception as exc:
        return None, (
            f"خطای غیرمنتظره: {type(exc).__name__}: {str(exc)[:1000]}"
        )


# =========================
# Offline mode
# =========================
def offline_answer(prompt):
    text = prompt.strip()
    lower = text.lower()

    if any(word in lower for word in ["سلام", "درود", "hello", "hi"]):
        return (
            "سلام! به ORBIT AI خوش آمدی 🌌\n\n"
            "در حال حاضر پاسخ آفلاین ارائه می‌دهم. "
            "جزئیات خطای اتصال را بالای این پیام بررسی کن."
        )

    if any(word in lower for word in ["برنامه", "هدف", "plan"]):
        return (
            "پیشنهاد پایه برای برنامه‌ریزی:\n\n"
            "۱. هدفت را مشخص کن.\n"
            "۲. آن را به کارهای کوچک تقسیم کن.\n"
            "۳. برای هر کار زمان تعیین کن.\n"
            "۴. هر هفته پیشرفت را بررسی کن.\n\n"
            "این پاسخ پایه آفلاین است."
        )

    return (
        "حالت آفلاین ORBIT AI فعال است.\n\n"
        "برای پاسخ هوشمند آنلاین، ابتدا خطای اتصال نمایش‌داده‌شده "
        "در بالای این پیام را بررسی کن."
    )


# =========================
# UI
# =========================
st.markdown("""
<style>
.block-container {
    max-width: 1150px;
    padding-top: 1.5rem;
}
</style>
""")

st.title("🌌 ORBIT AI")
st.caption(
    "دستیار شخصی برای گفت‌وگو، مدیریت پروژه، حافظه و برنامه‌ریزی"
)

api_key, selected_model = get_api_config()

with st.sidebar:
    st.header("⚙️ وضعیت سیستم")

    if api_key:
        st.success("کلید API در تنظیمات پیدا شد")
    else:
        st.error("کلید API پیدا نشد")

    st.caption(f"مدل تنظیم‌شده: {selected_model}")
    st.divider()

    st.subheader("📁 پروژه‌ها")

    projects = fetch_all(
        "SELECT * FROM projects ORDER BY id DESC"
    )

    project_map = {row["name"]: row["id"] for row in projects}

    if not project_map:
        st.error("پروژه‌ای پیدا نشد.")
        st.stop()

    project_name = st.selectbox(
        "پروژه فعال",
        list(project_map.keys()),
    )
    project_id = project_map[project_name]

    with st.expander("➕ ساخت پروژه"):
        with st.form("create_project_form", clear_on_submit=True):
            new_project = st.text_input("نام پروژه")
            create_clicked = st.form_submit_button("ایجاد")

        if create_clicked:
            if new_project.strip():
                execute(
                    "INSERT INTO projects(name, created_at) VALUES (?, ?)",
                    (new_project.strip(), timestamp()),
                )
                st.rerun()
            else:
                st.warning("نام پروژه را وارد کن.")

    st.divider()
    st.caption("ORBIT AI • OpenRouter")


chat_tab, planner_tab, analysis_tab, memory_tab, settings_tab = st.tabs(
    [
        "💬 گفت‌وگو",
        "📋 برنامه‌ریز",
        "📝 تحلیل متن",
        "🧠 حافظه",
        "🔧 اتصال",
    ]
)


# =========================
# Chat
# =========================
with chat_tab:
    st.subheader(f"گفت‌وگو: {project_name}")

    history = fetch_all(
        """SELECT role, content FROM messages
           WHERE project_id = ?
           ORDER BY id ASC""",
        (project_id,),
    )

    for item in history:
        if item["role"] not in ("user", "assistant"):
            continue
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    if st.button("🗑️ پاک‌کردن تاریخچه گفت‌وگو"):
        execute(
            "DELETE FROM messages WHERE project_id = ?",
            (project_id,),
        )
        st.rerun()

    prompt = st.chat_input("پیامت را برای ORBIT AI بنویس...")

    if prompt:
        execute(
            """INSERT INTO messages(project_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (project_id, "user", prompt, timestamp()),
        )

        notes = fetch_all(
            """SELECT content FROM notes
               WHERE project_id = ?
               ORDER BY id DESC LIMIT 10""",
            (project_id,),
        )

        memory_text = "\n".join(
            "- " + row["content"] for row in notes
        ) or "یادداشت ذخیره‌شده‌ای وجود ندارد."

        recent = fetch_all(
            """SELECT role, content FROM messages
               WHERE project_id = ?
               ORDER BY id DESC LIMIT 16""",
            (project_id,),
        )
        recent = list(reversed(recent))

        api_messages = [
            {
                "role": "system",
                "content": (
                    "تو ORBIT AI هستی؛ دستیار دقیق، مفید و خوش‌برخورد. "
                    "به زبان کاربر پاسخ بده و اگر مطمئن نیستی صادق باش. "
                    f"\nنام پروژه: {project_name}"
                    f"\nیادداشت‌های مرتبط:\n{memory_text}"
                ),
            }
        ]

        api_messages.extend(
            {"role": row["role"], "content": row["content"]}
            for row in recent
            if row["role"] in ("user", "assistant")
        )

        with st.spinner("در حال اتصال به هوش مصنوعی..."):
            answer, error = ask_openrouter(api_messages)

        if answer is None:
            # Show the actual connection error directly on the page.
            st.error("اتصال آنلاین ناموفق بود.")
            st.code(error or "علت خطا مشخص نیست.", language="text")
            answer = offline_answer(prompt)

        execute(
            """INSERT INTO messages(project_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (project_id, "assistant", answer, timestamp()),
        )
        st.rerun()


# =========================
# Planner
# =========================
with planner_tab:
    st.subheader("📋 برنامه‌ریز اهداف")

    with st.form("add_task_form", clear_on_submit=True):
        task_text = st.text_input("هدف یا کار جدید")
        add_task = st.form_submit_button("افزودن کار")

    if add_task:
        if task_text.strip():
            execute(
                """INSERT INTO tasks(project_id, task, done, created_at)
                   VALUES (?, ?, 0, ?)""",
                (project_id, task_text.strip(), timestamp()),
            )
            st.rerun()
        else:
            st.warning("متن کار را وارد کن.")

    tasks = fetch_all(
        "SELECT * FROM tasks WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )

    if not tasks:
        st.info("هنوز کاری ثبت نشده است.")

    for task in tasks:
        col1, col2 = st.columns([5, 1])

        checked = col1.checkbox(
            task["task"],
            value=bool(task["done"]),
            key=f"task_done_{task['id']}",
        )

        if int(checked) != int(task["done"]):
            execute(
                "UPDATE tasks SET done = ? WHERE id = ?",
                (int(checked), task["id"]),
            )
            st.rerun()

        if col2.button("حذف", key=f"task_delete_{task['id']}"):
            execute("DELETE FROM tasks WHERE id = ?", (task["id"],))
            st.rerun()


# =========================
# Text analysis
# =========================
with analysis_tab:
    st.subheader("📝 تحلیل متن")

    text_input = st.text_area(
        "متن را وارد کن",
        height=220,
        placeholder="متن موردنظر را اینجا بنویس...",
    )

    analysis_kind = st.selectbox(
        "نوع عملیات",
        [
            "خلاصه‌سازی",
            "بازنویسی و بهبود",
            "استخراج نکات کلیدی",
            "ترجمه به انگلیسی",
            "ترجمه به فارسی",
        ],
    )

    if st.button("شروع تحلیل"):
        if not text_input.strip():
            st.warning("ابتدا متن را وارد کن.")
        else:
            with st.spinner("در حال تحلیل..."):
                result, error = ask_openrouter([
                    {
                        "role": "system",
                        "content": (
                            "تو دستیار حرفه‌ای ویرایش و تحلیل متن هستی. "
                            "پاسخ را واضح و متناسب با درخواست ارائه کن."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"این متن را به روش «{analysis_kind}» پردازش کن:\n\n"
                            f"{text_input}"
                        ),
                    },
                ])

            if result:
                st.markdown("### نتیجه")
                st.markdown(result)
            else:
                st.error("تحلیل آنلاین انجام نشد.")
                st.code(error or "علت خطا مشخص نیست.", language="text")


# =========================
# Memory
# =========================
with memory_tab:
    st.subheader("🧠 حافظه پروژه")
    st.write(
        "یادداشت‌های این بخش در گفت‌وگوهای بعدی همین پروژه "
        "به‌عنوان زمینه در اختیار ORBIT AI قرار می‌گیرند."
    )

    with st.form("add_note_form", clear_on_submit=True):
        note_text = st.text_area("یادداشت جدید")
        save_note = st.form_submit_button("ذخیره یادداشت")

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

    notes = fetch_all(
        "SELECT * FROM notes WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )

    if not notes:
        st.info("حافظه این پروژه خالی است.")

    for note in notes:
        with st.container(border=True):
            st.write(note["content"])
            st.caption(note["created_at"])

            if st.button("حذف یادداشت", key=f"note_delete_{note['id']}"):
                execute("DELETE FROM notes WHERE id = ?", (note["id"],))
                st.rerun()


# =========================
# Connection diagnostics
# =========================
with settings_tab:
    st.subheader("🔧 عیب‌یابی OpenRouter")

    st.write("این بخش تنظیمات را بررسی می‌کند؛ کلید کامل را نمایش نمی‌دهد.")

    api_key, selected_model = get_api_config()

    st.write(
        "وضعیت کلید:",
        "تنظیم شده" if api_key else "تنظیم نشده",
    )
    st.write("مدل:", selected_model)
    st.write("نشانی API:", API_URL)

    if st.button("🧪 آزمایش اتصال آنلاین"):
        with st.spinner("در حال آزمایش اتصال..."):
            test_answer, test_error = ask_openrouter([
                {
                    "role": "user",
                    "content": "فقط بنویس: اتصال ORBIT موفق است.",
                }
            ])

        if test_answer:
            st.success("اتصال آنلاین موفق بود.")
            st.write(test_answer)
        else:
            st.error("آزمایش اتصال ناموفق بود.")
            st.code(
                test_error or "علت خطا مشخص نیست.",
                language="text",
            )

    st.caption(
        "اگر اتصال ناموفق بود، متن خطا را برای بررسی نگه دار. "
        "کلید API را در چت یا اسکرین‌شات منتشر نکن."
    )

st.divider()
st.caption(
    "ORBIT AI • حالت آنلاین با OpenRouter • حالت آفلاین پایه"
)
