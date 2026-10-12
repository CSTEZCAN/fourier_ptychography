## 🔬 Microscope OLED Pattern Controller

A hybrid **PyQt5 desktop application** and **Flask + Socket.IO web server** designed to control real-time, custom illumination patterns on an external screen (e.g., a smartphone used as a microscope OLED ring light).

### Key Features

* **Real-Time Web Canvas**: Serves a full-screen, ultra-low latency HTML5 Canvas over WebSockets to render light patterns dynamically on connected mobile devices.
* **Multiple Illumination Modes**:
  * **Full Screen**: Uniform illumination across the target screen.
  * **Single Spot**: Targetable single light source with adjustable size and coordinates.
  * **LED Ring Pattern**: Multi-point ring arrangement simulating physical LED rings for computational microscopy/Fourier Ptychography.
* **Interactive Desktop GUI**:
  * **Pattern Customization**: Live sliders for $X/Y$ center offset, ring radius, spot thickness, and RGB color selection.
  * **Resolution Syncing**: Automatically scales slider ranges based on the connected client's screen dimensions.
* **Automated Sequential Flashing**: Built-in macro sequencer that steps through individual LEDs on the ring one-by-one with configurable millisecond delay intervals.
