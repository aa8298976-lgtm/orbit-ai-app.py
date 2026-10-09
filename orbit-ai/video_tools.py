
import os
import subprocess
import tempfile

import streamlit as st
import imageio_ffmpeg


def render_video_tools():
    st.header("🎬 ORBIT AI | ویرایش ویدئو")
    st.caption("برش ویدئو، تبدیل به MP4 و حذف صدا")

    uploaded = st.file_uploader(
        "ویدئوی خود را انتخاب کن",
        type=["mp4", "mov", "m4v", "avi", "mkv"]
    )

    if not uploaded:
        st.info("برای شروع، یک ویدئو بارگذاری کن.")
        return

    max_size = 150 * 1024 * 1024
    if uploaded.size > max_size:
        st.error("حجم فایل باید کمتر از 150 مگابایت باشد.")
        return

    st.video(uploaded)

    start = st.number_input(
        "زمان شروع (ثانیه)",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

    end = st.number_input(
        "زمان پایان (ثانیه)",
        min_value=1.0,
        value=10.0,
        step=1.0
    )

    mute = st.checkbox("حذف صدای ویدئو")
    convert_mp4 = st.checkbox(
        "تبدیل خروجی به MP4",
        value=True
    )

    if st.button("✂️ پردازش ویدئو", type="primary"):
        if end <= start:
            st.error("زمان پایان باید از زمان شروع بیشتر باشد.")
            return

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input_video")
            output_path = os.path.join(tmp, "output.mp4")

            with open(input_path, "wb") as f:
                f.write(uploaded.getvalue())

            command = [
                ffmpeg,
                "-y",
                "-ss", str(start),
                "-i", input_path,
                "-t", str(end - start),
            ]

            if mute:
                command += ["-an"]
            else:
                command += ["-c:a", "aac"]

            if convert_mp4:
                command += [
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                ]
            else:
                command += ["-c", "copy"]

            command += [output_path]

            try:
                with st.spinner("در حال پردازش ویدئو..."):
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        check=False,
                    )

                if result.returncode != 0:
                    st.error("پردازش ویدئو ناموفق بود.")
                    st.code(result.stderr[-2500:])
                    return

                with open(output_path, "rb") as f:
                    video_bytes = f.read()

                st.success("پردازش ویدئو با موفقیت انجام شد.")
                st.video(video_bytes)

                st.download_button(
                    "⬇️ دانلود ویدئوی ویرایش‌شده",
                    data=video_bytes,
                    file_name="orbit_ai_edited.mp4",
                    mime="video/mp4",
                )

            except subprocess.TimeoutExpired:
                st.error(
                    "پردازش بیش از حد طول کشید. "
                    "یک ویدئوی کوتاه‌تر امتحان کن."
                )
            except Exception as exc:
                st.error(f"خطا در پردازش: {exc}")
