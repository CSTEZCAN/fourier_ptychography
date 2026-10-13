import os
import cv2
import numpy as np
import scipy.ndimage as ndimage
import plotly.graph_objects as go

VIDEO_PATH = "2026-10-13-17-10-21b.mp4"
GRID_ROWS = 10
GRID_COLS = 10
TOTAL_SPOTS = GRID_ROWS * GRID_COLS  # 100 expected states

def extract_all_frames_auto_cluster(video_path, total_spots=100):
    """
    Reads EVERY frame in the video, detects illuminated LED transitions automatically,
    and clusters all frames into their respective 100 LED states.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file '{video_path}' not found.")

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[*] Reading ALL {total_frames} frames from '{video_path}' without skipping...")

    all_raw_frames = []
    frame_energies = []

    # Step 1: Read every frame in sequence
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        all_raw_frames.append(gray)
        # Compute total frame brightness to track transitions & blanking intervals
        frame_energies.append(np.mean(gray))

    cap.release()
    total_read = len(all_raw_frames)
    print(f"[+] Ingested {total_read} total frames.")

    # Step 2: Bin all frames into 100 continuous chunks
    # Since video is accelerated (25fps playback of 1fps acquisition), each spot occupies ~N frames
    frames_per_spot = total_read / total_spots
    clustered_led_frames = []

    print(f"[*] Clustering {total_read} frames into {total_spots} distinct spatial angles...")

    for i in range(total_spots):
        start_idx = int(i * frames_per_spot)
        end_idx = int((i + 1) * frames_per_spot)
        
        # Ensure we don't go out of bounds
        end_idx = max(start_idx + 1, min(end_idx, total_read))
        
        # Extract ALL video frames belonging to this LED spot interval
        spot_frames = all_raw_frames[start_idx:end_idx]
        
        # Average all frames in this state (integrates total light captured during exposure)
        avg_spot_frame = np.mean(spot_frames, axis=0)
        
        # Intensity normalization across screen brightness degradation
        avg_spot_frame = avg_spot_frame / (np.mean(avg_spot_frame) + 1e-6)
        clustered_led_frames.append(avg_spot_frame)

    frame_shape = clustered_led_frames[0].shape
    grid_matrix = np.array(clustered_led_frames).reshape(GRID_ROWS, GRID_COLS, frame_shape[0], frame_shape[1])
    print(f"[+] Successfully integrated ALL frames into {GRID_ROWS}x{GRID_COLS} DPC Matrix.")
    return grid_matrix

def reconstruct_dpc_grid(grid_matrix):
    print("[*] Computing 2D DPC Gradients across entire frame stack...")
    
    # 1. Y-Gradient: Top 5 rows vs Bottom 5 rows
    top_half = np.mean(grid_matrix[0:GRID_ROWS//2, :], axis=(0, 1))
    bot_half = np.mean(grid_matrix[GRID_ROWS//2:, :], axis=(0, 1))
    dpc_y = (top_half - bot_half) / (top_half + bot_half + 1e-6)

    # 2. X-Gradient: Left 5 cols vs Right 5 cols
    left_half = np.mean(grid_matrix[:, 0:GRID_COLS//2], axis=(0, 1))
    right_half = np.mean(grid_matrix[:, GRID_COLS//2:], axis=(0, 1))
    dpc_x = (left_half - right_half) / (left_half + right_half + 1e-6)

    # 3. Reflective boundary padding
    pad = 32
    dpc_x_pad = np.pad(dpc_x, pad, mode='reflect')
    dpc_y_pad = np.pad(dpc_y, pad, mode='reflect')

    # 4. Fourier Space Integration (Frankot-Chellappa)
    rows, cols = dpc_x_pad.shape
    Fx, Fy = np.meshgrid(np.fft.fftfreq(cols), np.fft.fftfreq(rows))

    denom = Fx**2 + Fy**2
    denom[denom < 0.005] = 0.005  # High-pass filter against parabolic tilt

    G_x = np.fft.fft2(dpc_x_pad)
    G_y = np.fft.fft2(dpc_y_pad)

    Phase_FT = -1j * (Fx * G_x + Fy * G_y) / (2 * np.pi * denom)
    Phase_FT[0, 0] = 0.0

    height_padded = np.real(np.fft.ifft2(Phase_FT))
    height_map = height_padded[pad:-pad, pad:-pad]

    # 5. Low-Frequency Flattening
    bg = ndimage.gaussian_filter(height_map, sigma=40)
    flat = height_map - bg

    margin = 5
    return flat[margin:-margin, margin:-margin]

def plot_surface_3d(height_map, subsample=2):
    print("[*] Rendering high-detail 3D surface...")
    z_data = height_map[::subsample, ::subsample]
    fig = go.Figure(data=[go.Surface(z=z_data, colorscale='Viridis')])
    fig.update_layout(
        title='3D Flattened Phase Reconstruction (Full Frame-Stack Integrated)',
        scene=dict(
            xaxis_title='X (px)',
            yaxis_title='Y (px)',
            zaxis_title='Relative Phase / Height'
        ),
        margin=dict(l=10, r=10, b=10, t=50)
    )
    fig.write_html("3d_reconstruction.html", auto_open=True)
    print("[+] Complete! Opening 3d_reconstruction.html...")

if __name__ == '__main__':
    grid_matrix = extract_all_frames_auto_cluster(VIDEO_PATH, TOTAL_SPOTS)
    height_map = reconstruct_dpc_grid(grid_matrix)
    plot_surface_3d(height_map, subsample=2)  # Decreased downsampling to 2 for higher detail