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

        # Landmark lists — separate for each hand
        self.lmLists = {"Left": [], "Right": []}

        # Keep a single lmList for backward compatibility (defaults to first detected hand)
        self.lmList = []

    def findHands(self, img, draw=True):

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        # Reset both hand landmark lists each frame
        self.lmLists = {"Left": [], "Right": []}

        if self.results.multi_hand_landmarks:

            for handLms in self.results.multi_hand_landmarks:

                if draw:
                    self.mpDraw.draw_landmarks(
                        img,
                        handLms,
                        self.mpHands.HAND_CONNECTIONS
                    )

        return img

    def findPosition(self, img, handType=None, handNo=0,
                     draw=True,
                     PointId=None,
                     pointprintid=None,
                     pointprint=False):
        """
        Find positions of hand landmarks.
        
        Args:
            img: The camera frame.
            handType: "Left" or "Right" to get a specific hand.
                      If None, falls back to handNo index (backward compatible).
            handNo: Index of the hand (0 or 1) — used only when handType is None.
            draw: Whether to draw the specified point.
            PointId: Landmark ID to draw a circle on.
            pointprintid: Landmark ID to print coordinates for.
            pointprint: Whether to print landmark coordinates.
        
        Returns:
            List of [id, cx, cy] for the requested hand.
        """

        lmList = []

        if self.results.multi_hand_landmarks and self.results.multi_handedness:

            # Build landmark lists for all detected hands
            for idx, (handLms, handedness) in enumerate(
                zip(self.results.multi_hand_landmarks,
                    self.results.multi_handedness)
            ):
                # MediaPipe labels the hand from the camera's perspective,
                # so we flip it to match the user's perspective (since image is flipped)
                label = handedness.classification[0].label  # "Left" or "Right"

                hand_lm_list = []
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx = int(lm.x * w)
                    cy = int(lm.y * h)
                    hand_lm_list.append([id, cx, cy])

                    if draw and id == PointId:
                        cv2.circle(
                            img,
                            (cx, cy),
                            5,
                            (255, 0, 255),
                            cv2.FILLED
                        )

                    if pointprintid is None and pointprint:
                        print(f"[{label}] {id}, {cx}, {cy}")

                    if (
                        pointprintid is not None
                        and id == pointprintid
                        and pointprint
                    ):
                        print(f"[{label}] {hand_lm_list[id]}")

                # Store in the per-hand dictionary
                self.lmLists[label] = hand_lm_list

            # Determine which hand to return
            if handType is not None:
                # Return the requested hand type
                lmList = self.lmLists.get(handType, [])
            else:
                # Backward compatible: return by index
                if handNo < len(self.results.multi_hand_landmarks):
                    label = self.results.multi_handedness[handNo].classification[0].label
                    lmList = self.lmLists.get(label, [])

        # Keep backward compatibility with self.lmList
        self.lmList = lmList

        return lmList

    def fingersUp(self, handType=None):
        """
        Detect which fingers are up for a given hand.
        
        Args:
            handType: "Left" or "Right". If None, uses self.lmList (backward compatible).
        
        Returns:
            List of 5 values (1=up, 0=down) for [thumb, index, middle, ring, pinky].
        """

        if handType is not None:
            lmList = self.lmLists.get(handType, [])
        else:
            lmList = self.lmList

        if len(lmList) < 21:
            return []

        fingers = []

        # Thumb — use handedness to determine direction
        if handType == "Right":
            # Right hand: thumb tip should be to the LEFT of thumb IP (in flipped image)
            if lmList[self.tipIds[0]][1] < lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif handType == "Left":
            # Left hand: thumb tip should be to the RIGHT of thumb IP (in flipped image)
            if lmList[self.tipIds[0]][1] > lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            # Backward compatible: auto-detect using relative position
            if lmList[self.tipIds[0]][1] < lmList[self.tipIds[4]][1]:
                # Right hand
                if lmList[self.tipIds[0]][1] < lmList[self.tipIds[0] - 1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            elif lmList[self.tipIds[0]][1] > lmList[self.tipIds[4]][1]:
                # Left hand
                if lmList[self.tipIds[0]][1] > lmList[self.tipIds[0] - 1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

        # 4 Fingers (index, middle, ring, pinky)
        for id in range(1, 5):
            if (
                lmList[self.tipIds[id]][2]
                < lmList[self.tipIds[id] - 2][2]
            ):
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def findDistance(self, p1, p2, img, handType=None, draw=True, r=15, t=3):
        """
        Find distance between two landmarks on a specific hand.
        
        Args:
            p1, p2: Landmark IDs to measure distance between.
            img: The camera frame.
            handType: "Left" or "Right". If None, uses self.lmList (backward compatible).
            draw: Whether to draw the line and points.
        
        Returns:
            (length, img, [x1, y1, x2, y2, cx, cy])
        """

        if handType is not None:
            lmList = self.lmLists.get(handType, [])
        else:
            lmList = self.lmList

        x1, y1 = lmList[p1][1:]
        x2, y2 = lmList[p2][1:]

        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]

    def getDetectedHands(self):
        """
        Returns a list of hand types currently detected (e.g., ["Left"], ["Right"], or ["Left", "Right"]).
        """
        return [hand for hand, lm in self.lmLists.items() if len(lm) > 0]


def displayModuleName(img, module_name):
    """
    Draw the active module name as a professional overlay on the frame.

    Places a semi-transparent rounded banner at the top-center of the frame
    with a text shadow for readability. Designed to be lightweight and
    consistent across all modules.

    Args:
        img: The OpenCV frame (numpy array, modified in-place).
        module_name: The name string to display (e.g. "Virtual Mouse").
    """
    if not module_name:
        return

    font = cv2.FONT_HERSHEY_TRIPLEX
    font_scale = 0.7
    thickness = 2
    color = (255, 255, 255)       # white text
    shadow_color = (0, 0, 0)      # black shadow
    bg_color = (40, 40, 40)       # dark grey banner

    # Measure text size
    (text_w, text_h), baseline = cv2.getTextSize(
        module_name, font, font_scale, thickness
    )

    frame_h, frame_w = img.shape[:2]

    # Centre the banner horizontally, 8px from the bottom
    pad_x, pad_y = 16, 10
    box_w = text_w + pad_x * 2
    box_h = text_h + pad_y * 2 + baseline
    x_start = (frame_w - box_w) // 2
    y_start = frame_h - box_h - 8

    # Semi-transparent background banner
    overlay = img.copy()
    cv2.rectangle(
        overlay,
        (x_start, y_start),
        (x_start + box_w, y_start + box_h),
        bg_color,
        cv2.FILLED,
    )
    cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)

    # Text position (bottom-left of the text baseline)
    text_x = x_start + pad_x
    text_y = y_start + pad_y + text_h

    # Shadow (offset by 1px)
    cv2.putText(
        img, module_name,
        (text_x + 1, text_y + 1),
        font, font_scale, shadow_color, thickness + 1, cv2.LINE_AA,
    )

    # Main text
    cv2.putText(
        img, module_name,
        (text_x, text_y),
        font, font_scale, color, thickness, cv2.LINE_AA,
    )