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
Wcam, Hcam = 640, 480 # 1280, 720

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

def start (img):

    img = detector.findHands(img)

    # Find positions for both hands
    lmListRight = detector.findPosition(img, handType="Right")
    lmListLeft = detector.findPosition(img, handType="Left")

    # Default values
    xL1, yL1, xL2, yL2 = 0, 0, 0, 0
    lengthLeft = 9999  # large value = fingers apart (not pinched)

    if len(lmListRight) != 0 and len(lmListLeft) != 0:
        # Left Hand
        xL1 , yL1 = lmListLeft[4][1], lmListLeft[4][2]
        xL2, yL2 = lmListLeft[8][1], lmListLeft[8][2]
        lengthLeft = np.hypot(xL2 - xL1, yL2 - yL1)

    return img, lengthLeft, lmListRight, lmListLeft, xL1, yL1, xL2, yL2

# Webcam
cap = cv2.VideoCapture(0)

cap.set(3, Wcam)
cap.set(4, Hcam)

xL1, yL1, xR1, yR1, xL2, yL2, xR2, yR2 = 0, 0, 0, 0, 0, 0, 0, 0

#########################################################################################################################################

#                                    Volume control with both hands Module
vol = 0
volBar = 400
volPer = 0


#########################################################################################################################################

#                                           Hand Number Module

detected_fingersRightHandNum = [0, 1, 1, 1, 1]
folder_path_HandNum = r"F:\Github\AI_Virtual_Controller\Images\FingerNumberImage"
# Read images
myList = os.listdir(folder_path_HandNum)
overlaylistHandNum = []

