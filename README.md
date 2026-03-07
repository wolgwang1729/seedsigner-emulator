# seedsigner-emulator

A standalone emulator for [SeedSigner](https://github.com/SeedSigner/seedsigner) that runs a GUI simulator for easy local development. You can interact with the buttons in the window or use keyboard controls: arrow keys, Enter, Numpad_1, Numpad_2, Numpad_3.

> **Note:** Only tested on macOS (26) using Homebrew and Python 3.14.

<img src="docs/img/simulator.png" width=320 />

---

## Prerequisites

- A desktop / laptop with webcam
- An existing clone of the [SeedSigner repository](https://github.com/SeedSigner/seedsigner)

---

## Installing System Dependencies

SeedSigner's simulator depends on Python with `tkinter` support, and native libraries for QR scanning and camera access.

- `tkinter` is Python's built-in library for creating desktop GUI applications.
- `pyzbar` requires a system library called `zbar`.

### macOS (Homebrew)

```bash
brew install python@3.14  # includes tkinter support
brew install zbar
```

### Linux

```bash
sudo apt-get install python3-tk
sudo apt install libzbar0
```

---

## Setting Up the Dev Environment

```bash
git clone https://github.com/SeedSigner/seedsigner-emulator

python3 -m venv env
source env/bin/activate

# Verify tkinter works (should open a small window)
python3 -m tkinter

pip install -r requirements.txt
```

---

## Camera Permissions (macOS)

On first run, macOS will block camera access. You may see logs like:

```
OpenCV: not authorized to capture video
OpenCV: camera failed to properly initialize
```

Go to **System Settings → Privacy & Security → Camera** and enable access for:

- **Terminal** (if running from Terminal)
- **VS Code** (if running from VS Code)

Then restart Terminal and rerun the emulator.

If macOS didn't prompt you, reset permissions manually:

```bash
tccutil reset Camera
```

---

## Running the Emulator

Pass the path to your SeedSigner repository (or its `src/` directory directly):

```bash
python run_emulator.py /path/to/seedsigner
# or
python run_emulator.py /path/to/seedsigner/src
```

---

## Notes

- The emulator environment is **not security-hardened** and should never be used with real funds.
- Camera access, QR decoding, and GUI rendering are platform-dependent; macOS behaviour differs from Raspberry Pi OS.
- For hardware deployment, follow the official Raspberry Pi OS instructions in the main SeedSigner README.

---

## Credits

- Original work inspired by [enteropositivo/seedsigner-emulator](https://github.com/enteropositivo/seedsigner-emulator), the first working emulator POC using Tkinter-based replacements for camera, buttons, and renderer.
- Further macOS support with local GPIO socket emulation from [ltcmweb/seedsigner](https://github.com/ltcmweb/seedsigner), building on @enteropositivo's work.
