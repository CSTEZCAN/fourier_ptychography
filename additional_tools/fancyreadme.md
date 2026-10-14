
### 1. Raspberry Pi Setup & Video Capture

1. Boot the Raspberry Pi.
2. Copy `camserver.py`, `camserver.sh`, and `capture.sh` to the home directory (`/home/pi`).


3. Make the shell scripts executable:

```bash
chmod +x camserver.sh
chmod +x capture.sh

```

4. Open crontab:

```bash
crontab -e

```

5. Add the following line at the end of the file:

```text
@reboot /home/pi/camserver.sh

```

6. Save and exit (`Ctrl + O`, `Enter`, `Ctrl + X`).
7. Reboot the Raspberry Pi:

```bash
sudo reboot

```

8. After reboot, log in and retrieve the IP address for the PC connection:

```bash
ifconfig

```

9. Place the OLED smartphone on the microscope stage, place and adjust the slide pattern, and focus the slide pattern using the live camera preview:

```bash
raspistill -t 0

```

10. Start the automated video capture on the Raspberry Pi:



```bash
sh capture.sh

```

---

### 2. Illumination & Alignment (PC & Smartphone)

1. On the PC, run the Python controller server:



```bash
python pc2phone_colorserver-Grid_Ptychography.py

```

*(Reference `pc2phone_colorserver-Grid_Ptychography-settings.png` for control panel settings if needed).*

2. Open a browser on the PC and connect to the Raspberry Pi control/stream interface:

```text
http://192.168.1.x:8080

```

*(Replace `192.168.1.x` with the IP obtained from `ifconfig`)*.

3. On the smartphone mounted under the microscope, open a browser and navigate to the PC server UI:



```text
http://192.168.1.x:5000

```

(Replace `192.168.1.x` with your PC's IP address on the local network).

4. Adjust the center view and alignment using the PC controller GUI controls.



---

### 3. File Transfer & Video Conversion

1. Open the browser window connected to `192.168.1.x:8080`.


2. Navigate to the `camera_videos/` folder and download the raw captured video file (e.g., `202x-xx-xx-xx-xx-xx.h264`).


3. Convert the raw `.h264` file to `.mp4` using GPU-accelerated FFmpeg:

```bash
h264tomp4.bat
```

---

### 4. 3D Reconstruction Pipeline

#### Option A: Qt GUI Reconstruction

1. Run the Qt GUI application:



```bash
python reconstruction_grid_qt.py

```

2. Update the video file path, grid LED dimensions, optical parameters, and rendering options inside the interface, then click **PROCESS & RECONSTRUCT**.



#### Option B: Plotly HTML Script Reconstruction

1. Open `construction4htmlv2.py` (or `construction4html.py`) in a text editor.


2. Update the `VIDEO_PATH`, `GRID_ROWS`, `GRID_COLS`, and configuration settings to match your setup.


3. Execute the script to generate and open the interactive 3D visualization:



```bash
python construction4htmlv2.py

```
