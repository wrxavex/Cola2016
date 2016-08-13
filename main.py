# -*- coding: utf-8 -*-

from __future__ import division

# 讀cpu溫度時用到
import subprocess

# kivy用
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

# PCA9685板用
import Adafruit_PCA9685 as servo

# MCP3008用
import Adafruit_MCP3008

# reset pin 用
import RPi.GPIO as GPIO

# 設定 gpio 命名為bcm
GPIO.setmode(GPIO.BCM)

# 設17 pin為resetpin
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# GPIO.setup(17, GPIO.IN)       # 不使用內建pull down

# Servo : IC2 = 0x40
pwm = servo.PCA9685()

# 切換low active模式，若為low active 的輸出模組請設1，high active請設0
low_active = 1

# 設定sw控制模式，sw_mode = 1 的時候開關off的時候就會停止閃燈，sw_mode = 0的時候鬆開還是會閃完count_limit次數
sw_mode = 1

# mcp3008讀值的頻率，影響到整體的更新率
mcp3008_Frequency = 0.016

# 閃燈的頻率
blink_Frequency = 0.25

# sw計數最大值→閃燈時間
sw_count_limit = 30

# 指定可變電阻最小值
vr_min = 262

# 指定可變電阻最大值
vr_max = 453

# 設定mcp3008引腳讀值觸發點 （0到1023）
analogy_toggle_point = 850

# 設定舵機旋轉角度 min 及 max
servo_min = 210  # min Pulse length out of 4096
servo_max = 500  # max Pulse length out of 4096
pwm.set_pwm_freq(60)  # Set frequency to 60hz, good for servos.

# 設定 spi pin腳（非使用預設值）
CLK = 11
MISO = 9
MOSI = 10
CS = 8

# 建立mcp 為adafruit mcp3008物件
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# 讀mcp3008的函式
def read_mcp3008():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)
    return values


# 像arduino的map的用法，讀可變電阻用
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

    # 設定初始值
    def __init__(self):

        # 開關設定區
        self.sw = 0                 # sw的值
        self.sw_count = 0           # 計算撞到sw後的計數

        # 閃燈作用狀態
        self.lights_status = [0,0,0,0,0,0]

        # 六組閃燈的腳本，腳本為二維陣列，一次呼叫掃福一行值，依序為1到6號燈，值為1時亮燈，0時不亮
        self.light_set = [[1, 0, 1, 1, 1, 1],
                          [0, 1, 0, 1, 1, 1],
                          [1, 0, 1, 0, 1, 1],
                          [1, 1, 0, 1, 0, 1],
                          [1, 1, 1, 0, 1, 0],
                          [1, 1, 1, 1, 0, 1]]

        # 洞口燈作用狀態，共五個洞口燈
        self.hole_lights = [0,0,0,0,0]

        # 偵測碰撞開關
        self.cd = 0

        # 設定是否是測試模式
        self.test_mode = 0

        # PCA9685 在low_active = 1 時全部拉high，否則拉low
        for i in range(16):
            if low_active == 1:
                pwm.set_pwm(i, 0, 4095)

            if low_active == 0:
                pwm.set_pwm(i, 0, 0)

    # 重置遊戲數值
    def game_reset(self):

        # 重置時sw和sw_count歸零
        self.sw = 0
        self.sw_count = 0

        # 取消測試模式
        self.test_mode = 0

        # 重置閃燈
        self.lights_status = [0,0,0,0,0,0]

        # 重置洞口燈
        self.hole_lights = [0,0,0,0,0]

        # 沒用到的碰撞偵測
        self.cd = 0


