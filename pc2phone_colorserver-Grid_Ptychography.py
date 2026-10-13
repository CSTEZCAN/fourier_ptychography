import sys
import threading
import socket
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QSlider, QComboBox, QGroupBox,
    QColorDialog, QTextEdit, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# ==========================================
# 1. FLASK + SOCKETIO SERVER
# ==========================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'fourier_ptychography_scientific_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class ServerBridge(QObject):
    log_signal = pyqtSignal(str)
    client_connected_signal = pyqtSignal(dict)

bridge = ServerBridge()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Scientific Ptychography Display</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body, html { margin: 0; padding: 0; width: 100vw; height: 100vh; background: #000; overflow: hidden; }
        canvas { display: block; width: 100vw; height: 100vh; background: #000; touch-action: none; }
        #status { position: absolute; top: 10px; left: 10px; color: #00ff00; font-family: monospace; font-size: 14px; z-index: 100; pointer-events: none; background: rgba(0,0,0,0.7); padding: 5px; }
    </style>
</head>
<body>
    <div id="status">Connecting...</div>
    <canvas id="displayCanvas"></canvas>
    <script>
        const statusDiv = document.getElementById('status');
        const canvas = document.getElementById('displayCanvas');
        const ctx = canvas.getContext('2d');
        
        const socket = io({ transports: ['websocket', 'polling'] });

        let lastData = {
            mode: 'grid',
            color: '#FF0000',
            shape: 'circle',
            offset_x: 0,
            offset_y: 0,
            spot_size: 40,
            rows: 12,
            cols: 12,
            pitch_x: 50,
            pitch_y: 50,
            active_index: -1,
            is_blanking: false
        };

        function drawShape(cx, cy, size, shape, color) {
            ctx.fillStyle = color;
            ctx.strokeStyle = color;
            ctx.lineWidth = Math.max(2, size * 0.2);

            if (shape === 'circle') {
                ctx.beginPath();
                ctx.arc(cx, cy, size / 2, 0, 2 * Math.PI);
                ctx.fill();
            } else if (shape === 'square') {
                ctx.fillRect(cx - size / 2, cy - size / 2, size, size);
            } else if (shape === 'triangle') {
                // Centroid alignment for equilateral triangle
                const h = (Math.sqrt(3) / 2) * size;
                ctx.beginPath();
                ctx.moveTo(cx, cy - (2 / 3) * h);
                ctx.lineTo(cx + size / 2, cy + (1 / 3) * h);
                ctx.lineTo(cx - size / 2, cy + (1 / 3) * h);
                ctx.closePath();
                ctx.fill();
            } else if (shape === 'hollow_ring') {
                ctx.beginPath();
                ctx.arc(cx, cy, size / 2, 0, 2 * Math.PI);
                ctx.stroke();
            }
        }

        function draw(data) {
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            if (data.is_blanking) return;

            // Absolute screen optical center + custom user offset
            const centerX = (canvas.width / 2) + data.offset_x;
            const centerY = (canvas.height / 2) + data.offset_y;

            if (data.mode === 'all') {
                ctx.fillStyle = data.color;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            } else if (data.mode === 'single') {
                drawShape(centerX, centerY, data.spot_size, data.shape, data.color);
            } else if (data.mode === 'grid') {
                const rows = data.rows;
                const cols = data.cols;
                const pitchX = data.pitch_x;
                const pitchY = data.pitch_y;
                const spotSize = data.spot_size;

                const startX = centerX - ((cols - 1) * pitchX) / 2;
                const startY = centerY - ((rows - 1) * pitchY) / 2;

                let currentIndex = 0;

                for (let r = 0; r < rows; r++) {
                    for (let c = 0; c < cols; c++) {
                        if (data.active_index === -1 || data.active_index === currentIndex) {
                            let x = startX + c * pitchX;
                            let y = startY + r * pitchY;
                            drawShape(x, y, spotSize, data.shape, data.color);
                        }
                        currentIndex++;
                    }
                }
            }
        }

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            if (socket && socket.connected) {
                socket.emit('client_info', { width: canvas.width, height: canvas.height, ppr: window.devicePixelRatio });
            }
            draw(lastData);
        }
        window.addEventListener('resize', resize);
        resize();

        socket.on('connect', () => {
            statusDiv.innerText = "CONNECTED!";
            statusDiv.style.color = "#00ff00";
            socket.emit('client_info', { width: canvas.width, height: canvas.height, ppr: window.devicePixelRatio });
            setTimeout(() => { statusDiv.style.display = 'none'; }, 2000);
        });

        socket.on('disconnect', () => {
            statusDiv.style.display = 'block';
            statusDiv.innerText = "DISCONNECTED!";
            statusDiv.style.color = "#ff0000";
        });

        socket.on('render_state', function(data) {
            lastData = data;
            draw(data);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    bridge.log_signal.emit("Phone connected over HTTP!")

@socketio.on('client_info')
def handle_client_info(data):
    bridge.client_connected_signal.emit(data)
    bridge.log_signal.emit(f"Phone Display: {data['width']}x{data['height']} px (DPR: {data.get('ppr', 1)})")

def start_flask_http():
    socketio.run(app, host='0.0.0.0', port=5000, log_output=False)


# ==========================================
# 2. PYQT5 SCIENTIFIC CONTROLLER
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Fourier Ptychography Controller")
        self.setGeometry(100, 100, 1000, 850)

        self.current_color = "#FF0000"
        self.is_blanking_phase = False

        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.process_scan_step)

        self.init_ui()

        bridge.log_signal.connect(self.log)
        bridge.client_connected_signal.connect(self.update_client_info)

        self.server_thread = threading.Thread(target=start_flask_http, daemon=True)
        self.server_thread.start()

        local_ip = get_local_ip()
        self.log(f"HTTP Server Running! Address:\nhttp://{local_ip}:5000")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_panel = QVBoxLayout()

        # Mode & Geometry Group
        geom_group = QGroupBox("Pattern & LED Aperture Geometry")
        geom_layout = QVBoxLayout()

        geom_layout.addWidget(QLabel("Pattern Mode:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Full Screen", "Single Spot", "Grid Pattern"])
        self.combo_mode.setCurrentIndex(2)
        self.combo_mode.currentIndexChanged.connect(self.send_render_command)
        geom_layout.addWidget(self.combo_mode)

        geom_layout.addWidget(QLabel("LED Aperture Shape:"))
        self.combo_shape = QComboBox()
        self.combo_shape.addItems(["Circle (Standard)", "Square", "Triangle", "Hollow Ring (Darkfield)"])
        self.combo_shape.currentIndexChanged.connect(self.send_render_command)
        geom_layout.addWidget(self.combo_shape)

        geom_group.setLayout(geom_layout)
        left_panel.addWidget(geom_group)

        # Color Selection
        color_group = QGroupBox("Illumination Wavelength / Color")
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("Select Color")
        self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: white; font-weight: bold;")
        self.btn_color.clicked.connect(self.choose_color)
        color_layout.addWidget(self.btn_color)
        color_group.setLayout(color_layout)
        left_panel.addWidget(color_group)

        # Center Position Adjusters
        align_group = QGroupBox("Optical Center Alignment Sliders")
        align_layout = QVBoxLayout()

        align_layout.addWidget(QLabel("Center Offset X (px):"))
        self.slider_offset_x = QSlider(Qt.Horizontal)
        self.slider_offset_x.setRange(-800, 800)
        self.slider_offset_x.setValue(0)
        self.slider_offset_x.valueChanged.connect(self.send_render_command)
        align_layout.addWidget(self.slider_offset_x)

        align_layout.addWidget(QLabel("Center Offset Y (px):"))
        self.slider_offset_y = QSlider(Qt.Horizontal)
        self.slider_offset_y.setRange(-800, 800)
        self.slider_offset_y.setValue(0)
        self.slider_offset_y.valueChanged.connect(self.send_render_command)
        align_layout.addWidget(self.slider_offset_y)

        align_group.setLayout(align_layout)
        left_panel.addWidget(align_group)

        # Scientific Calibration & Repeatability
        metric_group = QGroupBox("Scientific Metrics & Repeatability")
        metric_layout = QVBoxLayout()

        metric_layout.addWidget(QLabel("Pixel Pitch / Size (mm/px):"))
        self.spin_pixel_pitch = QDoubleSpinBox()
        self.spin_pixel_pitch.setRange(0.001, 1.000)
        self.spin_pixel_pitch.setDecimals(4)
        self.spin_pixel_pitch.setValue(0.0635)
        self.spin_pixel_pitch.valueChanged.connect(self.update_physical_metrics)
        metric_layout.addWidget(self.spin_pixel_pitch)

        metric_layout.addWidget(QLabel("LED Settling On-Delay (ms):"))
        self.spin_on_delay = QSpinBox()
        self.spin_on_delay.setRange(0, 5000)
        self.spin_on_delay.setValue(200)
        metric_layout.addWidget(self.spin_on_delay)

        metric_layout.addWidget(QLabel("Off-State Blanking Duration (ms):"))
        self.spin_off_delay = QSpinBox()
        self.spin_off_delay.setRange(0, 2000)
        self.spin_off_delay.setValue(50)
        metric_layout.addWidget(self.spin_off_delay)

        self.lbl_metric_info = QLabel("Physical Pitch: -- mm | Spot Diameter: -- mm")
        self.lbl_metric_info.setStyleSheet("color: #1976D2; font-weight: bold;")
        metric_layout.addWidget(self.lbl_metric_info)

        metric_group.setLayout(metric_layout)
        left_panel.addWidget(metric_group)

        # Grid Matrix Control
        grid_group = QGroupBox("Ptychography Grid Dimensions")
        grid_layout = QVBoxLayout()

        row_col_layout = QHBoxLayout()
        row_col_layout.addWidget(QLabel("Rows:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 40)
        self.spin_rows.setValue(12)
        self.spin_rows.valueChanged.connect(self.on_grid_dimensions_changed)
        row_col_layout.addWidget(self.spin_rows)

        row_col_layout.addWidget(QLabel("Cols:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 40)
        self.spin_cols.setValue(12)
        self.spin_cols.valueChanged.connect(self.on_grid_dimensions_changed)
        row_col_layout.addWidget(self.spin_cols)
        grid_layout.addLayout(row_col_layout)

        grid_layout.addWidget(QLabel("Pitch X (px):"))
        self.slider_pitch_x = QSlider(Qt.Horizontal)
        self.slider_pitch_x.setRange(5, 300)
        self.slider_pitch_x.setValue(50)
        self.slider_pitch_x.valueChanged.connect(self.send_render_command)
        grid_layout.addWidget(self.slider_pitch_x)

        grid_layout.addWidget(QLabel("Pitch Y (px):"))
        self.slider_pitch_y = QSlider(Qt.Horizontal)
        self.slider_pitch_y.setRange(5, 300)
        self.slider_pitch_y.setValue(50)
        self.slider_pitch_y.valueChanged.connect(self.send_render_command)
        grid_layout.addWidget(self.slider_pitch_y)

        grid_layout.addWidget(QLabel("Spot Size (px):"))
        self.slider_size = QSlider(Qt.Horizontal)
        self.slider_size.setRange(2, 200)
        self.slider_size.setValue(30)
        self.slider_size.valueChanged.connect(self.send_render_command)
        grid_layout.addWidget(self.slider_size)

        grid_group.setLayout(grid_layout)
        left_panel.addWidget(grid_group)

        # Automated Sequence
        scan_group = QGroupBox("Automated Sequence Control")
        scan_layout = QVBoxLayout()

        scan_layout.addWidget(QLabel("Active LED Index (-1 = All On):"))
        self.spin_active = QSpinBox()
        self.spin_active.setRange(-1, 143)
        self.spin_active.setValue(-1)
        self.spin_active.valueChanged.connect(self.send_render_command)
        scan_layout.addWidget(self.spin_active)

        self.btn_scan_toggle = QPushButton("START SCIENTIFIC SCAN")
        self.btn_scan_toggle.setCheckable(True)
        self.btn_scan_toggle.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 10px;")
        self.btn_scan_toggle.clicked.connect(self.toggle_scanning)
        scan_layout.addWidget(self.btn_scan_toggle)

        scan_group.setLayout(scan_layout)
        left_panel.addWidget(scan_group)

        left_panel.addStretch()
        main_layout.addLayout(left_panel, stretch=6)

        # Log Window
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("System Logs:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        right_panel.addWidget(self.txt_log)

        main_layout.addLayout(right_panel, stretch=4)
        self.update_physical_metrics()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: white; font-weight: bold;")
            self.send_render_command()

    def update_client_info(self, data):
        self.update_physical_metrics()

    def update_physical_metrics(self):
        pitch = self.spin_pixel_pitch.value()
        pitch_x_mm = self.slider_pitch_x.value() * pitch
        spot_mm = self.slider_size.value() * pitch
        self.lbl_metric_info.setText(f"Physical Pitch X: {pitch_x_mm:.2f} mm | Spot Size: {spot_mm:.2f} mm")

    def on_grid_dimensions_changed(self):
        total_spots = self.spin_rows.value() * self.spin_cols.value()
        self.spin_active.setRange(-1, total_spots - 1)
        self.update_physical_metrics()
        self.send_render_command()

    def toggle_scanning(self, checked):
        if checked:
            self.btn_scan_toggle.setText("STOP SCAN")
            self.btn_scan_toggle.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 10px;")
            self.spin_active.setValue(0)
            self.is_blanking_phase = False
            self.scan_timer.start(self.spin_on_delay.value())
        else:
            self.btn_scan_toggle.setText("START SCIENTIFIC SCAN")
            self.btn_scan_toggle.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 10px;")
            self.scan_timer.stop()
            self.is_blanking_phase = False
            self.spin_active.setValue(-1)
            self.send_render_command()

    def process_scan_step(self):
        off_delay = self.spin_off_delay.value()
        on_delay = self.spin_on_delay.value()

        if off_delay > 0 and not self.is_blanking_phase:
            self.is_blanking_phase = True
            self.send_render_command()
            self.scan_timer.setInterval(off_delay)
        else:
            self.is_blanking_phase = False
            current = self.spin_active.value()
            total_spots = self.spin_rows.value() * self.spin_cols.value()
            next_index = (current + 1) % total_spots
            self.spin_active.setValue(next_index)
            self.scan_timer.setInterval(on_delay)

    def send_render_command(self):
        mode_map = {0: 'all', 1: 'single', 2: 'grid'}
        shape_map = {0: 'circle', 1: 'square', 2: 'triangle', 3: 'hollow_ring'}

        payload = {
            'mode': mode_map[self.combo_mode.currentIndex()],
            'shape': shape_map[self.combo_shape.currentIndex()],
            'color': self.current_color,
            'offset_x': self.slider_offset_x.value(),
            'offset_y': self.slider_offset_y.value(),
            'spot_size': self.slider_size.value(),
            'rows': self.spin_rows.value(),
            'cols': self.spin_cols.value(),
            'pitch_x': self.slider_pitch_x.value(),
            'pitch_y': self.slider_pitch_y.value(),
            'active_index': self.spin_active.value(),
            'is_blanking': self.is_blanking_phase
        }

        socketio.emit('render_state', payload)
        self.update_physical_metrics()

    def log(self, msg):
        self.txt_log.append(msg)

if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app_qt.exec_())