from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label

import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

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
    # Pause for half a second.
    return values


class Cola2016Widget(Widget):
    def on_touch_down(self, touch):
        print(touch)
        read_mcp3008()


class Cola2016App(App):
    def build(self):
        lb1 = Label(text='Hello')
        return lb1


if __name__ == '__main__':
    Cola2016App().run()