for imPath in myList:

    imagePath = os.path.join(folder_path_HandNum, imPath)

    image = cv2.imread(imagePath)

    if image is not None:

        h, w, c = image.shape
        
        image = cv2.resize(image, (w // 2, h // 2))

        overlaylistHandNum.append(image)

tipIdsHandNum = [4, 8, 12, 16, 20]

totalFingersHandNum = 0

#########################################################################################################################################

#                                          Virtual Painter Module

detected_fingersRightPainter = [0, 1, 0, 0, 0]
# Folder path
folder_path_Painter = r"F:\Github\AI_Virtual_Controller\Images\HeaderVirtualPainter"

# Read images
myListPainter = os.listdir(folder_path_Painter)

overlaylistPainter = []

for imPath in myListPainter:

    imagePath = os.path.join(folder_path_Painter, imPath)

    image = cv2.imread(imagePath)

    if image is not None:

        # Resize all headers to fit screen width
        image = cv2.resize(image, (Wcam, 125 // 2))

        overlaylistPainter.append(image)

# First header
headerPainter = overlaylistPainter[0]

drawColorPainter = None

BrachThicknessPainter = 15
EraserThicknessPainter = 70

xpPainter, ypPainter = 0, 0

imgCanvasPainter = np.zeros((Hcam, Wcam, 3), np.uint8)


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
    if len(lmListRight) != 0:
        fingersRight = detector.fingersUp(handType="Right")
        #print(f"Right: {fingersRight}")

    # --- Left Hand ---
    if len(lmListLeft) != 0:
        fingersLeft = detector.fingersUp(handType="Left")
        #print(f"Left:  {fingersLeft}")


    if len(lmListRight) != 0 and len(lmListLeft) != 0:
        # Right Hand
        xR1, yR1 = lmListRight[4][1], lmListRight[4][2]
        xR2, yR2 = lmListRight[8][1], lmListRight[8][2]

        # Left Hand
        xL1, yL1 = lmListLeft[4][1], lmListLeft[4][2]
        xL2, yL2 = lmListLeft[8][1], lmListLeft[8][2]

        # Distance between fingers
        lengthRight = np.hypot(xR2 - xR1, yR2 - yR1)
        lengthLeft = np.hypot(xL2 - xL1, yL2 - yL1)

        #print("Left: ", int(lengthLeft), "Right: ", int(lengthRight))

        #########################################################################################################################################
        #Volume control with both hands Module
        if lengthLeft < 30 and lengthRight < 30:

            while lengthLeft < 30:

                success, img = cap.read()
                img = cv2.flip(img, 1)

                if not success:
                    break

                # Detect hands
                img, lengthLeft, lmListRight, lmListLeft, xL1, yL1, xL2, yL2 = start(img)

                if len(lmListRight) != 0 and len(lmListLeft) != 0:
                    # Right Hand                    
                    xR1, yR1 = lmListRight[4][1], lmListRight[4][2]
                    xR2, yR2 = lmListRight[8][1], lmListRight[8][2]

                    # Distance between fingers
                    lengthRight = np.hypot(xR2 - xR1, yR2 - yR1)

                    #draw Hand Volume Task for both hands
                    drawHandVolumeTask(img, xR1, yR1, xR2, yR2)
                    drawHandVolumeTask(img, xL1, yL1, xL2, yL2)

                    # Distance between fingers
                    lengthR = np.hypot(xR2 - xR1, yR2 - yR1)
                    

                    volume.SetMasterVolumeLevel(vol, None)

                    vol = np.interp(
                        lengthRight,
                        [20, 150],
                        [minVol, maxVol]
                    )

                    volBar = np.interp(lengthR, [20, 150], [400, 150])
                    volPer = np.interp(lengthR, [20, 150], [0, 100])

                    # Set system volume
                    volume.SetMasterVolumeLevel(vol, None)

                    # Green circle when fingers are closeq1q
                    if lengthR < 20:
                        cv2.circle(
                        img,
                        ((xR1 + xR2) // 2, (yR1 + yR2) // 2),
                        10,
                        (0, 255, 0),
                        cv2.FILLED
                    )
                    print("Left: ", int(lengthLeft), "Right: ", int(lengthRight), 'Volume: ', int(vol))


                    # Show distance
                    cv2.putText(
                        img,
                        f'Distance: {int(lengthR)}',
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

        #########################################################################################################################################
        #Hand Number Module
        elif lengthLeft < 30 and fingersRight == detected_fingersRightHandNum: 
            while lengthLeft < 30:

                success, img = cap.read()
                img = cv2.flip(img, 1)

                if not success:
                    break
                
                img, lengthLeft, lmListRight, lmListLeft, xL1, yL1, xL2, yL2 = start(img)

                if len(lmListRight) != 0:
                        Fingers = []

                        # Thumb
                        if lmListRight[tipIdsHandNum[0]][1] < lmListRight[tipIdsHandNum[0] - 1][1]:
                            Fingers.append(1)
                        else:
                            Fingers.append(0)
                
                        #  4 Fingers
                        for id in range(1, 5):
                            
                            if lmListRight[tipIdsHandNum[id]][2] < lmListRight[tipIdsHandNum[id] - 2][2]:

                                Fingers.append(1)
                            else:
                                Fingers.append(0)

                        totalFingersHandNum = Fingers.count(1)
                        print(totalFingersHandNum)

                        # Put overlay image
                if len(overlaylistHandNum) > 0 :
                    overlay = overlaylistHandNum[totalFingersHandNum ]
                    h, w, c = overlay.shape
                    frame_h, frame_w, _ = img.shape
                    img[0:h, frame_w - w:frame_w] = overlay
                        
                #pTime = FPS(img, pTime)                

                cv2.imshow("Image", img)                  
            
                # Quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        #########################################################################################################################################
        #Virtual Painter Module
        elif lengthLeft < 30 and fingersRight == detected_fingersRightPainter: 
            
            while lengthLeft < 30:

                success, img = cap.read()
                img = cv2.flip(img, 1)

                if not success:
                    break
                
                img, lengthLeft, lmListRight, lmListLeft, xL1, yL1, xL2, yL2 = start(img)
                if len(lmListRight) != 0:
                        

                        xR1,yR1 = lmListRight[8][1], lmListRight[8][2]
                        xR2,yR2 = lmListRight[12][1], lmListRight[12][2]

                        fingersRight = detector.fingersUp(handType="Right")

                        # Selection mode - Two fingers up
                        if fingersRight[1] and fingersRight[2]:

                            xpPainter, ypPainter = 0, 0

                            print("Selection Mode")
                            cv2.rectangle(
                                img,
                                (xR1, yR1 - 25),
                                (xR2, yR2 + 25),
                                drawColorPainter,
                                cv2.FILLED
                            )

                            headerPainter = overlaylistPainter[0]

                            if yR1 < 125 // 2:
                                if 200 // 2 < xR1 < 350 // 2:
                                    headerPainter = overlaylistPainter[1]
                                    drawColorPainter = (0, 0, 255)
                                elif 500 // 2 < xR1 < 650 // 2:
                                    headerPainter = overlaylistPainter[2]
                                    drawColorPainter=(255, 0, 0)

                                elif 800 // 2 < xR1 < 950 // 2:
                                    headerPainter = overlaylistPainter[3]
                                    drawColorPainter=(0, 255, 0)

                                elif 1050 // 2 < xR1 < 1200 // 2:  
                                    headerPainter = overlaylistPainter[4]
                                    drawColorPainter=(0, 0, 0)

                        if fingersRight[1] and not fingersRight[2]:
                            print("Drawing Mode")
                            cv2.circle(
                                img,
                                (xR1, yR1),
                                15,
                                drawColorPainter,
                                cv2.FILLED
                            )
                            if xpPainter == 0 and ypPainter == 0:
                                xpPainter, ypPainter = xR1, yR1

                            print("xR1:", xR1, "yR1:", yR1)

                            if drawColorPainter == (0, 0, 0):
                                
                                cv2.line(
                                img,
                                (xpPainter, ypPainter),
                                (xR1, yR1),
                                drawColorPainter,
                                EraserThicknessPainter
                                )

                                cv2.line(
                                    imgCanvasPainter,
                                    (xpPainter, ypPainter),
                                    (xR1, yR1),
                                    drawColorPainter,
                                    EraserThicknessPainter
                                )

                            else:
                            
                                cv2.line(
                                    img,
                                    (xpPainter, ypPainter),
                                    (xR1, yR1),
                                    drawColorPainter,
                                    BrachThicknessPainter
                                )
                                
                                cv2.line(
                                    imgCanvasPainter,
                                    (xpPainter, ypPainter),
                                    (xR1, yR1),
                                    drawColorPainter,
                                    BrachThicknessPainter
                                )

                            xpPainter, ypPainter = xR1, yR1

                    
                imgGray = cv2.cvtColor(imgCanvasPainter, cv2.COLOR_BGR2GRAY)
                _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
                imgInv = cv2.cvtColor(imgInv,cv2.COLOR_GRAY2BGR)
                img = cv2.bitwise_and(img,imgInv)
                img = cv2.bitwise_or(img,imgCanvasPainter)

                # Put header on top
                h_header, w_header = headerPainter.shape[:2]
                img[0:h_header, 0:w_header] = headerPainter



                cv2.imshow("Image", img)                  
            
                # Quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            

        elif lengthLeft > 1000:
            while lengthLeft < 30:

                success, img = cap.read()
                img = cv2.flip(img, 1)

                if not success:
                    break
                
                img, lengthLeft, lmListRight, lmListLeft, xL1, yL1, xL2, yL2 = start(img)

                print("Left: ", int(lengthLeft))

                cv2.imshow("Image", img)                  
            
                # Quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        else:
            pass
            #print("Left: ", int(lengthLeft), "Right: ", int(lengthRight))



    pTime = FPS(img, pTime)

    # Show image
    cv2.imshow("Image", img)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()