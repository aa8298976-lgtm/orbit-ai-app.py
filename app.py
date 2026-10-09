
import streamlit as st

from orbit_ai.core.planner import create_plan
from core.agent import OrbitAgent


st.set_page_config(
    page_title="ORBIT AI",
    page_icon="🌐",
    layout="centered"
)

st.title("🌐 ORBIT AI")
st.caption("Open-World AI | Offline-ready V0.2")

st.write(
    "یک دستیار قابل توسعه برای برنامه‌ریزی، "
    "تحلیل متن و اجرای ابزارهای داخلی."
)

if "agent" not in st.session_state:
    st.session_state.agent = OrbitAgent()

if "history" not in st.session_state:
    st.session_state.history = []

goal = st.text_area(
    "🎯 هدف خود را وارد کن",
    placeholder="مثلاً: برای یادگیری برنامه‌نویسی یک برنامه ۳۰ روزه بساز."
)

col1, col2 = st.columns(2)

with col1:
    plan_clicked = st.button(
        "🧠 ساخت برنامه",
        use_container_width=True
    )

with col2:
    clear_clicked = st.button(
        "🗑️ پاک‌کردن نتیجه",
        use_container_width=True
    )

if clear_clicked:
    st.session_state.history = []
    st.rerun()

if plan_clicked:
    if not goal.strip():
        st.warning("ابتدا یک هدف وارد کن.")
    else:
        with st.spinner("در حال برنامه‌ریزی..."):
            plan = create_plan(goal)

        st.session_state.history.insert(
            0,
            {
                "goal": goal,
                "plan": plan
            }
        )

if st.session_state.history:
    st.subheader("📋 نتیجه برنامه‌ریزی")

    for item in st.session_state.history:
        with st.expander(item["goal"], expanded=True):
            plan = item["plan"]

            st.write("حالت اجرا:", plan.get("mode", "unknown"))

            if "steps" in plan:
                for index, step in enumerate(
                    plan["steps"],
                    start=1
                ):
                    st.write(f"{index}. {step}")

                st.info(plan.get("message", ""))
            else:
                st.write(plan.get("plan", plan))

st.divider()

st.subheader("🧰 ابزارهای داخلی")

text = st.text_input(
    "متن برای تحلیل",
    placeholder="یک جمله وارد کن..."
)

if st.button("تحلیل متن"):
    if text.strip():
        result = st.session_state.agent.use_tool(
            "text_analyzer",
            text=text
        )
        st.json(result)
    else:
        st.warning("ابتدا یک متن وارد کن.")

st.caption(
    "نسخه آزمایشی: برنامه‌ریزی آفلاین و ابزارهای پایه فعال‌اند؛ "
    "اتصال مدل ابری به اعتبار API نیاز دارد."
)
