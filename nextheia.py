import json
import os
import sys
import threading
import time
import tkinter as tk
import urllib.request
from PIL import Image
import psutil

try:
  import pynvml

  NVML_AVAILABLE = True
except ImportError:
  NVML_AVAILABLE = False

CONFIG_FILE = "nextheia_config.json"
VERSION = "v1.1.1"

DEFAULT_CONFIG = {
    "position": "top_right",
    "custom_x": 100,
    "custom_y": 100,
    "opacity": 0.85,
    "metrics": {
        "cpu": True,
        "cpu_temp": True,
        "gpu": True,
        "gpu_temp": True,
        "vram": True,
        "tokens": True,
        "model": True,
        "context": True,
        "power": True,
        "io": True,
    },
}


def resource_path(relative_path):
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)


class nextheiaHUD:

  def __init__(self):
    self.config = self.load_config()

    self.root = tk.Tk()
    self.root.overrideredirect(True)
    self.root.attributes("-topmost", True)
    self.root.attributes("-alpha", self.config.get("opacity", 0.85))
    self.root.configure(bg="#0d1117")

    self.labels = {}
    self.create_widgets()

    self.dragging = False
    self.root.bind("<Button-1>", self.start_drag)
    self.root.bind("<B1-Motion>", self.do_drag)
    self.root.bind("<ButtonRelease-1>", self.stop_drag)

    self.running = True
    self.poll_thread = threading.Thread(target=self.data_poll_loop, daemon=True)
    self.poll_thread.start()

    self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
    self.tray_thread.start()

  def load_config(self):
    if os.path.exists(CONFIG_FILE):
      try:
        with open(CONFIG_FILE, "r") as f:
          cfg = json.load(f)
          for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
              cfg[k] = v
          return cfg
      except:
        pass
    return DEFAULT_CONFIG.copy()

  def save_config(self):
    with open(CONFIG_FILE, "w") as f:
      json.dump(self.config, f, indent=4)

  def create_widgets(self):
    header = tk.Label(
        self.root,
        text=f"◆ nextheia AI HUD ({VERSION})",
        fg="#00d2ff",
        bg="#0d1117",
        font=("Consolas", 9, "bold"),
    )
    header.pack(anchor="w", padx=8, pady=(4, 2))

    metric_keys = [
        ("cpu", "CPU: Lade..."),
        ("cpu_temp", "CPU Temp: N/A"),
        ("gpu", "GPU Auslastung: -"),
        ("gpu_temp", "GPU Temp: -"),
        ("vram", "VRAM: Lade..."),
        ("tokens", "Tokens/s: -"),
        ("model", "Modell: Inaktiv"),
        ("context", "Kontext: -"),
        ("power", "Power: -"),
        ("io", "Disk I/O: -"),
    ]

    for key, text in metric_keys:
      lbl = tk.Label(
          self.root,
          text=text,
          fg="#c9d1d9",
          bg="#0d1117",
          font=("Consolas", 8),
          anchor="w",
      )
      self.labels[key] = lbl
      if self.config["metrics"].get(key, True):
        lbl.pack(anchor="w", padx=10, pady=1)

    self.update_window_geometry()

  def update_metrics_visibility(self):
    for key, lbl in self.labels.items():
      if self.config["metrics"].get(key, True):
        if not lbl.winfo_ismapped():
          lbl.pack(anchor="w", padx=10, pady=1)
      else:
        if lbl.winfo_ismapped():
          lbl.pack_forget()
    self.update_window_geometry()

  def update_window_geometry(self):
    self.root.update_idletasks()
    w = 260
    h = self.root.winfo_reqheight()
    sw = self.root.winfo_screenwidth()
    sh = self.root.winfo_screenheight()

    pos = self.config["position"]
    padding = 20

    if pos == "top_left":
      x, y = padding, padding
    elif pos == "top_right":
      x, y = sw - w - padding, padding
    elif pos == "bottom_left":
      x, y = padding, sh - h - padding - 40
    elif pos == "bottom_right":
      x, y = sw - w - padding, sh - h - padding - 40
    elif pos == "top_center":
      x, y = (sw - w) // 2, padding
    elif pos == "bottom_center":
      x, y = (sw - w) // 2, sh - h - padding - 40
    else:
      x, y = self.config.get("custom_x", 100), self.config.get("custom_y", 100)

    self.root.geometry(f"{w}x{h}+{x}+{y}")

  def start_drag(self, event):
    if self.config["position"] == "custom":
      self.dragging = True
      self.dx = event.x
      self.dy = event.y

  def do_drag(self, event):
    if self.dragging:
      x = self.root.winfo_x() + event.x - self.dx
      y = self.root.winfo_y() + event.y - self.dy
      self.config["custom_x"] = x
      self.config["custom_y"] = y
      self.root.geometry(f"+{x}+{y}")

  def stop_drag(self, event):
    if self.dragging:
      self.dragging = False
      self.save_config()

  def data_poll_loop(self):
    if NVML_AVAILABLE:
      try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
      except:
        pass

    last_disk_io = psutil.disk_io_counters()

    while self.running:
      try:
        cpu_perc = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        # Robusterer CPU-Temperatur-Check für Windows
        cpu_temp_text = "N/A"
        try:
          temps = psutil.sensors_temperatures()
          if temps:
            for name, entries in temps.items():
              for entry in entries:
                if entry.current > 0:
                  cpu_temp_text = f"{entry.current:.1f} °C"
                  break
              if cpu_temp_text != "N/A":
                break
        except Exception:
          pass

        time.sleep(1)
        disk_io_curr = psutil.disk_io_counters()
        disk_read_kb = (
            (disk_io_curr.read_bytes - last_disk_io.read_bytes) / 1024
            if last_disk_io
            else 0
        )
        disk_write_kb = (
            (disk_io_curr.write_bytes - last_disk_io.write_bytes) / 1024
            if last_disk_io
            else 0
        )
        last_disk_io = disk_io_curr
        io_text = f"R: {disk_read_kb:.0f} | W: {disk_write_kb:.0f} KB/s"

        gpu_util = "-"
        gpu_temp_text = "-"
        vram_text = "-"
        power_text = "-"
        if NVML_AVAILABLE:
          try:
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            g_temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )
            gpu_util = f"{util.gpu}%"
            gpu_temp_text = f"{g_temp} °C"
            vram_used = mem_info.used / (1024**3)
            vram_total = mem_info.total / (1024**3)
            vram_text = f"{vram_used:.1f} / {vram_total:.1f} GB"
            power_text = f"{power:.1f} W"
          except:
            pass

        model_text = "Inaktiv"
        context_text = "Kontext: - / -"
        try:
          req = urllib.request.Request("http://localhost:11434/api/ps")
          with urllib.request.urlopen(req, timeout=0.8) as response:
            ollama_data = json.loads(response.read().decode())
            running_models = ollama_data.get("models", [])
            if running_models:
              m = running_models[0]
              name = m.get("name", "Unbekannt")
              details = m.get("details", {})
              quant = details.get("quantization_level", "")
              model_text = f"{name} ({quant})" if quant else name
              size_vram = m.get("size_vram", 0) / (1024**3)
              context_text = f"VRAM Modell: {size_vram:.1f} GB"
        except Exception:
          pass

        def refresh_ui():
          if "cpu" in self.labels:
            self.labels["cpu"].config(
                text=f"CPU: {cpu_perc}% | RAM: {mem.percent}%"
            )
          if "cpu_temp" in self.labels:
            self.labels["cpu_temp"].config(text=f"CPU Temp: {cpu_temp_text}")
          if "gpu" in self.labels:
            self.labels["gpu"].config(text=f"GPU Auslastung: {gpu_util}")
          if "gpu_temp" in self.labels:
            self.labels["gpu_temp"].config(text=f"GPU Temp: {gpu_temp_text}")
          if "vram" in self.labels:
            self.labels["vram"].config(text=f"VRAM: {vram_text}")
          if "power" in self.labels:
            self.labels["power"].config(text=f"Leistungsaufnahme: {power_text}")
          if "model" in self.labels:
            self.labels["model"].config(text=f"Modell: {model_text}")
          if "context" in self.labels:
            self.labels["context"].config(text=f"{context_text}")
          if "io" in self.labels:
            self.labels["io"].config(text=f"Disk I/O: {io_text}")

        self.root.after(0, refresh_ui)

      except Exception as e:
        print(f"Polling Fehler: {e}")

    if NVML_AVAILABLE:
      try:
        pynvml.nvmlShutdown()
      except:
        pass

  def setup_tray(self):
    import pystray
    from pystray import MenuItem as item

    icon_path = resource_path("Logo_N_nextfield_circle.ico")
    if os.path.exists(icon_path):
      icon_image = Image.open(icon_path)
    else:
      icon_image = Image.new("RGB", (64, 64), color=(0, 210, 255))

    def set_pos(pos_name):
      self.config["position"] = pos_name
      self.save_config()
      self.root.after(0, self.update_window_geometry)

    def set_opacity(val):
      self.config["opacity"] = val
      self.save_config()
      self.root.after(0, lambda: self.root.attributes("-alpha", val))

    def toggle_metric(metric_key):
      self.config["metrics"][metric_key] = not self.config["metrics"][
          metric_key
      ]
      self.save_config()
      self.root.after(0, self.update_metrics_visibility)

    menu = pystray.Menu(
        item(
            "Position",
            pystray.Menu(
                item(
                    "Oben Links",
                    lambda: set_pos("top_left"),
                    checked=lambda item: self.config["position"] == "top_left",
                ),
                item(
                    "Oben Rechts",
                    lambda: set_pos("top_right"),
                    checked=lambda item: self.config["position"] == "top_right",
                ),
                item(
                    "Oben Mitte",
                    lambda: set_pos("top_center"),
                    checked=lambda item: self.config["position"] == "top_center",
                ),
                item(
                    "Unten Links",
                    lambda: set_pos("bottom_left"),
                    checked=lambda item: self.config["position"]
                    == "bottom_left",
                ),
                item(
                    "Unten Rechts",
                    lambda: set_pos("bottom_right"),
                    checked=lambda item: self.config["position"]
                    == "bottom_right",
                ),
                item(
                    "Unten Mitte",
                    lambda: set_pos("bottom_center"),
                    checked=lambda item: self.config["position"]
                    == "bottom_center",
                ),
                item(
                    "Custom (Drag & Drop)",
                    lambda: set_pos("custom"),
                    checked=lambda item: self.config["position"] == "custom",
                ),
            ),
        ),
        item(
            "Transparenz (Opacity)",
            pystray.Menu(
                item(
                    "50% (Halbtransparent)",
                    lambda: set_opacity(0.5),
                    checked=lambda item: self.config.get("opacity", 0.85)
                    == 0.5,
                ),
                item(
                    "70% (Dezent)",
                    lambda: set_opacity(0.7),
                    checked=lambda item: self.config.get("opacity", 0.85)
                    == 0.7,
                ),
                item(
                    "85% (Standard)",
                    lambda: set_opacity(0.85),
                    checked=lambda item: self.config.get("opacity", 0.85)
                    == 0.85,
                ),
                item(
                    "100% (Vollständig deckend)",
                    lambda: set_opacity(1.0),
                    checked=lambda item: self.config.get("opacity", 1.0) == 1.0,
                ),
            ),
        ),
        item(
            "Metriken anzeigen",
            pystray.Menu(
                item(
                    "CPU & RAM",
                    lambda: toggle_metric("cpu"),
                    checked=lambda item: self.config["metrics"]["cpu"],
                ),
                item(
                    "CPU Temperatur (°C)",
                    lambda: toggle_metric("cpu_temp"),
                    checked=lambda item: self.config["metrics"]["cpu_temp"],
                ),
                item(
                    "GPU Auslastung",
                    lambda: toggle_metric("gpu"),
                    checked=lambda item: self.config["metrics"]["gpu"],
                ),
                item(
                    "GPU Temperatur (°C)",
                    lambda: toggle_metric("gpu_temp"),
                    checked=lambda item: self.config["metrics"]["gpu_temp"],
                ),
                item(
                    "VRAM & Temp",
                    lambda: toggle_metric("vram"),
                    checked=lambda item: self.config["metrics"]["vram"],
                ),
                item(
                    "Token-Geschwindigkeit",
                    lambda: toggle_metric("tokens"),
                    checked=lambda item: self.config["metrics"]["tokens"],
                ),
                item(
                    "Modell & Quantisierung",
                    lambda: toggle_metric("model"),
                    checked=lambda item: self.config["metrics"]["model"],
                ),
                item(
                    "Kontextfenster",
                    lambda: toggle_metric("context"),
                    checked=lambda item: self.config["metrics"]["context"],
                ),
                item(
                    "Leistungsaufnahme (W)",
                    lambda: toggle_metric("power"),
                    checked=lambda item: self.config["metrics"]["power"],
                ),
                item(
                    "RAM & Disk I/O",
                    lambda: toggle_metric("io"),
                    checked=lambda item: self.config["metrics"]["io"],
                ),
            ),
        ),
        pystray.Menu.SEPARATOR,
        item("Beenden", self.quit_app),
    )

    self.tray_icon = pystray.Icon(
        "nextheia", icon_image, f"nextheia AI HUD ({VERSION})", menu
    )
    self.setup_complete = True
    self.tray_icon.run()

  def quit_app(self, icon, item):
    self.running = False
    icon.stop()
    self.root.after(0, self.root.destroy)

  def run(self):
    self.root.mainloop()


if __name__ == "__main__":
  app = nextheiaHUD()
  app.run()