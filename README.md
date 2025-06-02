# Eye Controlled Mouse with Hand and Face Gestures

This project allows you to control your mouse cursor, click, scroll, and trigger actions using your eyes, face, and hand gestures via your webcam. It uses Python, OpenCV, MediaPipe, and PyAutoGUI.

## Features
- **Move Mouse with Eyes:** Cursor follows your gaze.
- **Blink to Click:** Blink to perform a mouse click.
- **Hand Gestures for Scrolling:** Use your index finger position relative to your wrist to scroll vertically and horizontally.
- **Smile to Open YouTube:** Smile to automatically open YouTube in your browser.
- **Quit Anytime:** Press `q` to exit the application.

## Installation

1. **Clone the repository:**
   ```powershell
   git clone <your-repo-url>
   cd eye_controlled_mouse-main
   ```

2. **Install Python 3.11 (64-bit):**
   - Download from [python.org](https://www.python.org/downloads/release/python-3118/)
   - Add Python to PATH during installation.

3. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv311
   .\venv311\Scripts\Activate.ps1
   ```
   If you get a script execution error, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   .\venv311\Scripts\Activate.ps1
   ```

4. **Install required libraries:**
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**
   ```powershell
   python main.py
   ```

2. **Allow webcam access if prompted.**

3. **Controls:**
   - **Move mouse:** Move your eyes.
   - **Click:** Blink your eyes.
   - **Scroll:** Move your index finger up/down (vertical) or left/right (horizontal) relative to your wrist in view of the camera.
   - **Smile:** Smile to open YouTube.
   - **Quit:** Press `q`.

## Notes
- Works best in good lighting and with your face and hand clearly visible to the webcam.
- You can tune gesture sensitivity in `main.py` by adjusting the thresholds.

## Requirements
- Python 3.11 (64-bit)
- Webcam

## Libraries
- opencv-python
- mediapipe
- pyautogui

Install all with:
```powershell
pip install -r requirements.txt
```

---

Feel free to fork, modify, and contribute!
