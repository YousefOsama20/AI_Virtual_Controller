import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import cv2
import time
import numpy as np
import autopy
from Lib import library
# Camera size
Wcam, Hcam = 640, 480

# Hand detector (detects up to 2 hands)
detector = library.HandDetector()

# FPS variable
pTime = 0


def FPS(img, pTime=0):

    cTime = time.time()

    fps = 1 / (cTime - pTime) if pTime != 0 else 0

    cv2.putText(
        img,
        f'FPS: {int(fps)}',
        (10, 70),
        cv2.FONT_HERSHEY_PLAIN,
        3,
        (255, 0, 255),
        3
    )

    return cTime


# Webcam
cap = cv2.VideoCapture(0)

cap.set(3, Wcam)
cap.set(4, Hcam)


while True:

    success, img = cap.read()
    img = cv2.flip(img, 1)

    if not success:
        break

    # Detect hands
    img = detector.findHands(img)

    # Find positions for both hands
    lmListRight = detector.findPosition(img, handType="Right")
    lmListLeft = detector.findPosition(img, handType="Left")

    # Get which hands are currently detected
    detectedHands = detector.getDetectedHands()

    # --- Right Hand ---
    if len(lmListRight) != 0:
        x1, y1 = lmListRight[8][1], lmListRight[8][2]
        x2, y2 = lmListRight[12][1], lmListRight[12][2]

        fingersRight = detector.fingersUp(handType="Right")
        print(f"Right: {fingersRight}")

    # --- Left Hand ---
    if len(lmListLeft) != 0:
        x1, y1 = lmListLeft[8][1], lmListLeft[8][2]
        x2, y2 = lmListLeft[12][1], lmListLeft[12][2]

        fingersLeft = detector.fingersUp(handType="Left")
        print(f"Left:  {fingersLeft}")

    pTime = FPS(img, pTime)

    # Show image
    cv2.imshow("Image", img)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()