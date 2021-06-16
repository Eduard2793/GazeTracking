#!/usr/bin/env python

import sys
import os
from pydub import AudioSegment
from pydub.playback import play

import rospy
from std_msgs.msg import String

list_audio = []

def play_chord(n):

    """
    The function plays the chord corresponding to the message received.
    """
    
    global list_audio
    folder = 'mp3_chords'
    chords = os.listdir(folder)
    file = folder + "/" + chords[n]
    s = AudioSegment.from_mp3(file)
    list_audio.append(s)
    play(s)

def callback(data):

    """
    The callback function of the subscriber.
    """
    
    global list_audio
    
    rospy.loginfo(rospy.get_caller_id() + ' OH, I heard %s', data.data)
    n = int(data.data)
    
    if n == 6:
        sum(list_audio).export('result.mp3', format='mp3')
    else:
        play_chord(n)


def listener():

    """
    This function sets up the subsciber rosnode "listner" and subscibes
    on the topik "chatter".
    """

    rospy.init_node('listener', anonymous=True)

    rospy.Subscriber('chatter', String, callback)

    rospy.spin()

if __name__ == '__main__':
    listener()
    
