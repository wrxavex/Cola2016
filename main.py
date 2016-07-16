from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label


class Cola2016Widget(Widget):
    def on_touch_down(self, touch):
        print(touch)


class Cola2016App(App):
    def build(self):
        lb1 = Label(text='Hello')
        return lb1


if __name__ == '__main__':
    Cola2016App().run()
