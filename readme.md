# 🔬 Mobile-OLED Fourier Ptychography & DPC Microscopy Suite

An open-source hardware-software framework that converts a smartphone display into a dynamic, programmable OLED illumination array for computational phase imaging, Differential Phase Contrast (DPC), and Fourier Ptychography (FP) microscopy

This repository provides an end-to-end pipeline—from hardware control and acquisition scripts on Raspberry Pi to automated video clustering, Frankot-Chellappa phase integration, and interactive 3D web visualizations

### PC Server Demo of using OLED as light source for fourier ptychography (Youtube)
[![IMAGE ALT TEXT](http://img.youtube.com/vi/USzi0stUIRU/0.jpg)](http://www.youtube.com/watch?v=USzi0stUIRU " PC Server Demo of using OLED as light source for fourier ptychography ")

### Repurposing Cracked Screen Galaxy S10 for Ptychography Light Source (Youtube)
[![IMAGE ALT TEXT](http://img.youtube.com/vi/12SVKarnK3o/0.jpg)](http://www.youtube.com/watch?v=12SVKarnK3o " Repurposing Cracked Screen Galaxy S10 for Ptychography Light Source ")

### videosample pollengrain 2026 10 13 17 10 21b (Youtube)
[![IMAGE ALT TEXT](http://img.youtube.com/vi/1tK447fYKqI/0.jpg)](http://www.youtube.com/watch?v=1tK447fYKqI " videosample pollengrain 2026 10 13 17 10 21b ")

### videosample fresnelzoneplate 2026 10 13 11 10 34 (Youtube)
[![IMAGE ALT TEXT](http://img.youtube.com/vi/V9b4FgiHLlA/0.jpg)](http://www.youtube.com/watch?v=V9b4FgiHLlA " videosample fresnelzoneplate 2026 10 13 11 10 34 ")

### 3D Reconstruction of the Fresnel Zone Plate (Youtube)
[![IMAGE ALT TEXT](http://img.youtube.com/vi/OYcoacdYIvk/0.jpg)](http://www.youtube.com/watch?v=OYcoacdYIvk " 3D Reconstruction of the Fresnel Zone Plate ")



## ✨ Features

### 🖥️ Display Control & Illumination Engine (`run1st_pc2phone_colorserver-Grid_Ptychography.py`)
- **PyQt5 Desktop Control GUI**: Complete manual and automated control over pattern geometry, grid spacing, spot sizing, offsets, and wavelengths
- **WebSocket Web Canvas Interface**: Low-latency, full-screen HTML5 rendering engine running over Flask & Socket.IO
- **Custom LED Geometries**: Supports Circle, Square, Triangle, and Hollow Ring (Darkfield) aperture geometries
- **Automated Sequencer with Blanking**: Step-by-step LED pattern scanning with configurable settling delays (`on_delay`) and off-state blanking phases (`off_delay`) to clear sensor buffer lag
- **Physical Calibration**: Real-time conversion between screen pixel dimensions and physical metrics ($\text{mm/px}$)

### 🎥 Low-Light Camera Acquisition (`additional_tools/`)
- **Extreme Long-Exposure Script (`capture.sh`)**: High-gain, 1 FPS capture script utilizing 1-second ($1,000,000\,\mu\text{s}$) open shutter times, $12.0\times$ analog gain, zeroed chroma (`-cfx 128:128`), and fixed AWB for low-light raw H.264 capture
- **Automated Logging & Storage Management**: Prevents storage overflow by maintaining a strict disk quota (e.g., 1 GB) using rolling file deletion
- **Video Conversion Helper (`h264tomp4.bat`)**: FFmpeg NVENC batch script to convert raw `.h264` video streams to `.mp4`

### 📐 DPC 3D Reconstruction Pipeline (`run2nd_construction4htmlv2.py`)
- **Automated State Clustering**: Reads video frame streams without skipping and automatically clusters frames into their respective $N \times N$ LED spatial illumination angles
- **Intensity Normalization**: Corrects for screen brightness variations across LED positions during frame binning
- **2D DPC Phase Gradients**: Calculates directional differential gradients ($DPC_X$ and $DPC_Y$) across top/bottom and left/right LED array hemispheres
- **Frankot-Chellappa Integration**: Reconstructs quantitative phase maps using Fourier-space gradient integration with high-pass tilt filtering and reflective boundary padding
- **Interactive 3D Surface Export**: Generates standalone interactive 3D HTML surface plots (`3d_reconstruction.html`) powered by Plotly



## 🛠️ Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/CSTEZCAN/fourier_ptychography
   cd fourier_ptychography

   ```

2. **Install Required Python Packages:**
   ```bash
   pip install -r requirements.txt
   
   ```


*(For reconstruction scripts, ensure OpenCV, SciPy, NumPy, and Plotly are also installed)*


---

## 🚀 Step-by-Step Workflow

### Step 1: Launch the OLED Display Controller

Run the pattern controller server on your primary PC:

```bash
python run1st_pc2phone_colorserver-Grid_Ptychography.py

```

1. Open the indicated HTTP URL (e.g., `http://<YOUR_PC_IP>:5000`) on your mobile device (OLED smartphone/tablet).


2. Align the smartphone under the objective lens as the primary light source.


3. Adjust the grid rows/cols, aperture shape, and color from the PyQt5 desktop GUI.



### Step 2: Acquire Multi-Angle Datasets (Raspberry Pi)

On your camera-equipped Raspberry Pi:

```bash
chmod +x additional_tools/capture.sh
./additional_tools/capture.sh

```

Convert the resulting H.264 video file into MP4 using `ffmpeg` or `additional_tools/h264tomp4.bat`.

### Step 3: Run 3D Phase Reconstruction

Update the video path inside `run2nd_construction4htmlv2.py` and run:

```bash
python run2nd_construction4htmlv2.py

```

The script will process the video, cluster frame states, integrate phase gradients, and automatically open `3d_reconstruction.html` in your web browser.

---

## 📁 Repository Structure

```text
.
├── additional_tools/
│   ├── camserver.py            # Flask HTTP video stream server for RPi camera
│   ├── capture.sh              # Bash script for extreme long-exposure H.264 capture
│   ├── h264tomp4.bat           # FFmpeg batch converter for raw camera streams
│   └── rpi_camserver.sh        # System startup service wrapper for camserver
├── run1st_pc2phone_colorserver-Grid_Ptychography.py  # GUI & Socket.IO server
├── run2nd_construction4htmlv2.py                     # DPC processing & 3D Plotly engine
├── sample_3d_reconstruction_demo_html.zip             # Sample output HTML files
├── videosample_fresnelzoneplate_2026-10-13-11-10-34.mp4 # Sample dataset: Zone Plate
├── videosample_pollengrain_2026-10-13-17-10-21b.mp4   # Sample dataset: Pollen Grain
├── requirements.txt            # Core dependencies list
└── LICENSE                     # MIT License

```

---



## 📄 License

This project is open-source and released under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```