# 主要起點
class ColaApp(App):

    # app 起點
    def on_start(self):

        # 排程執行 udate_mcp3008_value
        Clock.schedule_interval(self.update_mcp3008_value, mcp3008_Frequency)

        # 排程執行 light+blinky 改變第二個值可以改變呼叫週期
        Clock.schedule_interval(self.light_blinky, blink_Frequency)

    # 更新mcp3008數值
    def update_mcp3008_value(self, nap):

        # 呼叫 read_mcp3008取值
        values = read_mcp3008()

        # 讀可變電阻  五個變數是 1、 mcp3008的第一腳位讀值 2、類比讀值最小值 3、類比讀值最大值 4、舵機最小角 5、舵機最大角
        values[0] = translate(values[0], vr_min, vr_max, servo_min, servo_max)

        # 叫pca9685 讓舵機動 （第12pin）
        pwm.set_pwm(12, 0, int(values[0]))

        # values的[1]到[5]如果不在測試模式下才運作 gs.test_mode 為是否是測試模式
        if gs.test_mode == 0 and values[1] > analogy_toggle_point:
            gs.hole_lights[0] = 1

        if gs.test_mode == 0 and values[2] > analogy_toggle_point:
            gs.hole_lights[1] = 1

        if gs.test_mode == 0 and values[3] > analogy_toggle_point:
            gs.hole_lights[2] = 1

        if gs.test_mode == 0 and values[4] > analogy_toggle_point:
            gs.hole_lights[3] = 1

        if gs.test_mode == 0 and values[5] > analogy_toggle_point:
            gs.hole_lights[4] = 1

        # 觸發開關的條件
        if gs.test_mode == 0 and values[6] > analogy_toggle_point and gs.sw == 0:
            # 觸發後讓gs.sw = 1 （達成閃燈條件）
            gs.sw = 1
        elif gs.test_mode == 0 and values[6] < analogy_toggle_point and sw_mode == 1:
            # 如果sw_mode是1的時候，鬆開sw按鈕會停止閃燈
            gs.sw = 0

        # 碰撞觸發的條件 還沒指定要做什麼，只是改變文字狀態（應該是要讓gs.sw = 1)
        if gs.test_mode == 0 and values[7] > analogy_toggle_point:
            self.root.ids.collision_status.text = 'Collision detection'
        elif gs.test_mode == 0 and values[7] < analogy_toggle_point:
            self.root.ids.collision_status.text = 'No Collision detection'

        # 判斷 reset pin 狀態 預設是17 pin
        if GPIO.input(17):

            # 顯示 reset pin 狀態
            self.root.ids.reset_status.text = 'reset press'

            # reset的pin，執行重置函式（reset_on)
            self.reset_on()

        # 沒按到reset pin的時候維持顯示 no reset press
        elif GPIO.input(17) == 0:
            self.root.ids.reset_status.text = 'no reset press'

        # 配置mcp3008值到顯示的文字上
        self.root.ids.mcp0.text = str(int(values[0]))
        self.root.ids.mcp1.text = str(values[1])
        self.root.ids.mcp2.text = str(values[2])
        self.root.ids.mcp3.text = str(values[3])
        self.root.ids.mcp4.text = str(values[4])
        self.root.ids.mcp5.text = str(values[5])
        self.root.ids.mcp6.text = str(values[6])
        self.root.ids.mcp7.text = str(values[7])

        # 取 cpu 的值
        cpu_temp_raw_data = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_temp"])
        get_cpu_temp = cpu_temp_raw_data.strip()

        # 顯示cpu值至cputemp
        self.root.ids.cputemp.text = get_cpu_temp

        # 掃描light變數至硬體輸出
        self.light_scan()

        # 掃描hole變數至硬體輸出
        self.hole_scan()

        # 更新應對文字顯示資訊
        self.text_scan()

    # 閃燈函式 gs.sw = 1 才會 count
    # low_active 指定 pca9685 輸出值為high或low

    def light_scan(self):

        for i in range(6):
            if low_active == 1:
                if gs.lights_status[i] == 1:
                    pwm.set_pwm(i, 0, 0)
                else:
                    pwm.set_pwm(i, 0, 4095)
            if low_active == 0:
                if gs.lights_status[i] == 1:
                    pwm.set_pwm(i, 0, 4095)
                else:
                    pwm.set_pwm(i, 0, 0)

    # low_active 指定 pca9685 輸出值為high或low
    def hole_scan(self):

        for i in range(5):
            if low_active == 1:
                if gs.hole_lights[i] == 1:
                    pwm.set_pwm(i + 6, 0, 0)
                else:
                    pwm.set_pwm(i + 6, 0, 4095)
            else:
                if gs.hole_lights[i] == 1:
                    pwm.set_pwm(i + 6, 0, 4095)
                else:
                    pwm.set_pwm(i + 6, 0, 0)

    # 更新應對文字顯示資訊
    def text_scan(self):

        # 洞口燈掃描
        if gs.hole_lights[0] == 1:
            self.root.ids.H1.text = 'H1 on'
        else:
            self.root.ids.H1.text = 'H1 off'

        if gs.hole_lights[1] == 1:
            self.root.ids.H2.text = 'H2 on'
        else:
            self.root.ids.H2.text = 'H2 off'

        if gs.hole_lights[2] == 1:
            self.root.ids.H3.text = 'H3 on'
        else:
            self.root.ids.H3.text = 'H3 off'

        if gs.hole_lights[3] == 1:
            self.root.ids.H4.text = 'H4 on'
        else:
            self.root.ids.H4.text = 'H4 off'

        if gs.hole_lights[4] == 1:
            self.root.ids.H5.text = 'H5 on'
        else:
            self.root.ids.H5.text = 'H5 off'

        # 閃燈掃描
        if gs.lights_status[0] == 1:
            self.root.ids.L1.text = 'l1 On'
        else:
            self.root.ids.L1.text = 'l1 Off'
        if gs.lights_status[1] == 1:
            self.root.ids.L2.text = 'l2 On'
        else:
            self.root.ids.L2.text = 'l2 Off'
        if gs.lights_status[2] == 1:
            self.root.ids.L3.text = 'l3 On'
        else:
            self.root.ids.L3.text = 'l3 Off'
        if gs.lights_status[3] == 1:
            self.root.ids.L4.text = 'l4 On'
        else:
            self.root.ids.L4.text = 'l4 Off'
        if gs.lights_status[4] == 1:
            self.root.ids.L5.text = 'l5 On'
        else:
            self.root.ids.L5.text = 'l5 Off'
        if gs.lights_status[5] == 1:
            self.root.ids.L6.text = 'l6 On'
        else:
            self.root.ids.L6.text = 'l6 Off'

        # 顯示是否是測試模式
        if gs.test_mode == 1:
            self.root.ids.test_mode.text = 'TEST Mode'
        else:
            self.root.ids.test_mode.text = 'RUN Mode'

        # 顯示 gs.sw 狀態
        if gs.sw == 1:
            self.root.ids.gs_sw_status.text = 'GS SW Active'
        else:
            self.root.ids.gs_sw_status.text = 'GS SW no Active'

    # 閃燈陣列對付至硬體輸出的函式
    def light_blinky(self, nap):

        # gs.sw = 1的話開始計數
        if gs.sw == 1:
            gs.sw_count += 1

        # 不是測試模式時，sw為零時重置sw_count和lights_status的狀態（似乎可以和下面整合，加入todo）
        elif gs.test_mode == 0 and gs.sw == 0:
            gs.sw_count = 0
            gs.lights_status = [0,0,0,0,0,0]

        # sw_count_limit（count多少次才結束，也可以想成是閃燈時間）  在game_status的屬性 設定
        if gs.sw_count > sw_count_limit:
            gs.sw = 0
            gs.sw_count = 0
            gs.lights_status = [0,0,0,0,0,0]

        numrows = len(gs.light_set)         # 計算light_set的總行數

        rows = gs.sw_count % numrows        # 計算現在要顯示燈號陣列的行數 count對總行數取除數

        # 以下對應燈號和陣列 1是亮 0 是暗
        if gs.sw == 1 and gs.light_set[rows][0] == 1:
            gs.lights_status[0] = 1
        elif gs.sw == 1 and gs.light_set[rows][0] == 0:
            gs.lights_status[0] = 0

        if gs.sw == 1 and gs.light_set[rows][1] == 1:
            gs.lights_status[1] = 1
        elif gs.sw == 1 and gs.light_set[rows][1] == 0:
            gs.lights_status[1] = 0

        if gs.sw == 1 and gs.light_set[rows][2] == 1:
            gs.lights_status[2] = 1
        elif gs.sw == 1 and gs.light_set[rows][2] == 0:
            gs.lights_status[2] = 1

        if gs.sw == 1 and gs.light_set[rows][3] == 1:
            gs.lights_status[3] = 1
        elif gs.sw == 1 and gs.light_set[rows][3] == 0:
            gs.lights_status[3] = 0

        if gs.sw == 1 and gs.light_set[rows][4] == 1:
            gs.lights_status[4] = 1
        elif gs.sw == 1 and gs.light_set[rows][4] == 0:
            gs.lights_status[4] = 0

        if gs.sw == 1 and gs.light_set[rows][5] == 1:
            gs.lights_status[5] = 1
        elif gs.sw == 1 and gs.light_set[rows][5] == 0:

            gs.lights_status[5] = 0

    # 按鈕執行 switch on
    def switch_on(self):
        print('press switch on')
        gs.sw = 1

    # 按鈕執行switch off
    def switch_off(self):
        print('press switch off')
        gs.sw = 0

    # 按下reset的時候執行的
    def reset_on(self):
        print('reset on')
        gs.test_mode = 0            # 關閉測試模式
        gs.game_reset()             # 執行重置

    # all_light按鈕 → 全亮
    def all_light(self):
        gs.test_mode = 1
        gs.sw = 0

        for i in range(6):
            gs.lights_status[i] = 1

        for i in range(5):
            gs.hole_lights[i] = 1

    # all_close按鈕時執行
    def all_close(self):
        gs.test_mode = 1
        gs.sw = 0

        for i in range(6):
            gs.lights_status[i] = 0

        for i in range(5):
            gs.hole_lights[i] = 0

    # 測試模式用 l1 按鈕，以下類推
    def l1_press(self):

        if gs.test_mode == 1 and gs.lights_status[0] == 0:
            gs.lights_status[0] = 1
        elif gs.test_mode == 1 and gs.lights_status[0] == 1:
            gs.lights_status[0] = 0

    def l2_press(self):

        if gs.test_mode == 1 and gs.lights_status[1] == 0:
            gs.lights_status[1] = 1
        elif gs.test_mode == 1 and gs.lights_status[1] == 1:
            gs.lights_status[1] = 0

    def l3_press(self):

        if gs.test_mode == 1 and gs.lights_status[2] == 0:
            gs.lights_status[2] = 1
        elif gs.test_mode == 1 and gs.lights_status[2] == 1:
            gs.lights_status[2] = 0

    def l4_press(self):

        if gs.test_mode == 1 and gs.lights_status[3] == 0:
            gs.lights_status[3] = 1
        elif gs.test_mode == 1 and gs.lights_status[3] == 1:
            gs.lights_status[3] = 0

    def l5_press(self):

        if gs.test_mode == 1 and gs.lights_status[4] == 0:
            gs.lights_status[4] = 1
        elif gs.test_mode == 1 and gs.lights_status[4] == 1:
            gs.lights_status[4] = 0

    def l6_press(self):

        if gs.test_mode == 1 and gs.lights_status[5] == 0:
            gs.lights_status[5] = 1
        elif gs.test_mode == 1 and gs.lights_status[5] == 1:
            gs.lights_status[5] = 0

    # 測試模式用 h1 按鈕，以下類推
    def h1_press(self):

        if gs.test_mode == 1 and gs.hole_lights[0] == 0:
            gs.hole_lights[0] = 1
        elif gs.test_mode == 1 and gs.hole_lights[0] == 1:
            gs.hole_lights[0] = 0

    def h2_press(self):

        if gs.test_mode == 1 and gs.hole_lights[1] == 0:
            gs.hole_lights[1] = 1
        elif gs.test_mode == 1 and gs.hole_lights[1] == 1:
            gs.hole_lights[1] = 0

    def h3_press(self):

        if gs.test_mode == 1 and gs.hole_lights[2] == 0:
            gs.hole_lights[2] = 1
        elif gs.test_mode == 1 and gs.hole_lights[2] == 1:
            gs.hole_lights[2] = 0

    def h4_press(self):

        if gs.test_mode == 1 and gs.hole_lights[3] == 0:
            gs.hole_lights[3] = 1
        elif gs.test_mode == 1 and gs.hole_lights[3] == 1:
            gs.hole_lights[3] = 0

    def h5_press(self):

        if gs.test_mode == 1 and gs.hole_lights[4] == 0:
            gs.hole_lights[4] = 1
        elif gs.test_mode == 1 and gs.hole_lights[4] == 1:
            gs.hole_lights[4] = 0


class ColaLayout(BoxLayout):
    time_prop = ObjectProperty(None)


if __name__ == '__main__':
    gs = GameStatus()
    ColaApp().run()
