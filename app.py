




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
DB_PATH = os.environ.get("ORBIT_DB_PATH", "orbit_memory.db")
DEFAULT_MODEL = "openrouter/free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌌",
    layout="wide",
)


# =========================
# Persian Language Rules
# =========================
SYSTEM_PROMPT = """
تو ORBIT AI هستی؛ یک دستیار هوش مصنوعی حرفه‌ای، دقیق و خوش‌بیان.

قوانین اصلی پاسخ‌گویی:

۱. زبان پیش‌فرض تو فارسی معیار، روان و طبیعی است.
۲. جمله‌ها را با دستور زبان صحیح و ترتیب طبیعی کلمات فارسی بنویس.
۳. فارسی و انگلیسی را بی‌دلیل در یک جمله ترکیب نکن.
۴. اگر واژه یا اصطلاح فارسی مناسبی وجود دارد، از آن استفاده کن.
۵. اصطلاح تخصصی انگلیسی را فقط در صورت نیاز بیاور و در اولین کاربرد،
معادل یا توضیح فارسی آن را ارائه بده.
۶. نام مدل‌ها، نام سرویس‌ها، کدها، نام متغیرها و پیام‌های فنی را تغییر نده.
۷. از ترجمه تحت‌اللفظی عبارت‌های انگلیسی به فارسی خودداری کن.
۸. پاراگراف‌ها را کوتاه، روشن و خوانا بنویس.
۹. برای مراحل از شماره‌گذاری و برای موارد مرتبط از فهرست استفاده کن.
۱۰. نشانه‌گذاری، فاصله‌گذاری و نیم‌فاصله را درست رعایت کن.
۱۱. از تکرار، جمله‌های ناقص، عبارت‌های نامأنوس و مقدمه‌های غیرضروری پرهیز کن.
۱۲. اگر کاربر راهنمایی مرحله‌به‌مرحله می‌خواهد، هر مرحله را واضح توضیح بده.
۱۳. اگر پاسخ شامل کد است، کد را در بلوک جداگانه قرار بده و توضیحات را فارسی بنویس.
۱۴. اگر اطلاعات کافی نداری، صادقانه بیان کن و چیزی را حدس نزن.
۱۵. اگر کاربر صریحاً زبان دیگری خواست، به همان زبان پاسخ بده.
۱۶. پیش از ارسال، پاسخ را از نظر دستور زبان، روانی و یکپارچگی زبانی بررسی کن.

قواعد استفاده از حافظه:
- یادداشت‌های ارائه‌شده را فقط زمانی استفاده کن که به درخواست فعلی مرتبط باشند.
- یادداشت‌ها را واقعیت قطعی فرض نکن؛ در صورت ابهام سؤال بپرس.
- اطلاعات جدید را بدون اجازه کاربر به‌عنوان یادداشت دائمی ثبت نکن.

لحن پاسخ‌ها باید طبیعی، محترمانه، مفید و متناسب با درخواست کاربر باشد.
"""


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
                (
                    "پروژه اصلی ORBIT",
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )


def fetch_all(sql, params=()):
    with database() as db:
        return db.execute(sql, params).fetchall()


def execute(sql, params=()):
    with database() as db:
        cursor = db.execute(sql, params)
        return cursor.lastrowid


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

    if model.startswith(("http://", "https://")):
        model = DEFAULT_MODEL

    return api_key, model or DEFAULT_MODEL


# =========================
# OpenRouter Connection
# =========================
def ask_openrouter(messages):
    api_key, model = get_api_config()

    if not api_key:
        return None, (
            "کلید OPENROUTER_API_KEY پیدا نشد. "
            "تنظیمات Secrets را در Streamlit Cloud بررسی کن."
        )

    if api_key.lower() in {
        "your-api-key",
        "your_key",
        "کلید واقعی خودت",
    }:
        return None, "مقدار کلید API نمونه است، نه کلید واقعی."

    # تمام درخواست‌ها از یک دستورالعمل زبانی ثابت پیروی می‌کنند.
    # دستورالعمل اختصاصی هر بخش نیز حفظ می‌شود.
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

    api_messages = [
        {
            "role": "system",
            "content": "\n\n".join(system_parts),
        }
    ] + conversation

    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": 0.5,
    }

    request_data = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": APP_TITLE,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )
            data = json.loads(raw)

        choices = data.get("choices", [])

        if not choices:
            return None, "سرویس هوش مصنوعی پاسخ قابل‌استفاده‌ای برنگرداند."

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
                "ممکن است مدل انتخاب‌شده محدودیت داشته باشد."
            )

        return str(content).strip(), None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

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
            f"خطای غیرمنتظره: {type(exc).__name__}: "
            f"{str(exc)[:1000]}"
        )


# =========================
# Offline Mode
# =========================
def offline_answer(prompt):
    text = prompt.strip()
    lower = text.lower()

    if any(word in lower for word in [
        "سلام", "درود", "hello", "hi"
    ]):
        return (
            "سلام! به ORBIT AI خوش آمدی. 🌌\n\n"
            "در حال حاضر پاسخ آفلاین ارائه می‌دهم. "
            "برای بررسی اتصال آنلاین، بخش «اتصال» را باز کن."
        )

    if any(word in lower for word in [
        "برنامه", "هدف", "plan"
    ]):
        return (
            "برای برنامه‌ریزی بهتر، این مراحل را دنبال کن:\n\n"
            "۱. هدف اصلی خودت را مشخص کن.\n"
            "۲. هدف را به چند کار کوچک تقسیم کن.\n"
            "۳. برای هر کار زمان مشخصی در نظر بگیر.\n"
            "۴. در پایان هفته، میزان پیشرفت را بررسی کن.\n\n"
            "این پاسخ پایه در حالت آفلاین تولید شده است."
        )

    return (
        "در حال حاضر حالت آفلاین فعال است.\n\n"
        "برای دریافت پاسخ هوشمند آنلاین، بخش «اتصال» را باز کن "
        "و خطای سرویس را بررسی کن."
    )


