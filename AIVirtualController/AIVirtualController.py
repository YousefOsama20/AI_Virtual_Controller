import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import cv2
import time
import numpy as np
import autopy
from Lib import library

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
from pycaw.api.endpointvolume import IAudioEndpointVolume

# Camera size
Wcam, Hcam = 640, 480

# Hand detector (detects up to 2 hands)
detector = library.HandDetector()

# Audio setup
devices = AudioUtilities.GetSpeakers()

interface = devices.Activate(
    IAudioEndpointVolume._iid_,
    CLSCTX_ALL,
    None
)

volume = cast(
    interface,
    POINTER(IAudioEndpointVolume)
)


volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]


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

def drawHandVolumeTask(img, x1, y1, x2, y2):
    # Get center point
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    # Draw circles
    cv2.circle(img, (x1, y1), 10,
               (255, 0, 0), cv2.FILLED)
    cv2.circle(img, (x2, y2), 10,
                (255, 0, 0), cv2.FILLED)
    # Draw line
    cv2.line(img, (x1, y1), (x2, y2),
                (255, 0, 255), 3)
    # Draw center point
    cv2.circle(img, (cx, cy), 10,
                (255, 0, 0), cv2.FILLED)

# Webcam
cap = cv2.VideoCapture(0)

cap.set(3, Wcam)
cap.set(4, Hcam)
#########################################################################################################################################
vol = 0
volBar = 400
volPer = 0
#########################################################################################################################################

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
    ''''if len(lmListRight) != 0:
        fingersRight = detector.fingersUp(handType="Right")
        print(f"Right: {fingersRight}")

    # --- Left Hand ---
    if len(lmListLeft) != 0:
        fingersLeft = detector.fingersUp(handType="Left")
        print(f"Left:  {fingersLeft}")'''


    if len(lmListRight) != 0 and len(lmListLeft) != 0:
        # Left Hand
        x1, y1 = lmListRight[4][1], lmListRight[4][2]
        x2, y2 = lmListRight[8][1], lmListRight[8][2]

        # Right Hand
        x3, y3 = lmListLeft[4][1], lmListLeft[4][2]
        x4, y4 = lmListLeft[8][1], lmListLeft[8][2]

        # Distance between fingers
        lengthRight = np.hypot(x2 - x1, y2 - y1)
        lengthLeft = np.hypot(x4 - x3, y4 - y3)

        #print("Left: ", int(lengthLeft), "Right: ", int(lengthRight))


        if lengthLeft < 25 and lengthRight < 25:

            while lengthLeft < 25:
                

                success, img = cap.read()
                img = cv2.flip(img, 1)

                if not success:
                    break
                
                # Detect hands
                img = detector.findHands(img)

                # Find positions for both hands
                lmListRight = detector.findPosition(img, handType="Right")
                lmListLeft = detector.findPosition(img, handType="Left")

                if len(lmListRight) != 0 and len(lmListLeft) != 0:
                    # Left Hand
                    x1, y1 = lmListRight[4][1], lmListRight[4][2]
                    x2, y2 = lmListRight[8][1], lmListRight[8][2]

                    # Right Hand
                    x3, y3 = lmListLeft[4][1], lmListLeft[4][2]
                    x4, y4 = lmListLeft[8][1], lmListLeft[8][2]

                    # Distance between fingers
                    lengthRight = np.hypot(x2 - x1, y2 - y1)
                    lengthLeft = np.hypot(x4 - x3, y4 - y3)

                    #draw Hand Volume Task for both hands
                    drawHandVolumeTask(img, x1, y1, x2, y2)
                    drawHandVolumeTask(img, x3, y3, x4, y4)

                    # Distance between fingers
                    length = np.hypot(x2 - x1, y2 - y1)

                    volume.SetMasterVolumeLevel(vol, None)

                    vol = np.interp(
                        lengthLeft,
                        [20, 150],
                        [minVol, maxVol]
                    )

                    volBar = np.interp(length, [20, 150], [400, 150])
                    volPer = np.interp(length, [20, 150], [0, 100])

                    # Set system volume
                    volume.SetMasterVolumeLevel(vol, None)

                    # Green circle when fingers are closeq1q
                    if length < 20:
                        cv2.circle(
                        img,
                        ((x1 + x2) // 2, (y1 + y2) // 2),
                        10,
                        (0, 255, 0),
                        cv2.FILLED
                    )
                    print("Left: ", int(lengthLeft), "Right: ", int(lengthRight), 'Volume: ', int(vol))


                    # Show distance
                    cv2.putText(
                        img,
                        f'Distance: {int(length)}',
                        (10, 120),
                        cv2.FONT_HERSHEY_PLAIN,
                        2,
                        (0, 255, 0),
                        2
                    )
                    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
                    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED) 
                    cv2.putText(img, f'{int(volPer)} %', (40, 450),
                                cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)

                    # Update image and wait
                    #pTime = FPS(img, pTime)
                    cv2.imshow("Image", img)
                    
                    # Quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        else:
            print("Left: ", int(lengthLeft), "Right: ", int(lengthRight))


    pTime = FPS(img, pTime)

    # Show image
    cv2.imshow("Image", img)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()