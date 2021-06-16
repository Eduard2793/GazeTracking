
from subprocess import *

def run(cmd, stdout, stderr):
    return Popen(cmd, stdout=stdout, stderr=stderr, shell=False)    

def start_process(cmd):
    return run(cmd, PIPE, PIPE)

def start():

    """
    This function starts roscore, the subscriber node (listener.py)
    and the publisher node (Trecker_with6acord.py) in three parallel
    subprocesses.
    """

    master = start_process(['/opt/ros/noetic/bin/roscore'])

    listener_node = start_process(['rosrun', 'spoproject', 'listener.py'])

    talker_node = start_process(['rosrun', 'spoproject', 'Trecker_with6acord.py'])
    
    outCode = talker_node.wait()

    if outCode == 0 or outCode == 1:

        call(["killall", "-9", "rosmaster"])

        listener_node.kill()
        master.kill()

    else:
        print("strainge Out Code")
