import cv2
import mediapipe as mp
import time


class HandDetector():

    def __init__(self, mode=False, maxHands=2,
                 detectionCon=0.7, trackCon=0.7):

        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands

        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )

        self.mpDraw = mp.solutions.drawing_utils

        # Fingertips IDs
        self.tipIds = [4, 8, 12, 16, 20]

        # Landmark list
        self.lmList = []

    def findHands(self, img, draw=True):

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:

            for handLms in self.results.multi_hand_landmarks:

                if draw:
                    self.mpDraw.draw_landmarks(
                        img,
                        handLms,
                        self.mpHands.HAND_CONNECTIONS
                    )

        return img

    def findPosition(self, img, handNo=0,
                     draw=True,
                     PointId=None,
                     pointprintid=None,
                     pointprint=False):

        # IMPORTANT: save into self.lmList
        self.lmList = []

        if self.results.multi_hand_landmarks:

            myHand = self.results.multi_hand_landmarks[handNo]

            for id, lm in enumerate(myHand.landmark):

                h, w, c = img.shape

                cx = int(lm.x * w)
                cy = int(lm.y * h)

                self.lmList.append([id, cx, cy])

                if draw and id == PointId:
                    cv2.circle(
                        img,
                        (cx, cy),
                        5,
                        (255, 0, 255),
                        cv2.FILLED
                    )

                if pointprintid is None and pointprint:
                    print(id, cx, cy)

                if (
                    pointprintid is not None
                    and id == pointprintid
                    and pointprint
                ):
                    print(self.lmList[id])

        return self.lmList

    def fingersUp(self):

        fingers = []

        # Thumb
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[4]][1]:
            # for right hand
            if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        elif self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[4]][1]:
            # for left hand
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        
 

        # 4 Fingers
        for id in range(1, 5):

            if (
                self.lmList[self.tipIds[id]][2]
                < self.lmList[self.tipIds[id] - 2][2]
            ):
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
    
    def findDistance(self, p1, p2, img ,draw=True ,r=15 ,t=3):

        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]

        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]