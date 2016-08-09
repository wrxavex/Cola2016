# -*- coding: utf-8 -*-

from __future__ import division

import time

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

import Adafruit_PCA9685 as servo
import Adafruit_MCP3008

# Servo : IC2 = 0x40
pwm = servo.PCA9685()

# 設定舵機旋轉角度 min 及 max
servo_min = 210  # min Pulse length out of 4096
servo_max = 500  # max Pulse length out of 4096
pwm.set_pwm_freq(60)  # Set frequency to 60hz, good for servos.


CLK = 11
MISO = 9
MOSI = 10
CS = 8

mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
# print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
# print('-' * 57)


def read_mcp3008():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)
    # Print the ADC values.
    # print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
    # print(values)
    # Pause for half a second.
    return values


# class ColaWidget(Widget):
#     def on_touch_down(self, touch):
#         print(touch)


# 像arduino的map的用法
def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


# 遊戲設定值物件
class GameStatus():

    def __init__(self):
        self.sw = 0                 # sw的值
        self.sw_count = 0           # 計算撞到sw後的計數
        self.sw_count_limit = 30   # sw計數最大值→閃燈時間

        self.h1 = 0                 # 偵測洞口一
        self.h2 = 0                 # 偵測洞口二
        self.h3 = 0                 # 偵測洞口三
        self.h4 = 0                 # 偵測洞口四
        self.h5 = 0                 # 偵測洞口五

        self.cd = 0                 # 偵測碰撞開關

        self.light_set = [[1, 0, 1, 1, 1, 1],       # 六組燈光的調節
                          [0, 1, 0, 1, 1, 1],
                          [1, 0, 1, 0, 1, 1],
                          [1, 1, 0, 1, 0, 1],
                          [1, 1, 1, 0, 1, 0],
                          [1, 1, 1, 1, 0, 1]]

        self.test_mode = 0      # 設定是否是測試模式

        # 初始化PCA-9685，因為用的繼電器模組是low-active 所以初始值設high-4095（12bit）
        pwm.set_pwm(1, 0, 4095)
        pwm.set_pwm(2, 0, 4095)
        pwm.set_pwm(3, 0, 4095)
        pwm.set_pwm(4, 0, 4095)
        pwm.set_pwm(5, 0, 4095)
        pwm.set_pwm(6, 0, 4095)
        pwm.set_pwm(7, 0, 4095)
        pwm.set_pwm(8, 0, 4095)
        pwm.set_pwm(9, 0, 4095)
        pwm.set_pwm(10, 0, 4095)
        pwm.set_pwm(11, 0, 4095)
        pwm.set_pwm(12, 0, 4095)
        pwm.set_pwm(13, 0, 4095)
        pwm.set_pwm(14, 0, 4095)
        pwm.set_pwm(15, 0, 4095)

    def game_reset(self):
        self.sw = 0
        self.sw_count = 0


        self.h1 = 0
        self.h2 = 0
        self.h3 = 0
        self.h4 = 0
        self.h5 = 0

        self.cd = 0

        pwm.set_pwm(1, 0, 4095)
        pwm.set_pwm(2, 0, 4095)
        pwm.set_pwm(3, 0, 4095)
        pwm.set_pwm(4, 0, 4095)
        pwm.set_pwm(5, 0, 4095)
        pwm.set_pwm(6, 0, 4095)
        pwm.set_pwm(7, 0, 4095)
        pwm.set_pwm(8, 0, 4095)
        pwm.set_pwm(9, 0, 4095)
        pwm.set_pwm(10, 0, 4095)
        pwm.set_pwm(11, 0, 4095)
        pwm.set_pwm(12, 0, 4095)
        pwm.set_pwm(13, 0, 4095)
        pwm.set_pwm(14, 0, 4095)
        pwm.set_pwm(15, 0, 4095)

    # def hl1_on(self):
    #     pwm.set_pwm(4, 0, 4095)
    #     self.hl1 = 1
    #
    # def hl1_off(self):
    #     pwm.set_pwm(4, 0, 0)
    #     self.hl1 = 0
    #
    # def hl2_on(self):
    #     pwm.set_pwm(5, 0, 4095)
    #     self.hl2 = 1
    #
    # def hl2_off(self):
    #     pwm.set_pwm(5, 0, 0)
    #     self.hl2 = 0


