from main.models import Termocamera
import cv2, time
import numpy as np
from flask import current_app


pix_res = (32, 24)
interp_h = pix_res[1] * Termocamera.INTERP
interp_w = pix_res[0] * Termocamera.INTERP
interp_res = (interp_h, interp_w)

def fast_resize(img):
    return cv2.resize(img, (interp_w, interp_h), interpolation=cv2.INTER_CUBIC)

def interp_lanczos(z_var, scale=Termocamera.INTERP):
    z_var = cv2.GaussianBlur(z_var, (3, 3), 0)
    return cv2.resize(z_var, (z_var.shape[1]*scale, z_var.shape[0]*scale), interpolation=cv2.INTER_LANCZOS4)

def array_to_rgb(img, vmin=Termocamera.VMIN, vmax=Termocamera.VMAX):
    #norm = np.clip((img - np.min(img)) / (np.max(img) - np.min(img)), 0, 1) #dynamic
    norm = np.clip((img - vmin) / (vmax - vmin), 0, 1) #static
    norm = norm * 255
    color = cv2.applyColorMap(norm.astype(np.uint8), cv2.COLORMAP_JET)
    return color

def build_colorbar(height):
    bar = np.zeros((height, 20, 3), dtype=np.uint8)
    for i in range(256):
        color = cv2.applyColorMap(np.array([[255 - i]], dtype=np.uint8), cv2.COLORMAP_JET)[0][0]
        start = i * height // 256
        end = (i + 1) * height // 256
        bar[start:end, :, :] = color
    return bar

COLORBAR = build_colorbar(interp_h)


def build_text_overlay():
    overlay = np.zeros((interp_h, interp_w + 20, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.4
    thick = 1

    cv2.putText(overlay,
                f"{Termocamera.VMAX:.1f}C",
                (interp_w - 40, 12),
                font, scale, (255, 255, 255), thick, cv2.LINE_AA)

    cv2.putText(overlay,
                f"{Termocamera.VMIN:.1f}C",
                (interp_w - 40, interp_h - 5),
                font, scale, (255, 255, 255), thick, cv2.LINE_AA)

    return overlay

TEXT_OVERLAY = build_text_overlay()

def generate_frames(mlx90640_websocket):
    #camera = mlx90640_view(url) #for rest api

    while True:
        try:
            #t_max, pixels, timestamp = camera.update() #for rest api
            t_max, pixels, timestamp = mlx90640_websocket.update()
            frame = interp_lanczos(pixels)
            #frame = fast_resize(pixels)
            frame_rgb = array_to_rgb(frame)
            frame_rgb = np.hstack((frame_rgb, COLORBAR))
            frame_rgb = cv2.add(frame_rgb, TEXT_OVERLAY)


            _, buffer = cv2.imencode('.jpg', frame_rgb)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print("Error Generate Frames:", e)
            time.sleep(1)