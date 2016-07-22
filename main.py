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

servo_min = 130  # min Pulse length out of 4096
servo_max = 600  # max Pulse length out of 4096
pwm.set_pwm_freq(60)  # Set frequency to 60hz, good for servos.


CLK = 11
MISO = 9
MOSI = 10
CS = 8

mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
print('-' * 57)


def read_mcp3008():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)
    # Print the ADC values.
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
    print(values)
    # Pause for half a second.
    return values


# class ColaWidget(Widget):
#     def on_touch_down(self, touch):
#         print(touch)


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


class GameStatus():

    def __init__(self):
        self.sw = 0
        self.sw_count = 0
        self.h1 = 0
        self.h2 = 0
        self.h3 = 0
        self.h4 = 0
        self.h5 = 0

    def game_reset(self):
        self.sw = 0
        self.sw_count = 0
        self.h1 = 0
        self.h2 = 0
        self.h3 = 0
        self.h4 = 0
        self.h5 = 0
        pwm.set_pwm(4, 0, 0)
        pwm.set_pwm(5, 0, 0)
        pwm.set_pwm(6, 0, 0)
        pwm.set_pwm(7, 0, 0)
        pwm.set_pwm(8, 0, 0)
        pwm.set_pwm(9, 0, 0)

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
        Clock.schedule_interval(self.light_blinky, 1)

    def update_mcp3008_value(self, nap):
        values = read_mcp3008()

        values[0] = translate(values[0], 0, 1023, 130, 600)
        pwm.set_pwm(0, 0, int(values[0]))  # servo..LR
        pwm.set_pwm(1, 0, int(values[0]))  # servo..LR

        print('rotation value: %d' % values[0])
        if values[0] >= 512:
            self.root.ids.vr_rotation.text = 'cw'
        else:
            self.root.ids.vr_rotation.text = 'ccw'

        if values[1] > 512:
            self.root.ids.switch_status_text.text = 'switch on'
        else:
            self.root.ids.switch_status_text.text = 'switch off'

        # if values[2] > 512:
        #     self.root.ids.HL1.text = 'H1 on'
        #     pwm.set_pwm(4, 0, 4095)
        # else:
        #     self.root.ids.HL1.text = 'H1 off'
        #     pwm.set_pwm(4, 0, 0)

        # if values[3] > 512:
        #     self.root.ids.HL2.text = 'H2 on'
        #     pwm.set_pwm(5, 0, 4095)
        # else:
        #     self.root.ids.HL2.text = 'H2 off'
        #     pwm.set_pwm(5, 0, 0)
        #
        # if values[4] > 512:
        #     self.root.ids.HL3.text = 'H3 on'
        #     pwm.set_pwm(6, 0, 4095)
        # else:
        #     self.root.ids.HL3.text = 'H3 off'
        #     pwm.set_pwm(6, 0, 0)
        #
        # if values[5] > 512:
        #     self.root.ids.HL4.text = 'H4 on'
        #     pwm.set_pwm(7, 0, 4095)
        # else:
        #     self.root.ids.HL4.text = 'H4 off'
        #     pwm.set_pwm(7, 0, 0)
        #
        # if values[6] > 512:
        #     self.root.ids.HL5.text = 'H5 on'
        #     pwm.set_pwm(8, 0, 4095)
        # else:
        #     self.root.ids.HL5.text = 'H5 off'
        #     pwm.set_pwm(8, 0, 0)

        values = map(str, values)
        values_string = ', '.join(values)
        self.root.ids.mcp.text = values_string

    def light_blinky(self, nap):
        if gs.sw == 1:
            gs.sw_count += 1
        else:
            gs.sw_count = 0

        if gs.sw == 1 and gs.sw_count % 3 == 0:
            pwm.set_pwm(9, 0, 4095)
        else:
            pwm.set_pwm(9, 0, 0)
        if gs.sw == 1 and gs.sw_count % 3 == 1:
            pwm.set_pwm(10, 0, 4095)
        else:
            pwm.set_pwm(10, 0, 0)
        if gs.sw == 1 and gs.sw_count % 3 == 2:
            pwm.set_pwm(11, 0, 4095)
        else:
            pwm.set_pwm(11, 0, 0)

    def switch_on(self):
        print('press switch')
        gs.sw = 1


    def reset_on(self):
        print('reset on')
        gs.game_reset()
        self.root.ids.HL1.text = 'h1 off'
        self.root.ids.HL2.text = 'h2 off'

    def h1_press(self):
        gs.h1 = 1
        pwm.set_pwm(4, 0, 4095)

    def h2_press(self):
        gs.h2 = 1
        pwm.set_pwm(5, 0, 4095)

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