class ColaApp(App):
    # def build(self):
    #     return ColaWidget

    def on_start(self):
        Clock.schedule_interval(self.update_mcp3008_value, 0.0016)
        Clock.schedule_interval(self.light_blinky, 0.25)

    def update_mcp3008_value(self, nap):
        values = read_mcp3008()

        values[0] = translate(values[0], 0, 1023, servo_min, servo_max)
        pwm.set_pwm(12, 0, int(values[0]))  # servo..LR

        # print('rotation value: %d' % values[0])

        if gs.test_mode == 0 and values[1] > 850:
            self.root.ids.H1.text = 'H1 on'
            pwm.set_pwm(6, 0, 0)
        else:
            self.root.ids.H1.text = 'H1 off'
            pwm.set_pwm(6, 0, 4095)

        if gs.test_mode == 0 and values[2] > 850:
            self.root.ids.H2.text = 'H2 on'
            pwm.set_pwm(7, 0, 0)
        else:
            self.root.ids.H2.text = 'H2 off'
            pwm.set_pwm(7, 0, 4095)

        if gs.test_mode == 0 and values[3] > 850:
            self.root.ids.H3.text = 'H3 on'
            pwm.set_pwm(8, 0, 0)
        else:
            self.root.ids.H3.text = 'H3 off'
            pwm.set_pwm(8, 0, 4095)

        if gs.test_mode == 0 and values[4] > 850:
            self.root.ids.H4.text = 'H4 on'
            pwm.set_pwm(9, 0, 0)
        else:
            self.root.ids.H4.text = 'H4 off'
            pwm.set_pwm(9, 0, 4095)

        if gs.test_mode == 0 and values[5] > 850:
            self.root.ids.H5.text = 'H5 on'
            pwm.set_pwm(10, 0, 0)
        else:
            self.root.ids.H5.text = 'H5 off'
            pwm.set_pwm(10, 0, 4095)

        if gs.test_mode == 0 and values[6] > 850 and gs.sw = 0:
            gs.sw = 1
            self.root.ids.switch_status_text.text = 'switch on'
        else:
            self.root.ids.switch_status_text.text = 'switch off'

        if gs.test_mode == 0 and values[7] > 850:
            self.root.ids.switch_status_text.text = 'Collision detection'
        else:
            self.root.ids.switch_status_text.text = 'Collision detection'

        values = map(str, values)
        values_string = ', '.join(values)

        self.root.ids.mcp0.text = values[0]
        self.root.ids.mcp1.text = values[1]
        self.root.ids.mcp2.text = values[2]
        self.root.ids.mcp3.text = values[3]
        self.root.ids.mcp4.text = values[4]
        self.root.ids.mcp5.text = values[5]
        self.root.ids.mcp6.text = values[6]
        self.root.ids.mcp7.text = values[7]

    def light_blinky(self, nap):
        if gs.sw == 1:
            gs.sw_count += 1
        else:
            gs.sw_count = 0

        if gs.sw_count > gs.sw_count_limit:
            gs.sw = 0

        numrows = len(gs.light_set)

        rows = gs.sw_count % numrows

        print('numrows = %s' % numrows)
        print('rows now = %s' % rows)
        print('test mode = %s' % gs.test_mode)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][0] == 1:
            pwm.set_pwm(0, 0, 0)
        else:
            pwm.set_pwm(0, 0, 4095)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][1] == 1:
            pwm.set_pwm(1, 0, 0)
        else:
            pwm.set_pwm(1, 0, 4095)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][2] == 1:
            pwm.set_pwm(2, 0, 0)
        else:
            pwm.set_pwm(2, 0, 4095)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][3] == 1:
            pwm.set_pwm(3, 0, 0)
        else:
            pwm.set_pwm(3, 0, 4095)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][4] == 1:
            pwm.set_pwm(4, 0, 0)
        else:
            pwm.set_pwm(4, 0, 4095)

        if gs.test_mode == 0 and gs.sw == 1 and gs.light_set[rows][5] == 1:
            pwm.set_pwm(5, 0, 0)
        else:
            pwm.set_pwm(5, 0, 4095)

    def switch_on(self):
        print('press switch')
        gs.sw = 1

    def reset_on(self):
        print('reset on')
        gs.test_mode = 0
        gs.game_reset()
        self.root.ids.H1.text = 'h1 off'
        self.root.ids.H2.text = 'h2 off'
        self.root.ids.H3.text = 'h3 off'
        self.root.ids.H4.text = 'h4 off'
        self.root.ids.H5.text = 'h5 off'

    def all_light(self):
        gs.test_mode = 1
        pwm.set_pwm(1, 0, 0)
        pwm.set_pwm(2, 0, 0)
        pwm.set_pwm(3, 0, 0)
        pwm.set_pwm(4, 0, 0)
        pwm.set_pwm(5, 0, 0)
        pwm.set_pwm(6, 0, 0)
        pwm.set_pwm(7, 0, 0)
        pwm.set_pwm(8, 0, 0)
        pwm.set_pwm(9, 0, 0)
        pwm.set_pwm(10, 0, 0)

    def all_close(self):
        gs.test_mode = 1
        pwm.set_pwm(1, 0, 4095)
        pwm.set_pwm(2, 0, 4095)
        pwm.set_pwm(3, 0, 4095)
        pwm.set_pwm(4, 0, 4095)
        pwm.set_pwm(5, 0, 4095)
        pwm.set_pwm(6, 0, 4095)
        pwm.set_pwm(7, 0, 4095)
        pwm.set_pwm(8, 0, 4095)
        pwm.set_pwm(9, 0, 4095)
        pwm.set_pwm(10, 0, 4095)

    def h1_press(self):
        gs.h1 = 1
        pwm.set_pwm(6, 0, 0)

    def h2_press(self):
        gs.h2 = 1
        pwm.set_pwm(7, 0, 0)

    def h3_press(self):
        gs.h3 = 1
        pwm.set_pwm(8, 0, 0)

    def h4_press(self):
        gs.h4 = 1
        pwm.set_pwm(9, 0, 0)

    def h5_press(self):
        gs.h5 = 1
        pwm.set_pwm(10, 0, 0)

    # def hl1_toggle(self):
    #     if gs.hl1 == 0:
    #         gs.hl1_on()
    #         self.root.ids.HL1.text = 'h1 on'
    #
    #     elif gs.hl1 == 1:
    #         gs.hl1_off()
    #         self.root.ids.HL1.text = 'h1 off'
    #
    # def hl2_toggle(self):
    #     if gs.hl2 == 0:
    #         gs.hl2_on()
    #         self.root.ids.HL2.text = 'h2 on'
    #
    #     elif gs.hl2 == 1:
    #         gs.hl2_off()
    #         self.root.ids.HL2.text = 'h2 off'


class ColaLayout(BoxLayout):
    time_prop = ObjectProperty(None)


if __name__ == '__main__':
    gs = GameStatus()
    ColaApp().run()
