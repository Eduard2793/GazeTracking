#!/usr/bin/env python

import os
from gaze_tracking.gaze_tracking import GazeTracking
import cv2
import numpy as np
import time

import matplotlib.pylab as plt

watchsOnPoint = False

def click(event, x, y, flags, param):
    global watchsOnPoint
    if event == cv2.EVENT_LBUTTONDOWN:
        watchsOnPoint = True

def getInhabitationOfPupilsWhenLookingOnScreen(s_w,s_h):

    """
    This function is intended for the calibration.
    It provides information about position of pupils on a frame
    when looking on the define point of the screen.
    This information is then used for avaluating the size of the domain in which pupils can be
    and the coordinats of the pupils when looking on the center of the screen.

    Arguments:
        s_w: width of the screen; s_h: height of the screen

    Return:
        List of the coordinates of pupils corresponding to the following cases:
        [looking on the center, looking on the top, looking on the right, on the bottom, on the left]
    """

    global watchsOnPoint
    
    gaze = GazeTracking() # object that is used for gaze traking
    
    webcam = cv2.VideoCapture(0)
    cv2.namedWindow("Colibration",cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Colibration", 0, cv2.cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("Colibration", click)

    points_f = [] # cords of domain that we are looking for

    text1 = "Let's pass through the calibration"
    text2 = "Look at the red point and click on"
    text3 = "the screen, please."
    
    k = 0 # counter of points
    i = 0 # counter of values to enumerait the coordinat of pupils when looking on concret point

    x_Pup = [] # x of pupils when looking on points_s[k]
    y_Pup = []

    x_face = [] # coordinats of point between eyes # not using now. use x_face_look_center
    y_face = []

    x_face_look_center = []
    y_face_look_center = []
    
    while cv2.getWindowProperty("Colibration", cv2.WND_PROP_VISIBLE) == 1 and k < 5:        

        _, frame = webcam.read()
        
        w = frame.shape[1]
        h = frame.shape[0]

        gaze.refresh(frame)
        frame = gaze.annotated_frame()
        
        # points on screen where the object should look
        points_s = [[w/2, h/2],  # center
                    [w/2, 10],     # top
                    [w-10, h/2], # right boundary
                    [w/2, h-10], # bottom
                    [10, h/2]]     # left boundary
                
        p = points_s[k] # corent point

        cv2.putText(frame, text1, (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2)
        cv2.putText(frame, text2, (30, 90), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2)
        cv2.putText(frame, text3, (120, 120), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2)
        cv2.circle(frame, (round(p[0]),round(p[1])), 10, (0,0,255), -1)

        resized_frame = cv2.resize(frame, (s_w,s_h), interpolation = cv2.INTER_AREA)
        cv2.imshow("Colibration", resized_frame)
                
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()

        left_eye = gaze.eye_left
        right_eye = gaze.eye_right
            
        if watchsOnPoint:
            
            text = ""
            
            if i < 20:

                if right_pupil != None and left_pupil != None and left_eye != None and right_eye != None:

                    x_Pup.append((right_pupil[0] + left_pupil[0]) / 2)
                    y_Pup.append((right_pupil[1] + left_pupil[1]) / 2)                    
                    
                    x_face.append((left_eye.cods[0] + right_eye.cods[0])/2)
                    y_face.append((left_eye.cods[1] + right_eye.cods[1])/2)
                    
                    if k == 0:
                        x_face_look_center.append((left_eye.cods[0] + right_eye.cods[0])/2)
                        y_face_look_center.append((left_eye.cods[1] + right_eye.cods[1])/2)
                    
                    i += 1
                    time.sleep(0.02)

            if i == 20:
                points_f.append([sum(x_Pup)/len(x_Pup),sum(y_Pup)/len(y_Pup)])
                x_Pup = []
                y_Pup = []
                
                text1 = ""
                text2 = "Look at the red point and click on"
                text3 = "the screen, please."
                            
                k += 1
                i = 0
                watchsOnPoint = False

        if cv2.waitKey(1) == 27:
            break

    if len(x_face) == 0 or len(y_face) == 0:
        
        eye_cords_when_looking_on_center = [0,0]
    else:

        eye_cords_when_looking_on_center = [sum(x_face_look_center)/len(x_face_look_center),sum(y_face_look_center)/len(y_face_look_center)]

            
    cv2.destroyAllWindows() 
    webcam.release()

    points_f.append(eye_cords_when_looking_on_center)

    return points_f
