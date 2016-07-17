# servo seeting
from __future__ import division
import time
import Adafruit_PCA9685 as servo

# import SPI Libery:MCP 3008
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008 as LR

# Servo : IC2 = 0x40
pwm = servo.PCA9685()

# SPI cnfige
CLK = 11
MISO = 9
MOSI = 10
CS = 8
mcp = LR.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
# Hardware SPI configuration:
# SPI_PORT   = 0
# SPI_DEVICE = 0
# mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# ---------------------------------------------------------------------

## Alternatively specify a different address and/or bus:
# pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)
servo_min = 130  # min Pulse length out of 4096
servo_max = 600  # max Pulse length out of 4096
pwm.set_pwm_freq(60)  # Set frequency to 60hz, good for servos.

"""
# Helper function to make setting a servo pulse width simpler.
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)
"""

print('Reading MCP3008 values, press Ctrl-C to quit....')
# print channel..
print('| {0:>4} | '.format(*range(1)))
print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
print('-' * 57)

while True:  # Main Program loop.
    # Read all the ADC channel values in a list
    values = [0] * 8
    # print (values) #try
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        # values[i] = mcp.read_adc(i)
        values[0] = (mcp.read_adc(0) - 396) * (470.0 / 627.0) + 130.0
        values[1] = (mcp.read_adc(1) - 50) * (470.0 / 850) + 130
        # print the ADC Values.
        print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))

    pwm.set_pwm(0, 0, int(values[0]))  # servo..LR
    pwm.set_pwm(3, 0, int(values[1]))  # servo..LR
    time.sleep(0.1)
"""
while True:
    pwm.set_pwm(0,0,servo_min)
    time.sleep(1)
    pwm.set_pwm(0,0,servo_max)
    time.sleep(1)
"""
