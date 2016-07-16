from kivy.app import App
from kivy.uix.widget import Widget


class Cola2016Widget(Widget):
    def on_touch_down(self, touch):
        print(touch)


class Cola2016App(App):
    def build(self):
        return Cola2016Widget()


if __name__ == '__main__':
    Cola2016App().run()
