# <img src="Logo_N_nextfield_circle.ico" width="130" style="vertical-align: middle; margin-right: 8px;">

# 🅝 nextheia (v1.1.1)

Ein leichtgewichtiger, rahmenloser Windows 11 System-Monitor als System-Tray-App mit HUD-Overlay. Speziell entwickelt für die Überwachung von Hardware-Ressourcen und lokalen KI-Prozessen (Ollama).

---

## 🚀 Features (v1.1.1)
* **HUD-Overlay:** Immer im Vordergrund, transparent und rahmenlos.
* **Live-Metriken:** CPU-Auslastung & RAM, CPU-Temperatur, GPU-Auslastung & VRAM (NVIDIA via NVML), Leistungsaufnahme (W), Disk I/O (Read/Write in KB/s).
* **Ollama Integration:** Zeigt aktive lokale KI-Modelle, Quantisierung und VRAM-Belegung in Echtzeit über die Ollama REST-API (`http://localhost:11434`).
* **System-Tray Steuerung:** Vollständig über das Taskleisten-Icon steuerbar (mit offiziellem *nextfield*-Logo).
* **Positionierung & Transparenz:** 6 feste Bildschirm-Presets + Custom Drag & Drop sowie stufenlose Transparenz-Regelung (50% bis 100%) direkt im Tray-Menü.
* **Persistente Einstellungen:** Alle Präferenzen werden automatisch in der `nextheia_config.json` gespeichert.

---

## 🚀 Download-Counter
<div align="left">

[![GitHub All Releases Download-Anzahl](https://img.shields.io/github/downloads/nextfield/nextheia/total?style=flat-square&logo=github&color=00d2ff)](https://github.com/nextfield/nextheia/releases)
[![GitHub Release (latest by date)](https://img.shields.io/github/v/release/nextfield/nextheia?style=flat-square&color=2ea043)](https://github.com/nextfield/nextheia/releases/latest)

*Entwickelt als Teil der **nextfield**-Infrastruktur.*

</div

## 🛠️ Tech Stack
* **Python 3.14** mit `tkinter` für das Overlay.
* **`pystray` & `Pillow`** für das System-Tray-Menü und Icon-Handling.
* **`psutil` & `pynvml`** für die Hardware- und Sensor-Abfragen.

---

## 📦 Verwendung & Build
Das Tool kann direkt aus dem Quellcode gestartet oder mittels PyInstaller als portable `.exe` kompiliert werden:

```bash
pyinstaller --noconsole --onefile --clean --icon=Logo_N_nextfield_circle.ico --add-data "Logo_N_nextfield_circle.ico;." nextheia.py

