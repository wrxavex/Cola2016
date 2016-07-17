from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from time import strftime

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
    print(values)
    # Pause for half a second.
    return values


# class ColaWidget(Widget):
#     def on_touch_down(self, touch):
#         print(touch)


class ColaApp(App):
    # def build(self):
    #     return ColaWidget

    def on_start(self):
        Clock.schedule_interval(self.update_mcp3008_value, 1)

    def update_mcp3008_value(self, nap):
        values = read_mcp3008()

        print('rotation value: %d' % values[0])

        values = map(str, values)
        values_string = ', '.join(values)
        self.root.ids.mcp.text = values_string

    def switch_on(self):
        print('press switch')

    def reset_on(self):
        print('reset on')


class ColaLayout(BoxLayout):
    time_prop = ObjectProperty(None)


if __name__ == '__main__':
    ColaApp().run()
