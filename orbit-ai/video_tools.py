

import os
import subprocess
import tempfile

import streamlit as st
import imageio_ffmpeg


def render_video_tools():
    st.title("🎬 ORBIT AI | Video Studio")
    st.caption("برش، رنگ، سرعت و خروجی ویدئو")

    uploaded = st.file_uploader(
        "انتخاب ویدئو",
        type=["mp4", "mov", "m4v", "avi", "mkv"],
        key="orbit_video_upload",
    )

    if not uploaded:
        st.info("برای شروع یک ویدئو بارگذاری کن.")
        return

    if uploaded.size > 150 * 1024 * 1024:
        st.error("حداکثر حجم فایل ۱۵۰ مگابایت است.")
        return

    st.video(uploaded)

    st.subheader("✂️ برش ویدئو")
    start = st.number_input(
        "شروع (ثانیه)", min_value=0.0, value=0.0, step=1.0
    )
    end = st.number_input(
        "پایان (ثانیه)", min_value=1.0, value=10.0, step=1.0
    )

    st.subheader("🎨 تنظیمات تصویر")
    brightness = st.slider(
        "روشنایی", 0.5, 1.8, 1.0, 0.05
    )
    contrast = st.slider(
        "کنتراست", 0.5, 2.0, 1.0, 0.05
    )
    saturation = st.slider(
        "اشباع رنگ", 0.0, 2.0, 1.0, 0.05
    )

    preset = st.selectbox(
        "فیلتر",
        ["طبیعی", "سیاه‌وسفید سینمایی", "گرم", "سرد"],
    )

    aspect = st.selectbox(
        "ابعاد خروجی",
        ["اصلی", "استوری و ریلز 9:16", "پست 4:5", "مربع 1:1", "افقی 16:9"],
    )

    speed = st.selectbox(
        "سرعت پخش",
        ["0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x"],
        index=2,
    )

    mute = st.checkbox("حذف کامل صدای ویدئو")
    make_mp4 = st.checkbox("خروجی MP4", value=True)

    if st.button("🚀 پردازش ویدئو", type="primary"):
        if end <= start:
            st.error("زمان پایان باید بیشتر از زمان شروع باشد.")
            return

        if end - start > 300:
            st.error("برای جلوگیری از فشار روی سرور، هر بار حداکثر ۵ دقیقه پردازش کن.")
            return

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        speed_value = float(speed.replace("x", ""))

        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input_video")
            output_path = os.path.join(tmp, "orbit_output.mp4")

            with open(input_path, "wb") as f:
                f.write(uploaded.getvalue())

            filters = []

            filters.append(
                f"eq=brightness={brightness - 1:.3f}:"
                f"contrast={contrast:.3f}:"
                f"saturation={saturation:.3f}"
            )

            if preset == "سیاه‌وسفید سینمایی":
                filters.append("hue=s=0")
                filters.append("eq=contrast=1.15")
            elif preset == "گرم":
                filters.append("colorbalance=rs=0.06:bs=-0.05")
            elif preset == "سرد":
                filters.append("colorbalance=rs=-0.05:bs=0.06")

            ratio_filters = {
                "استوری و ریلز 9:16":
                    "crop='if(gt(iw/ih,9/16),ih*9/16,iw)':'if(gt(iw/ih,9/16),ih,iw*16/9)',scale=720:1280",
                "پست 4:5":
                    "crop='if(gt(iw/ih,4/5),ih*4/5,iw)':'if(gt(iw/ih,4/5),ih,iw*5/4)',scale=720:900",
                "مربع 1:1":
                    "crop='min(iw,ih)':'min(iw,ih)',scale=720:720",
                "افقی 16:9":
                    "crop='if(gt(iw/ih,16/9),ih*16/9,iw)':'if(gt(iw/ih,16/9),ih,iw*9/16)',scale=1280:720",
            }

            if aspect != "اصلی":
                filters.append(ratio_filters[aspect])

            filters.append(f"setpts=PTS/{speed_value}")

            command = [
                ffmpeg, "-y",
                "-ss", str(start),
                "-i", input_path,
                "-t", str(end - start),
                "-vf", ",".join(filters),
            ]

            if mute:
                command += ["-an"]
            elif speed_value != 1:
                command += [
                    "-af",
                    f"atempo={speed_value}"
                ]

            command += [
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path,
            ]

            try:
                with st.spinner("در حال پردازش..."):
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        check=False,
                    )

                if result.returncode != 0:
                    st.error("پردازش ناموفق بود.")
                    st.code(result.stderr[-2000:])
                    return

                with open(output_path, "rb") as f:
                    video_data = f.read()

                st.success("ویدئو آماده است.")
                st.video(video_data)

                st.download_button(
                    "⬇️ دانلود MP4",
                    data=video_data,
                    file_name="orbit_ai_video.mp4",
                    mime="video/mp4",
                )

            except subprocess.TimeoutExpired:
                st.error("پردازش بیش از حد طول کشید. ویدئوی کوتاه‌تری امتحان کن.")
            except Exception as exc:
                st.error(f"خطا: {exc}")
