#!/usr/bin/env python

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QImage, QPalette, QBrush
from pydub import AudioSegment
from pydub.playback import play
import sys
import os
import start_ros as msr
from Blinking_count import blink


class Interface(QWidget):

    '''This class is creating GUI for an interaction with a gaze tracker.
       It provides main menu with several options for making custom music.'''

    def __init__(self):
        super().__init__()
        
        # play button
        self.play_button = QPushButton(self)
        self.play_button.setText("Play")
        self.play_button.setFont(QFont('Comic Sans MS', 15))
        self.play_button.resize(100, 50)
        self.play_button.clicked.connect(self.play)
        
        # beat button
        self.freq = 1
        self.const = 12
        self.beat_button = QPushButton(self)
        self.beat_button.setText("Beat")
        self.beat_button.setFont(QFont('Comic Sans MS', 15))
        self.beat_button.resize(100, 50)
        self.beat_button.clicked.connect(self.count_blinks)

        self.buttons_hbox = QHBoxLayout()
        self.buttons_hbox.addWidget(self.beat_button, 0, Qt.AlignLeft)
        self.buttons_hbox.addWidget(self.play_button, 0, Qt.AlignRight)
        
        # label Make your melody
        self.ins_label = QLabel()
        self.ins_label.setText("Make your melody")
        self.ins_label.setFont(QFont('Comic Sans MS', 30))
        self.ins_label.setStyleSheet('color: white')
        self.ins_label.setAlignment(Qt.AlignCenter)
        
        # check-boxes
        self.drums_cb = QCheckBox()
        self.drums_cb.setText("Drums")
        self.drums_cb.setFont(QFont('Comic Sans MS', 20))
        self.drums_cb.clicked.connect(self.set_drums)

        self.hihat_cb = QCheckBox()
        self.hihat_cb.setText("Hi-Hat")
        self.hihat_cb.setFont(QFont('Comic Sans MS', 20))
        
        self.bass_cb = QCheckBox()
        self.bass_cb.setText("Bass")
        self.bass_cb.setFont(QFont('Comic Sans MS', 20))
        
        self.cbs_hbox = QHBoxLayout()
        self.cbs_hbox.addWidget(self.drums_cb, 0, Qt.AlignLeft)
        self.cbs_hbox.addWidget(self.hihat_cb, 0, Qt.AlignCenter)
        self.cbs_hbox.addWidget(self.bass_cb, 0, Qt.AlignRight)
        
        # harmonic canvas button
        self.harm_button = QPushButton(self)
        self.harm_button.setText("Show harmonic canvas")
        self.harm_button.setFont(QFont('Comic Sans MS', 15))
        self.harm_button.resize(200, 50)
        self.harm_button.clicked.connect(self.harm)
        
        # Main widget
        self.main_vbox = QVBoxLayout()
        self.main_vbox.addLayout(self.buttons_hbox)
        self.main_vbox.addWidget(self.ins_label)
        self.main_vbox.addLayout(self.cbs_hbox)
        self.main_vbox.addWidget(self.harm_button, 0, Qt.AlignCenter)
        self.main_vbox.setContentsMargins(100, 50, 100, 50)
        
        # Main window settings
        self.setLayout(self.main_vbox)
        self.resize(700, 500)
        self.setWindowTitle('EyE_BeaT')
        oImage = QImage("images/background.jpg")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))                        
        self.setPalette(palette)
        self.center()
        self.show()

    def center(self):
        '''Set the main window on the center of screen.'''
        frameGm = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def harm(self):
        '''Launch window for calibration and after that provide special panel with
        harmonic canvas for making music.'''
        msr.start()

    def set_drums(self):
        '''Overlay a drum part on the music file. Write result in the result_with_drums.mp3.'''
        if  os.path.exists('result.mp3'):
            res = AudioSegment.from_mp3('result.mp3')
            res_len = res.duration_seconds
            chord = AudioSegment.from_mp3('mp3_chords/1.mp3')
            chord_len = chord.duration_seconds
            len_in_chords = int(res_len / chord_len)
            chord_len_ms = len(chord)
            drums = AudioSegment.from_mp3('mp3_drums/beats3.mp3')
            drums = drums[:chord_len_ms]
            whole_drums = drums * len_in_chords
            res_with_drums = res.overlay(whole_drums)
            res_with_drums.export('result_with_drums.mp3', format='mp3')

    def count_blinks(self):
        '''Count user's blinks and set up the frame rate for music file.'''
        def speed_change(sound, speed=1.0):
            '''Manually override the frame_rate. This tells the computer how many
               samples to play per second'''
            if speed <= 0:
                speed = 1
            sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
                 "frame_rate": int(sound.frame_rate * speed)
              })
             '''Convert the sound with altered frame rate to a standard frame rate
                so that regular playback programs will work right. They often only
                know how to play audio at standard frame rate (like 44.1k)'''
            return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

        self.hide()
        self.freq = blink()
        msg = QMessageBox()
        msg.setText(f'Вы моргнули {self.freq} раз.')
        msg.setWindowTitle('Blinks')
        msg.exec_()
        self.show()
        with open('blinks.txt', 'w') as bf:
            bf.write(str(self.freq))
        if os.path.exists('result_with_drums.mp3'):
            rwd = AudioSegment.from_mp3('result_with_drums.mp3')
            speed = self.freq / self.const
            res = speed_change(rwd, speed)
            res.export('result_with_drums_freq.mp3', format='mp3')
        elif os.path.exists('result.mp3'):
            r = AudioSegment.from_mp3('result.mp3')
            speed = self.freq / self.const
            res = speed_change(r, speed)
            res.export('result_with_freq.mp3', format='mp3')

    def play(self):
        '''Play the finished music file. It depends on selected options, which file will play.'''
        m = None
        if os.path.exists('result_with_drums_freq.mp3') and self.drums_cb.isChecked():
            m = AudioSegment.from_mp3('result_with_drums_freq.mp3')
        elif os.path.exists('result_with_drums.mp3') and self.drums_cb.isChecked():
            m = AudioSegment.from_mp3('result_with_drums.mp3')
        elif os.path.exists('result_with_freq.mp3'):
            m = AudioSegment.from_mp3('result_with_freq.mp3')
        elif os.path.exists('result.mp3'):
            m = AudioSegment.from_mp3('result.mp3')
        if m is not None:
            play(m)

app = QApplication(sys.argv)        
w = Interface()
app.exec_()
