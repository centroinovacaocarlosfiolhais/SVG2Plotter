# ✂ SVG2Plotter — Inkscape Extension

**Send to Plotter directly from Inkscape**  
_Extensions → Export → Send to SVG2Plotter_

> Developed by **David Marques** — *Vibe Coding with Claude.ai*  
> Centro de Inovação Carlos Fiolhais · CDI Portugal

---

## What is this?

An Inkscape extension that sends the current document to a running
**SVG2Plotter Network** server for cutting on the SK1350 (or any HPGL cutter).

No extra Python libraries needed — uses only Python stdlib (`urllib`, `json`).  
Works on Windows, macOS, and Linux.

```
Inkscape → Extensions → Export → Send to SVG2Plotter
              │
              │  HTTP (urllib — no extra deps)
              ▼
      SVG2Plotter Network          ← must be running on some machine
      http://<host>:7733
              │
              │  USB-Serial (HPGL)
              ▼
         SK1350 cutter
```

---

## Requirements

| | |
|---|---|
| Inkscape | 1.0 or newer |
| SVG2Plotter Network | Running on any machine on the LAN |
| Python deps | **None** — stdlib only |

**SVG2Plotter Network** must be running before you use the extension.  
Get it at: https://github.com/centroinovacaocarlosfiolhais/svg2plotter

---

## Installation

### Option 1 — Extensions Manager (recommended)

1. Open Inkscape
2. **Extensions → Manage Extensions...**
3. Click **Install from file...**
4. Select `svg2plotter-inkscape-extension.zip`
5. Restart Inkscape

The extension appears at **Extensions → Export → Send to SVG2Plotter**.

### Option 2 — Manual install

Copy both files to your Inkscape user extensions folder:

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\inkscape\extensions\` |
| Linux | `~/.config/inkscape/extensions/` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |

Files to copy:
```
svg2plotter_send.inx
svg2plotter_send.py
```

Restart Inkscape after copying.

---

## Usage

1. Draw or open your design in Inkscape
2. Make sure **SVG2Plotter Network** is running (on this PC or another on the LAN)
3. Go to **Extensions → Export → Send to SVG2Plotter**
4. Fill in the dialog:

| Field | Description |
|---|---|
| **Server IP or hostname** | IP of the machine running the server (e.g. `192.168.1.100` or `localhost`) |
| **Port** | Default `7733` |
| **Scale factor** | `1.0` = original size, `0.5` = half, `2.0` = double |
| **Mirror mode** | Check for glass/window application (cuts mirrored) |
| **Test connection only** | Verifies the server and cutter respond — does not cut |

5. Click **Apply**

The extension uploads the current SVG to the server and starts the cut job.  
Monitor progress in the browser interface: `http://<host>:7733`

---

## Workflow tip — CICF / multiple PCs

When switching computers:

1. Install the extension once via Extensions Manager (takes 30 seconds)
2. Set the server IP to the machine connected to the cutter
3. That's it — the cutter is shared across all PCs on the LAN

```
PC 1 (cutter connected) → runs SVG2Plotter Network server
PC 2, 3, 4...           → Inkscape + this extension → send jobs remotely
```

---

## Troubleshooting

**"Cannot reach SVG2Plotter Network"**  
→ Make sure `python server.py` is running on the host machine  
→ Check the IP address is correct  
→ On Windows, allow port 7733 through the firewall  

**"Connection test FAILED"**  
→ The server is running but the cutter is not responding  
→ Check the USB cable and the serial port selection in the server UI  

**Extension not appearing in the menu**  
→ Both `.inx` and `.py` files must be in the same extensions folder  
→ Restart Inkscape after installing  

---

## CLI mode (testing without Inkscape)

```bash
# Test connection
python svg2plotter_send.py myfile.svg --host 192.168.1.100 --test-only

# Send to cut
python svg2plotter_send.py myfile.svg --host 192.168.1.100 --scale 1.5

# Mirror mode
python svg2plotter_send.py myfile.svg --host localhost --mirror
```

---

## License

**© 2026 David Marques · Centro de Inovação Carlos Fiolhais · CDI Portugal**

[![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

Licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/).
