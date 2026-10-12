#powershell - set port rule
#New-NetFirewallRule -DisplayName "Allow Flask 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow -Profile Any
import sys
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QSlider, QComboBox, QGroupBox,
    QColorDialog, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# ==========================================
# 1. FLASK + HTTPS SOCKETIO SERVER
# ==========================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'microscope_oled_https_key'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class ServerBridge(QObject):
    log_signal = pyqtSignal(str)
    client_connected_signal = pyqtSignal(dict)

bridge = ServerBridge()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>OLED Pattern Display (Interactive)</title>
    <!-- Use CDN with fallback or inline minimal Socket.IO client -->
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body, html { margin: 0; padding: 0; width: 100vw; height: 100vh; background: #000; overflow: hidden; }
        canvas { display: block; width: 100vw; height: 100vh; background: #000; touch-action: none; }
        #status { position: absolute; top: 10px; left: 10px; color: #00ff00; font-family: monospace; font-size: 16px; z-index: 100; pointer-events: none; background: rgba(0,0,0,0.7); padding: 5px; }
    </style>
</head>
<body>
    <div id="status">Status: Initializing...</div>
    <canvas id="displayCanvas"></canvas>
    <script>
        const statusDiv = document.getElementById('status');
        const canvas = document.getElementById('displayCanvas');
        const ctx = canvas.getContext('2d');
        
        // Force WebSocket connection directly
        let socket;
        try {
            socket = io({
                transports: ['websocket', 'polling']
            });
        } catch(e) {
            statusDiv.innerText = "SocketIO Error: " + e.message;
        }

        let lastData = {
            mode: 'ring',
            color: '#FFFFFF',
            x: window.innerWidth / 2,
            y: window.innerHeight / 2,
            size: 60,
            count: 12,
            radius: Math.min(window.innerWidth, window.innerHeight) * 0.35,
            active_index: -1
        };

        function draw(data) {
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            if (data.mode === 'all') {
                ctx.fillStyle = data.color;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            } else if (data.mode === 'single') {
                ctx.fillStyle = data.color;
                ctx.beginPath();
                ctx.arc(data.x, data.y, data.size / 2, 0, 2 * Math.PI);
                ctx.fill();
            } else if (data.mode === 'ring') {
                const cx = data.x;
                const cy = data.y;
                const count = data.count;
                const radius = data.radius;
                const spotSize = data.size;

                for (let i = 0; i < count; i++) {
                    if (data.active_index !== -1 && i !== data.active_index) continue;
                    let angle = (i / count) * 2 * Math.PI;
                    let x = cx + radius * Math.cos(angle);
                    let y = cy + radius * Math.sin(angle);

                    ctx.fillStyle = data.color;
                    ctx.beginPath();
                    ctx.arc(x, y, spotSize / 2, 0, 2 * Math.PI);
                    ctx.fill();
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

        if (socket) {
            socket.on('connect', () => {
                statusDiv.innerText = "CONNECTED via WSS!";
                statusDiv.style.color = "#00ff00";
                socket.emit('client_info', { width: canvas.width, height: canvas.height, ppr: window.devicePixelRatio });
                setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
            });

            socket.on('connect_error', (err) => {
                statusDiv.innerText = "Connect Error: " + err.message;
                statusDiv.style.color = "#ff0000";
                statusDiv.style.display = 'block';
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
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    bridge.log_signal.emit("Phone connected over HTTPS!")

@socketio.on('client_info')
def handle_client_info(data):
    bridge.client_connected_signal.emit(data)
    bridge.log_signal.emit(f"Phone Screen Resolution: {data['width']}x{data['height']}")

def start_flask_http():
    bridge.log_signal.emit("Starting HTTP Server on port 5000...")
    # Standard HTTP - No cert.pem/key.pem required!
    socketio.run(app, host='0.0.0.0', port=5000, log_output=False)


# ==========================================
# 2. MACRO-ENABLED PYQT5 GUI
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Microscope OLED Interactive Macro Controller")
        self.setGeometry(100, 100, 900, 700)

        self.current_color = "#FFFFFF"
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.advance_flash_led)

        self.init_ui()

        bridge.log_signal.connect(self.log)
        bridge.client_connected_signal.connect(self.update_client_info)

        self.server_thread = threading.Thread(target=start_flask_http, daemon=True)
        self.server_thread.start()
        self.log("HTTP Server Started on http://192.168.1.12:5000")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_panel = QVBoxLayout()

        # Mode Selection
        mode_group = QGroupBox("Illumination Mode")
        mode_layout = QVBoxLayout()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Full Screen", "Single Spot / Pixel", "LED Ring Pattern"])
        self.combo_mode.setCurrentIndex(2)
        self.combo_mode.currentIndexChanged.connect(self.send_render_command)
        mode_layout.addWidget(self.combo_mode)
        mode_group.setLayout(mode_layout)
        left_panel.addWidget(mode_group)

        # Color
        color_group = QGroupBox("Color")
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("Select Color")
        self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black; font-weight: bold;")
        self.btn_color.clicked.connect(self.choose_color)
        color_layout.addWidget(self.btn_color)
        color_group.setLayout(color_layout)
        left_panel.addWidget(color_group)

        # Interactive Sliders
        slider_group = QGroupBox("Live Pattern & Position Sliders (Instant Update)")
        slider_layout = QVBoxLayout()

        # Position X
        slider_layout.addWidget(QLabel("Center X Position:"))
        self.slider_x = QSlider(Qt.Horizontal)
        self.slider_x.setRange(0, 2000)
        self.slider_x.setValue(500)
        self.slider_x.valueChanged.connect(self.send_render_command)
        slider_layout.addWidget(self.slider_x)

        # Position Y
        slider_layout.addWidget(QLabel("Center Y Position:"))
        self.slider_y = QSlider(Qt.Horizontal)
        self.slider_y.setRange(0, 3000)
        self.slider_y.setValue(1000)
        self.slider_y.valueChanged.connect(self.send_render_command)
        slider_layout.addWidget(self.slider_y)

        # Ring Radius
        slider_layout.addWidget(QLabel("Ring Radius (px):"))
        self.slider_radius = QSlider(Qt.Horizontal)
        self.slider_radius.setRange(10, 1200)
        self.slider_radius.setValue(350)
        self.slider_radius.valueChanged.connect(self.send_render_command)
        slider_layout.addWidget(self.slider_radius)

        # Spot Size
        slider_layout.addWidget(QLabel("Spot Size / Thickness (px):"))
        self.slider_size = QSlider(Qt.Horizontal)
        self.slider_size.setRange(2, 300)
        self.slider_size.setValue(60)
        self.slider_size.valueChanged.connect(self.send_render_command)
        slider_layout.addWidget(self.slider_size)

        # LED Count
        slider_layout.addWidget(QLabel("Ring LED Count:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(3, 64)
        self.spin_count.setValue(12)
        self.spin_count.valueChanged.connect(self.on_led_count_changed)
        slider_layout.addWidget(self.spin_count)

        # Manual Active LED Selection
        slider_layout.addWidget(QLabel("Active Single LED (-1 = All On):"))
        self.spin_active = QSpinBox()
        self.spin_active.setRange(-1, 63)
        self.spin_active.setValue(-1)
        self.spin_active.valueChanged.connect(self.send_render_command)
        slider_layout.addWidget(self.spin_active)

        slider_group.setLayout(slider_layout)
        left_panel.addWidget(slider_group)

        # Auto-Flash Sequencer
        flash_group = QGroupBox("One-by-One Flashing Macro (Automated Sequence)")
        flash_layout = QVBoxLayout()

        self.btn_flash_toggle = QPushButton("START FLASHING SEQUENCE")
        self.btn_flash_toggle.setCheckable(True)
        self.btn_flash_toggle.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px;")
        self.btn_flash_toggle.clicked.connect(self.toggle_flashing)
        flash_layout.addWidget(self.btn_flash_toggle)

        flash_layout.addWidget(QLabel("Flash Speed / Interval (ms):"))
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(20, 1000)
        self.slider_speed.setValue(200)
        self.slider_speed.valueChanged.connect(self.update_flash_speed)
        flash_layout.addWidget(self.slider_speed)

        flash_group.setLayout(flash_layout)
        left_panel.addWidget(flash_group)

        left_panel.addStretch()
        main_layout.addLayout(left_panel, stretch=6)

        # Right Log Panel
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("System Logs:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        right_panel.addWidget(self.txt_log)

        main_layout.addLayout(right_panel, stretch=4)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.btn_color.setStyleSheet(f"background-color: {self.current_color}; color: black;")
            self.send_render_command()

    def update_client_info(self, data):
        self.slider_x.setRange(0, data['width'])
        self.slider_y.setRange(0, data['height'])
        self.slider_x.setValue(data['width'] // 2)
        self.slider_y.setValue(data['height'] // 2)

    def on_led_count_changed(self, value):
        self.spin_active.setMaximum(value - 1)
        self.send_render_command()

    def toggle_flashing(self, checked):
        if checked:
            self.btn_flash_toggle.setText("STOP FLASHING")
            self.btn_flash_toggle.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 8px;")
            self.spin_active.setValue(0)
            self.flash_timer.start(self.slider_speed.value())
        else:
            self.btn_flash_toggle.setText("START FLASHING SEQUENCE")
            self.btn_flash_toggle.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 8px;")
            self.flash_timer.stop()
            self.spin_active.setValue(-1)
            self.send_render_command()

    def advance_flash_led(self):
        current = self.spin_active.value()
        count = self.spin_count.value()
        next_led = (current + 1) % count
        self.spin_active.setValue(next_led)

    def update_flash_speed(self, value):
        if self.flash_timer.isActive():
            self.flash_timer.setInterval(value)

    def send_render_command(self):
        mode_map = {0: 'all', 1: 'single', 2: 'ring'}
        selected_mode = mode_map[self.combo_mode.currentIndex()]

        payload = {
            'mode': selected_mode,
            'color': self.current_color,
            'x': self.slider_x.value(),
            'y': self.slider_y.value(),
            'size': self.slider_size.value(),
            'count': self.spin_count.value(),
            'radius': self.slider_radius.value(),
            'active_index': self.spin_active.value()
        }

        socketio.emit('render_state', payload)

    def log(self, msg):
        self.txt_log.append(msg)

if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app_qt.exec_())