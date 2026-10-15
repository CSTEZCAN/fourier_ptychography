for %%a in ("*.h264") do ffmpeg -n -i "%%a" -c:v h264_nvenc -b:v 2000k "%%~na.mp4"
