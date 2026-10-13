#!/usr/bin/env bash

set -e

# --- Configuration ---
RECORD_DIR="${HOME}/camera_videos"
MAX_SIZE_KB=$((1024 * 1024)) # 1 GB Storage limit
DURATION_MS=300000            # 30 seconds total run time
WIDTH=1080
HEIGHT=1080

# --- Extreme Low-Light & Grayscale Overrides ---
FPS=1                        # 1 FPS (allows 1-second long exposure per frame)
SHUTTER=1000000              # 1,000,000 µs = 1 full second open shutter
ISO=1600                     # Max hardware ISO
ANALOG_GAIN=12.0             # Maximum sensor hardware amplification
DIGITAL_GAIN=2.0              # Digital gain boost
AWB_GAINS="1.0,1.0"          # Neutral white balance gains

mkdir -p "${RECORD_DIR}"
cd "${RECORD_DIR}"

TIMESTAMP=$(date +"%Y-%m-%d-%H-%m-%S")
H264_FILE="${TIMESTAMP}.h264"

echo "Recording extreme low-light grayscale video (1 FPS, 1s shutter) -> ${H264_FILE}..."

# Execute raw H.264 capture with color channels zeroed out (-cfx 128:128)
raspivid -t "${DURATION_MS}" \
         -w "${WIDTH}" -h "${HEIGHT}" \
         -fps "${FPS}" \
         -cfx 128:128 \
         -awb off -awbg "${AWB_GAINS}" \
         -ex off -ss "${SHUTTER}" \
         -ISO "${ISO}" \
         -ag "${ANALOG_GAIN}" -dg "${DIGITAL_GAIN}" \
         -o "${H264_FILE}"

echo "Capture complete."

# Verification check
if [ -f "${H264_FILE}" ]; then
    echo "Successfully generated: $(ls -lh "${H264_FILE}" | awk '{print $9, "("$5")"}')"
fi

# Cleanup: Keep folder under 1GB threshold by deleting oldest .h264 files
while true; do
    CURRENT_SIZE_KB=$(du -ck *.h264 2>/dev/null | awk 'END {print $1}')
    
    if [ -z "${CURRENT_SIZE_KB}" ] || [ "${CURRENT_SIZE_KB}" -le "${MAX_SIZE_KB}" ]; then
        break
    fi

    OLDEST_FILE=$(ls -1t *.h264 2>/dev/null | tail -n 1)

    if [ -n "${OLDEST_FILE}" ]; then
        echo "Storage threshold reached (${CURRENT_SIZE_KB} KB). Removing oldest file: ${OLDEST_FILE}"
        rm -f "${OLDEST_FILE}"
    else
        break
    fi
done
