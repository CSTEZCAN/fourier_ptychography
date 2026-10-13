# 🔬 Microscope OLED Pattern Controller & Ptychography Suite

A hybrid **PyQt5 desktop application**, **Flask + Socket.IO web server**, and **Differential Phase Contrast (DPC) 3D reconstruction engine** designed to control real-time, custom illumination patterns on external displays (e.g., a smartphone used as a programmable microscope OLED light source) and process the resulting microscopy data.

---

## 🌟 Key Features

### 🖥️ Display & Illumination Engine

* **Real-Time Web Canvas**: Serves a full-screen, ultra-low latency HTML5 Canvas over WebSockets to render light patterns dynamically on connected mobile devices.


* **Multiple Pattern Modes**:
* **Full Screen**: Uniform illumination across the entire target display.


* **Single Spot / Pixel**: Precise, single target light source with custom spatial offset coordinates.


* **Circular LED Ring**: Multi-point ring arrangement simulating physical LED rings for computational microscopy and circular Ptychography.


* **Matrix Grid**: Configurable $M \times N$ matrix grid with customizable horizontal/vertical pitch ($X/Y$ spacing) for grid-based Ptychography.




* **Custom Aperture Geometries**: Toggle spot aperture shapes between **Circle**, **Square**, **Triangle**, and **Hollow Ring** (for Darkfield illumination).



### ⚙️ Desktop Controller & Automation

* **Interactive PyQt5 GUI**: Real-time sliders for $X/Y$ center offset, pitch, ring radius, spot thickness, and RGB color/wavelength selection.


* **Resolution & Scale Syncing**: Automatically detects client screen dimensions and translates pixel pitch metrics into physical dimensions ($\text{mm/px}$).


* **Automated Flashing Sequencer**: Programmable macro that steps through individual LEDs on the ring or grid sequentially, featuring configurable LED settling delays and off-state blanking intervals.



### 📐 DPC 3D Reconstruction Pipeline

* **Raw Video/Image Processing**: Automatically extracts frame sequences corresponding to multi-angle illumination patterns.


* **Input Contrast Enhancement**: Built-in CLAHE (Contrast Limited Adaptive Histogram Equalization), percentile stretching, and gamma correction pre-processing to eliminate baseline sensor noise floor.


* **Phase Integration**: Computes normalized $DPC_x$ and $DPC_y$ gradients, applies reflective padding to eliminate edge collapse artifacts, and flattens background variation via Gaussian filtering.


* **Interactive 3D Surface Mesh**: Embedded Matplotlib 3D viewer featuring interactive sliders for Z-amplification, mesh subsampling, denoising sigma, window clipping, and colormap selection.



---

## 📦 Requirements

```text
PyQt5
Flask
Flask-SocketIO
python-socketio
python-engineio
opencv-python
numpy
scipy
matplotlib

```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install PyQt5 Flask Flask-SocketIO python-socketio python-engineio opencv-python numpy scipy matplotlib

```

### 2. Run Circular Ptychography Server

```bash
python pc2phone_colorserver-Circular_Ptychography.py

```

### 3. Run Grid Ptychography Server

```bash
python pc2phone_colorserver-Grid_Ptychography.py

```

### 4. Connect Mobile Device

Navigate to `http://<YOUR_PC_IP>:5000` on your smartphone browser to connect it as an external OLED illumination source.

### 5. Run DPC 3D Reconstruction

```bash
python reconstruction.py

```

---

## 📄 License

This project is licensed under the **MIT License**.