# =========================
# User Interface
# =========================
st.markdown("""
<style>
.block-container {
    max-width: 1150px;
    padding-top: 1.5rem;
}
.stApp {
    direction: rtl;
}
[data-testid="stSidebar"] {
    direction: rtl;
}
[data-testid="stChatMessage"] {
    direction: rtl;
    text-align: right;
}
textarea, input {
    direction: rtl;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

st.title("🌌 ORBIT AI")
st.caption(
    "دستیار شخصی برای گفت‌وگو، مدیریت پروژه، حافظه و برنامه‌ریزی"
)

api_key, selected_model = get_api_config()

with st.sidebar:
    st.header("⚙️ وضعیت سیستم")

    if api_key:
        st.success("کلید API تنظیم شده است.")
    else:
        st.error("کلید API پیدا نشد.")

    st.caption(f"مدل فعال: {selected_model}")
    st.divider()
    st.subheader("📁 پروژه‌ها")

    projects = fetch_all(
        "SELECT * FROM projects ORDER BY id DESC"
    )

    project_map = {
        row["name"]: row["id"]
        for row in projects
    }

    if not project_map:
        st.error("پروژه‌ای پیدا نشد.")
        st.stop()

    project_name = st.selectbox(
        "پروژهٔ فعال",
        list(project_map.keys()),
    )
    project_id = project_map[project_name]

    with st.expander("➕ ساخت پروژه"):
        with st.form("create_project_form", clear_on_submit=True):
            new_project = st.text_input("نام پروژه")
            create_clicked = st.form_submit_button("ایجاد پروژه")

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
    st.caption("ORBIT AI · اتصال به OpenRouter")


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

    if st.button("🗑️ پاک‌کردن تاریخچهٔ گفت‌وگو"):
        execute(
            "DELETE FROM messages WHERE project_id = ?",
            (project_id,),
        )
        st.rerun()

    prompt = st.chat_input("پیامت را اینجا بنویس...")

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
            "- " + row["content"]
            for row in notes
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
                    f"نام پروژه: {project_name}\n\n"
                    "یادداشت‌های ذخیره‌شده برای این پروژه:\n"
                    f"{memory_text}\n\n"
                    "از یادداشت‌ها فقط در صورت مرتبط بودن با درخواست فعلی "
                    "استفاده کن. اگر یادداشتی ارتباطی ندارد، آن را نادیده بگیر."
                ),
            }
        ]

        api_messages.extend(
            {
                "role": row["role"],
                "content": row["content"],
            }
            for row in recent
            if row["role"] in ("user", "assistant")
        )

        with st.spinner("در حال آماده‌سازی پاسخ..."):
            answer, error = ask_openrouter(api_messages)

        if answer is None:
            st.error("پاسخ آنلاین دریافت نشد.")
            st.code(
                error or "علت خطا مشخص نیست.",
                language="text",
            )
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
        task_text = st.text_input("عنوان کار جدید")
        add_task_clicked = st.form_submit_button("افزودن کار")

    if add_task_clicked:
        if task_text.strip():
            execute(
                """INSERT INTO tasks(project_id, task, done, created_at)
                   VALUES (?, ?, 0, ?)""",
                (project_id, task_text.strip(), timestamp()),
            )
            st.rerun()
        else:
            st.warning("عنوان کار را وارد کن.")

    tasks = fetch_all(
        """SELECT * FROM tasks
           WHERE project_id = ?
           ORDER BY id DESC""",
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
            execute(
                "DELETE FROM tasks WHERE id = ?",
                (task["id"],),
            )
            st.rerun()


# =========================
# Text Analysis
# =========================
with analysis_tab:
    st.subheader("📝 تحلیل و بازنویسی متن")

    text_input = st.text_area(
        "متن موردنظر را وارد کن",
        height=220,
        placeholder="متن را اینجا بنویس...",
    )

    analysis_kind = st.selectbox(
        "نوع درخواست",
        [
            "اصلاح نگارش و روان‌سازی",
            "خلاصه‌سازی",
            "بازنویسی حرفه‌ای",
            "استخراج نکات کلیدی",
            "ترجمه به انگلیسی",
            "ترجمه به فارسی",
        ],
    )

    if st.button("شروع تحلیل"):
        if not text_input.strip():
            st.warning("ابتدا متن را وارد کن.")
        else:
            instructions = {
                "اصلاح نگارش و روان‌سازی": (
                    "متن را با حفظ معنا، از نظر دستور زبان و جمله‌بندی "
                    "اصلاح کن. اگر متن فارسی است، فارسی روان و طبیعی "
                    "تحویل بده. توضیح اضافه نده مگر لازم باشد."
                ),
                "خلاصه‌سازی": (
                    "متن را دقیق و منظم خلاصه کن و نکات اصلی را حفظ کن."
                ),
                "بازنویسی حرفه‌ای": (
                    "متن را حرفه‌ای، روشن و طبیعی بازنویسی کن. "
                    "معنای اصلی را تغییر نده."
                ),
                "استخراج نکات کلیدی": (
                    "نکات اصلی را به فارسی روان و در قالب فهرست مرتب ارائه کن."
                ),
                "ترجمه به انگلیسی": (
                    "متن را به انگلیسی طبیعی و درست ترجمه کن. "
                    "از ترجمه تحت‌اللفظی پرهیز کن."
                ),
                "ترجمه به فارسی": (
                    "متن را به فارسی معیار، روان و طبیعی ترجمه کن."
                ),
            }

            with st.spinner("در حال بررسی متن..."):
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
                st.markdown(result)
            else:
                st.error("تحلیل آنلاین انجام نشد.")
                st.code(
                    error or "علت خطا مشخص نیست.",
                    language="text",
                )


# =========================
# Memory
# =========================
with memory_tab:
    st.subheader("🧠 حافظهٔ پروژه")

    st.write(
        "یادداشت‌های این بخش در گفت‌وگوهای بعدی همین پروژه "
        "به‌عنوان اطلاعات کمکی در اختیار ORBIT AI قرار می‌گیرند."
    )

    with st.form("add_note_form", clear_on_submit=True):
        note_text = st.text_area("یادداشت جدید")
        save_note = st.form_submit_button("ذخیرهٔ یادداشت")

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
        """SELECT * FROM notes
           WHERE project_id = ?
           ORDER BY id DESC""",
        (project_id,),
    )

    if not notes:
        st.info("حافظهٔ این پروژه خالی است.")

    for note in notes:
        with st.container(border=True):
            st.write(note["content"])
            st.caption(f"زمان ثبت: {note['created_at']}")

            if st.button(
                "حذف یادداشت",
                key=f"note_delete_{note['id']}",
            ):
                execute(
                    "DELETE FROM notes WHERE id = ?",
                    (note["id"],),
                )
                st.rerun()


# =========================
# Connection Diagnostics
# =========================
with settings_tab:
    st.subheader("🔧 بررسی اتصال OpenRouter")

    st.write(
        "در این بخش می‌توانی وضعیت اتصال را آزمایش کنی. "
        "کلید کامل API نمایش داده نمی‌شود."
    )

    api_key, selected_model = get_api_config()

    st.write(
        "وضعیت کلید:",
        "تنظیم شده" if api_key else "تنظیم نشده",
    )
    st.write("مدل فعال:", selected_model)
    st.write("نشانی سرویس:", API_URL)

    if st.button("🧪 آزمایش اتصال آنلاین"):
        with st.spinner("در حال آزمایش اتصال..."):
            test_answer, test_error = ask_openrouter([
                {
                    "role": "user",
                    "content": (
                        "فقط با یک جملهٔ کوتاه و به فارسی روان بگو "
                        "که اتصال ORBIT AI برقرار است."
                    ),
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
        "اگر اتصال ناموفق بود، تنظیمات Secrets را بررسی کن. "
        "کلید API را در گفت‌وگو یا تصویر منتشر نکن."
    )


st.divider()
st.caption(
    "ORBIT AI · دستیار فارسی با اتصال آنلاین به OpenRouter"
)
)
