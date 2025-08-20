# Automated Tray Sorting System

## Overview

This project automates object sorting in a tray using a robot (slider + arm) and a camera, controlled by Python and Arduino. The system automatically detects occupied tray cells, selects a target cell, scans a QR code to identify the tray, and communicates with the Arduino for coordinated sorting and logging.

## Features

- **Automated cell detection:** Uses computer vision to identify which tray cells contain objects.
- **Random cell selection:** Randomly selects a detected cell for the next operation.
- **QR tray identification:** Scans QR codes within a configurable crop region to identify the tray.
- **Arduino communication:** Sends detected cell and tray info to Arduino via serial.
- **Robust workflow:** Falls back to default values if cell or QR code is not detected.
- **Logging:** Keeps track of tray usage and operations.

## File Structure

```
.
├── automated_cell_selection.py
├── automated_tray_sorting.py
├── main_controller.py
├── tray_counts.txt
├── crop_box.json
├── tray_cells.json
├── background.jpg
└── README.md
```

- **automated_cell_selection.py**  
  Detects object cells in the tray and randomly selects one.

- **automated_tray_sorting.py**  
  Scans for a tray QR code in a configurable region; defaults to `"b4"` if not found in 5 seconds.

- **main_controller.py**  
  Orchestrates workflow, communicates with Arduino, logs counts.

- **tray_counts.txt**  
  Logs tray operation counts.

- **crop_box.json**  
  Configures the crop area for QR code scanning.

- **tray_cells.json**  
  Configures tray cell locations for object detection.

- **background.jpg**  
  Reference image of empty tray for object detection.

## Quick Start

### Prerequisites

- Python 3.x
- Arduino with serial communication
- Camera connected to the system
- Python packages: `opencv-python`, `pyzbar`, `numpy`, `pyserial`

Install dependencies:

```bash
pip install opencv-python pyzbar numpy pyserial
```

### Hardware Setup

- Set up your tray and position objects as required.
- Ensure your camera index (e.g., `camera_index = 2`) matches your hardware.
- Connect Arduino via USB.

### Configuration

- **crop_box.json**  
  Configure the crop region for QR scanning:
  ```json
  {
    "x": 250,
    "y": 200,
    "width": 250,
    "height": 250
  }
  ```

- **tray_cells.json**  
  Define each cell's location:
  ```json
  [
    {"label": "A", "x": 10, "y": 20, "w": 50, "h": 50},
    {"label": "B", "x": 70, "y": 20, "w": 50, "h": 50},
    ...
  ]
  ```

- **background.jpg**  
  Capture an image of the empty tray for background subtraction.

### Running the System

1. **Start Arduino** with your control sketch.
2. **Run main_controller.py**:
   ```bash
   python main_controller.py
   ```
   The system will:
   - Wait for Arduino prompts,
   - Automatically detect and select a cell,
   - Scan QR code for tray identification,
   - Send info to Arduino and log results.

### Workflow Summary

1. Arduino prompts for cell/arm input.
2. Python detects occupied tray cells and randomly selects one.
3. Python randomly selects an arm action.
4. Python sends cell and arm info to Arduino.
5. Arduino requests tray code.
6. Python scans for QR code (5s timeout, else defaults to `"b4"`).
7. Python sends tray code to Arduino.
8. Arduino completes action; Python logs counts.

## Customization

- Adjust cell and crop regions via JSON files.
- Update camera index and serial port as needed in `main_controller.py`.
- Tweak detection parameters in `automated_cell_selection.py` for your objects/tray.

## Troubleshooting

- **Camera issues:** Ensure correct camera index and that OpenCV can access your camera.
- **Serial issues:** Make sure the serial port matches your hardware and is not busy.
- **Detection issues:** Update cell and crop boxes for accurate detection.
- **No QR detected:** Check lighting, focus, and crop region.

## License

MIT License

## Authors

- Nisith Moragoda (https://github.com/n1s1th)

## Acknowledgements

- OpenCV, Pyzbar, NumPy, PySerial communities
- Arduino project inspiration
