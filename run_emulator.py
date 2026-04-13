import sys
import os
import signal
import time
import argparse
import multiprocessing
from unittest.mock import Mock, patch
import numpy as np

# Add the emulator directory to sys.path to enable imports
emulator_dir = os.path.dirname(os.path.abspath(__file__))
if emulator_dir not in sys.path:
    sys.path.insert(0, emulator_dir)


class MockST7789:
    def __init__(self, width=240, height=240, _width=None, _height=None):
        self.width = _width if _width is not None else width
        self.height = _height if _height is not None else height

    def show_image(self, image, x=0, y=0):
        with open("display.bmp", "wb") as f:
            f.write(image.tobytes())

    def invert(self, enabled: bool = True):
        pass


class MockVideoStream:
    def __init__(self):
        self.frame = np.random.randint(0, 255, (240, 240, 3), dtype=np.uint8)

    def start(self):
        pass

    def read(self):
        return self.frame

    def stop(self):
        pass


MOCK_PATCHES = [
    ("seedsigner.hardware.displays.ST7789.ST7789", MockST7789),
    ("seedsigner.hardware.displays.st7789_mpy.ST7789", MockST7789),
    ("seedsigner.extras.local_display.ST7789", MockST7789),
    ("seedsigner.hardware.pivideostream.PiVideoStream", MockVideoStream),
    ("seedsigner.hardware.camera.Camera", None),  # filled after import
]


def add_seedsigner_path(seedsigner_path):
    """Add the seedsigner src directory to sys.path."""
    src_path = os.path.join(seedsigner_path, "src")
    if os.path.isdir(src_path):
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
    else:
        if seedsigner_path not in sys.path:
            sys.path.insert(0, seedsigner_path)


def setup_mocks(seedsigner_path):
    """Apply all mock patches"""
    add_seedsigner_path(seedsigner_path)

    from patches.camera import MockCamera
    from patches.gpio import MockGPIO

    # Mock the entire picamera module before anything imports it
    picamera_mock = Mock()
    picamera_mock.array = Mock()
    sys.modules["picamera"] = Mock()
    sys.modules["picamera.array"] = picamera_mock.array

    # Mock the RPi module and its components
    rpi_mock = Mock()
    rpi_mock.GPIO = MockGPIO()
    sys.modules["RPi"] = rpi_mock
    sys.modules["RPi.GPIO"] = rpi_mock.GPIO

    # Mock spidev module
    spidev_mock = Mock()
    spidev_mock.SpiDev = Mock()
    sys.modules["spidev"] = spidev_mock

    # Intercept os.execv to prevent nested processes on restart
    def mock_execv(*args, **kwargs):
        # os._exit bypasses exception handlers and terminates the subprocess immediately
        os._exit(42)
    
    patch("os.execv", side_effect=mock_execv).start()

    patches_to_apply = MOCK_PATCHES[:-1] + [
        ("seedsigner.hardware.camera.Camera", MockCamera)
    ]

    for module_path, mock_obj in patches_to_apply:
        try:
            patcher = patch(module_path, mock_obj)
            patcher.start()
        except (ImportError, AttributeError):
            continue


def run_gui(seedsigner_path):
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    setup_mocks(seedsigner_path)

    from patches.window import Window
    from seedsigner.hardware.buttons import HardwareButtons

    Window(HardwareButtons)


def run_main(seedsigner_path):
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Safely overwrite sys.argv within this subprocess. 
    # This prevents SeedSigner's parser from crashing on the emulator's "/path" argument.
    sys.argv = ["main.py"]

    setup_mocks(seedsigner_path)

    from main import main

    # Give GUI a moment to start up and create socket
    time.sleep(0.5)
    main()


def signal_handler(sig, frame):
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="SeedSigner emulator - runs against an existing seedsigner repository"
    )
    parser.add_argument(
        "path",
        help="Path to the seedsigner repository (must contain src/ or be the src/ directory itself)",
    )
    args = parser.parse_args()

    seedsigner_path = os.path.abspath(args.path)
    if not os.path.isdir(seedsigner_path):
        print(f"Error: path does not exist or is not a directory: {seedsigner_path}")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    print("Starting GUI simulator...")
    # Daemonizing the GUI ensures the OS cleans it up automatically if the parent crashes
    gui_process = multiprocessing.Process(
        target=run_gui, args=(seedsigner_path,), name="GUI", daemon=True
    )
    gui_process.start()

    try:
        while True:
            main_process = multiprocessing.Process(
                target=run_main, args=(seedsigner_path,), name="Main"
            )
            print("Starting SeedSigner main application...")
            main_process.start()

            while main_process.is_alive():
                # If the user closes the Pygame window, exit the whole emulator
                if not gui_process.is_alive():
                    print("GUI closed. Shutting down...")
                    main_process.terminate()
                    break
                try:
                    main_process.join(timeout=0.1)
                except KeyboardInterrupt:
                    break

            # If the process exited with our special code 42, a restart was requested.
            if main_process.exitcode == 42:
                print("\n[Emulator] Reboot requested. Restarting application...\n")
                continue  # Loop again and spawn a fresh main_process
            else:
                break     # Normal exit or user quit

    except KeyboardInterrupt:
        pass
    finally:
        # Robust cleanup
        if 'main_process' in locals() and main_process.is_alive():
            main_process.terminate()
            main_process.join(timeout=2)
            if main_process.is_alive():
                main_process.kill()

        if gui_process.is_alive():
            gui_process.terminate()
            gui_process.join(timeout=2)
            if gui_process.is_alive():
                gui_process.kill()


if __name__ == "__main__":
    main()
