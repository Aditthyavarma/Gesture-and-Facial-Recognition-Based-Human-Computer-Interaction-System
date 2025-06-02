import cv2
import mediapipe as mp
import pyautogui
import webbrowser
import numpy as np
import time
import psutil
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Disable PyAutoGUI fail-safe (WARNING: Use responsibly!)
pyautogui.FAILSAFE = False

def is_process_running(name):
    for proc in psutil.process_iter(['name']):
        try:
            if name.lower() in proc.info['name'].lower():
                return True
        except:
            pass
    return False

def calculate_ear(landmarks, eye_indices):
    p = [np.array([landmarks[i].x, landmarks[i].y]) for i in eye_indices]
    vertical1 = np.linalg.norm(p[1] - p[5])
    vertical2 = np.linalg.norm(p[2] - p[4])
    horizontal = np.linalg.norm(p[0] - p[3])
    return (vertical1 + vertical2) / (2.0 * horizontal + 1e-6)

def finger_extended(tip, pip):
    return tip.y < pip.y

def all_fingers_folded(hand_landmarks, mp_hands):
    folded = True
    fingers = [
        (mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.THUMB_IP),
        (mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_PIP),
        (mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
        (mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_PIP),
        (mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_PIP),
    ]
    for tip_idx, pip_idx in fingers:
        tip = hand_landmarks.landmark[tip_idx]
        pip = hand_landmarks.landmark[pip_idx]
        if finger_extended(tip, pip):
            folded = False
            break
    return folded

# Setup
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils
screen_w, screen_h = pyautogui.size()

prev_screen_x, prev_screen_y = screen_w // 2, screen_h // 2
blink_active, youtube_open, chatgpt_open = False, False, False
last_blink_click_time, last_scroll_time = 0, 0
blink_cooldown, scroll_debounce = 0.5, 0.3

# Audio volume setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_min, vol_max = volume.GetVolumeRange()[:2]

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_h, frame_w, _ = frame.shape

    face_results = face_mesh.process(rgb_frame)
    hand_results = hands.process(rgb_frame)

    if face_results.multi_face_landmarks:
        landmarks = face_results.multi_face_landmarks[0].landmark

        # Mouth open detection
        left_mouth, right_mouth = landmarks[61], landmarks[291]
        top_lip, bottom_lip = landmarks[13], landmarks[14]
        mouth_ratio = abs(right_mouth.x - left_mouth.x) / (abs(top_lip.y - bottom_lip.y) + 1e-6)
        cv2.putText(frame, f'Mouth Ratio: {mouth_ratio:.2f}', (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if mouth_ratio > 1.4 and abs(top_lip.y - bottom_lip.y) > 0.04 and not youtube_open:
            webbrowser.open('https://www.youtube.com')
            youtube_open = True
        elif mouth_ratio < 1.2 and youtube_open:
            youtube_open = is_process_running("chrome.exe")

        cv2.putText(frame, f'YouTube: {"Open" if youtube_open else "Closed"}', (10, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if youtube_open else (0, 255, 0), 2)

        # Eye tracking (iris)
        iris_landmark = landmarks[474]
        screen_x = int(screen_w * iris_landmark.x)
        screen_y = int(screen_h * iris_landmark.y)
        alpha = 0.8
        smooth_x = int(alpha * screen_x + (1 - alpha) * prev_screen_x)
        smooth_y = int(alpha * screen_y + (1 - alpha) * prev_screen_y)
        pyautogui.moveTo(smooth_x, smooth_y)
        prev_screen_x, prev_screen_y = smooth_x, smooth_y
        cx, cy = int(iris_landmark.x * frame_w), int(iris_landmark.y * frame_h)
        cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

        # Blink detection
        left_eye_indices = [33, 159, 158, 133, 153, 144]
        ear = calculate_ear(landmarks, left_eye_indices)
        cv2.putText(frame, f'EAR: {ear:.3f}', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        now = time.time()
        if ear < 0.25 and not blink_active and (now - last_blink_click_time) > blink_cooldown:
            pyautogui.click()
            blink_active = True
            last_blink_click_time = now
        elif ear >= 0.25:
            blink_active = False

    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            now = time.time()

            # Scroll/Arrow gesture
            if now - last_scroll_time > scroll_debounce:
                dy = index_tip.y - wrist.y
                dx = index_tip.x - wrist.x
                vertical_thresh, horizontal_thresh, scroll_speed = 0.4, 0.4, 300

                if dy < -vertical_thresh:
                    pyautogui.scroll(scroll_speed)
                    cv2.putText(frame, 'Scroll Up', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                elif dy > vertical_thresh:
                    pyautogui.scroll(-scroll_speed)
                    cv2.putText(frame, 'Scroll Down', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                elif dx < -horizontal_thresh:
                    pyautogui.press('left')
                    cv2.putText(frame, 'Left Arrow', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                elif dx > horizontal_thresh:
                    pyautogui.press('right')
                    cv2.putText(frame, 'Right Arrow', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                last_scroll_time = now

            # Punch = ChatGPT
            if all_fingers_folded(hand_landmarks, mp_hands):
                if not chatgpt_open:
                    webbrowser.open('https://chat.openai.com')
                    chatgpt_open = True
            elif chatgpt_open and not is_process_running("chrome.exe"):
                chatgpt_open = False

            cv2.putText(frame, f'ChatGPT: {"Open" if chatgpt_open else "Closed"}', (10, 190),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255) if chatgpt_open else (0, 255, 255), 2)

            # Volume control: index up, middle down
            index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
            middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
            if finger_extended(index_tip, index_pip) and not finger_extended(middle_tip, middle_pip):
                vol = np.interp(index_tip.y, [0, 1], [vol_max, vol_min])
                volume.SetMasterVolumeLevel(vol, None)
                cv2.putText(frame, 'Volume Control', (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Manual reset for both YouTube and ChatGPT
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        youtube_open = False
        chatgpt_open = False
        print("Restarted flags. You can reopen YouTube and ChatGPT.")

    # Automatic reset if browser is closed
    if youtube_open and not is_process_running("chrome.exe"):
        youtube_open = False
    if chatgpt_open and not is_process_running("chrome.exe"):
        chatgpt_open = False

    cv2.imshow('Eye & Gesture Control', frame)

cam.release()
cv2.destroyAllWindows()

//