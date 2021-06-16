#!/usr/bin/env python

import rospy
from std_msgs.msg import String

import os
import cv2
import numpy as np
import matplotlib.pylab as plt
from gaze_tracking.gaze_tracking import GazeTracking
from gaze_tracking.colibrationWithCV import getInhabitationOfPupilsWhenLookingOnScreen
from gi import require_version
require_version("Gdk", "3.0")
from gi.repository import Gdk


def get_screen_size(display):

    """
    This function provides the width and the height of the screen.

    Arguments:
        object Gdk.Display.get_default()

    Return:
        touple (width, height)
    """
    
    mon_geoms = [
        display.get_monitor(i).get_geometry()
        for i in range(display.get_n_monitors())
    ]

    x0 = min(r.x            for r in mon_geoms)
    y0 = min(r.y            for r in mon_geoms)
    x1 = max(r.x + r.width  for r in mon_geoms)
    y1 = max(r.y + r.height for r in mon_geoms)

    return x1 - x0, y1 - y0


def domain(x, y, s_w, s_h):

    """
    The function estimates the rectangle that includes the given point.

    Arguments:
        x and y coordinates of the point and width and height of the screen

    Return:
        integer 0 <= n <= 5
    """
    
    if x < s_w / 3:
        return 0 if y < s_h / 2 else 3
    if s_w / 3 < x < s_w * 2 / 3:
        return 1 if y < s_h / 2 else 4
    if x > s_w * 2 / 3:
        return 2 if y < s_h / 2 else 5


def drowLine(cord,orient,size):

    """
    The function provides the coordinates of the line.
    
    Arguments:
        starting x or y coordinate of the line, orientation
        (string. "vert" or "hor") and length of the line

    Return:
        list of two points (start and end of the line)
    """
        global cv2
        
        if orient == "vert":
            x1 = cord
            x2 = cord
            y1 = 0
            y2 = size
        elif orient == "hor":
            x1 = 0
            x2 = size
            y1 = cord
            y2 = cord
        else:
            print("not hor not vert")
            return 0
        
        return [(x1, y1), (x2, y2)] 

def talker():

    """
    This function tracks the user's gaze.
    First it runs the colibration.
    Using the information provided by colibration function it estimates
    the place on the screen where the user is looking.
    Whith frequence of 10 Hz the function publishes on the topic "chatter"
    the string representation of integer 0 <= n <= 5 which coresponds to
    the rectangle in which the user is looking.
    """
    
    pub = rospy.Publisher('chatter', String, queue_size=10)
    rospy.init_node('talker', anonymous=True)
    rate = rospy.Rate(10) # 10hz
    
    (s_w, s_h) = get_screen_size(Gdk.Display.get_default())
    s_h = s_h - 100

    # colibr
    points_f = getInhabitationOfPupilsWhenLookingOnScreen(s_w,s_h)
    
    f_w = points_f[4][0] - points_f[2][0] - 3
    f_h = points_f[3][1] - points_f[1][1] - 2

    f_c = points_f[0]

    eye_cords_when_looking_on_centre = points_f[5]
    # colibr

    # grid
    vert_lines = []#[200,400]
    hor_lines = []#[250]

    n = 3
    m = 2
    grid_w = round(s_w/n)
    grid_h = round(s_h/m)

    for i in range(1,n):
        vert_lines.append(i*grid_w)
    for i in range(1,m):
        hor_lines.append(i*grid_h)

    # grid

    dim = (s_w,s_h)

    # treck
    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0)
    cv2.namedWindow("Treking", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Treking", 0, cv2.cv2.WINDOW_FULLSCREEN)
    #treck

    # kalman
    K = 0.1
    x_f_k = 0
    y_f_k = 0
    j = 0
    # kalman
    prev_domain = 1
    cur_domain = 1
    list_audio = []
    
    while cv2.getWindowProperty("Treking", cv2.WND_PROP_VISIBLE) == 1:
        _, frame = webcam.read()

        gaze.refresh(frame)

        frame = gaze.annotated_frame()

        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()

        left_eye = gaze.eye_left
        right_eye = gaze.eye_right

        if right_pupil is not None and left_pupil is not None and 
           left_eye is not None and right_eye is not None:
            x_of_pupils = (right_pupil[0] + left_pupil[0]) / 2
            y_of_pupils = (right_pupil[1] + left_pupil[1]) / 2

            x_of_eyes = (left_eye.cods[0] + right_eye.cods[0])/2
            y_of_eyes = (left_eye.cods[1] + right_eye.cods[1])/2 

            if j == 0:
                x_of_pupils_k = x_of_pupils
                y_of_pupils_k = y_of_pupils

                x_of_eyes_k = x_of_eyes
                y_of_eyes_k = y_of_eyes
            else:
                x_of_pupils_k = x_of_pupils * K + x_of_pupils_k * (1 - K)
                y_of_pupils_k = y_of_pupils * K + y_of_pupils_k * (1 - K)

                x_of_eyes_k = x_of_eyes * K + x_of_eyes_k * (1 - K)
                y_of_eyes_k = y_of_eyes * K + y_of_eyes_k * (1 - K)

            e_w = 5.7*frame.shape[1]/s_w
            e_h = 4.3*frame.shape[0]/s_h
                              
            x_d = (x_of_eyes_k - eye_cords_when_looking_on_centre[0])
            y_d = (y_of_eyes_k - eye_cords_when_looking_on_centre[1])
            
            [x, y] = [((frame.shape[1] - (x_of_pupils_k - (f_c[0] + x_d))*frame.shape[1]/f_w) - frame.shape[1]/2),
                      ((y_of_pupils_k - (f_c[1] + y_d))*frame.shape[0]/f_h) + frame.shape[0]/2]

            if x > frame.shape[1]:
                x = frame.shape[1] - 11
            if x < 0:
                x = 11
            if y > frame.shape[0]:
                y = frame.shape[0] - 11
            if y < 0:
                y = 11
                
            cur_domain = domain(x, y, frame.shape[1], frame.shape[0])
            
            if cur_domain != prev_domain:
                pub.publish(str(cur_domain))
                rate.sleep()
            prev_domain = cur_domain

            #################### effect
            xg = round(x)
            yg = round(y)
            r = 10
            alfa = 1000
            betha = 600
            for i in range(xg-r,xg+r+1,2):
                for j in range(yg-r,yg+r+1,2):
                    if i < frame.shape[1] and j < frame.shape[0]:
                        er = ((i-xg)**2 + (j-yg)**2)**0.5
                        if er == 0:
                            er = 0.0001
                        if er <= r:
                            [b,g,red] = frame[j][i].copy()
                            frame[j][i][0] = b
                            frame[j][i][1] = alfa*er + g
                            frame[j][i][2] = (betha/er)+ red

            #################### effect

            cv2.circle(frame, (round(f_c[0] + x_d),round(f_c[1] + y_d)), 5, (0,255,0), 2)

            j += 1
            
        resized_frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        
        cords = drowLine(vert_lines[0], "vert", s_h)
        cv2.line(resized_frame, cords[0], cords[1], [0, 0, 0])
        cords = drowLine(vert_lines[1], "vert", s_h)
        cv2.line(resized_frame, cords[0], cords[1], [0, 0, 0])
        cords = drowLine(hor_lines[0], "hor", s_w)
        cv2.line(resized_frame, cords[0], cords[1], [0, 0, 0])

        cv2.imshow("Treking", resized_frame)

        if cv2.waitKey(1) == 27:
            break
        
    cv2.destroyAllWindows() 
    webcam.release()
    pub.publish(str(6))


if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass

