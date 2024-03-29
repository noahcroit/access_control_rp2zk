from machine import Pin
from machine import ADC
from machine import PWM
import time



# Constants for SecureDoor Class
STATE_IDLE   = const("IDLE")
STATE_LASTWILL = const("LASTWILL")
STATE_ACTIVE = const("ACTIVE")
STATE_EMERG  = const("EMERG")
IO_NUM_OUTAGE = const(3)
IO_NUM_CHARGER = const(4)
IO_NUM_LOCK = const(5)
IO_NUM_DOORSTATE = const(2)
IO_NUM_EXITBUTTON = const(22)
IO_NUM_BATT = const(26)
IO_NUM_BUZZER = const(18)
V_BATT_FULL = const(13.0)
V_BATT_LOW  = const(12.0)



class SecureDoor:
    def __init__(self, deepsleep=False, lastwill_cb=None):
        self.state = STATE_IDLE
        self.pin_outage = Pin(IO_NUM_OUTAGE, Pin.IN, Pin.PULL_UP)
        self.pin_lock   = Pin(IO_NUM_LOCK, Pin.OUT)
        self.pin_doorstate = Pin(IO_NUM_DOORSTATE, Pin.IN, Pin.PULL_UP)
        self.pin_exitbutton = Pin(IO_NUM_EXITBUTTON, Pin.IN, Pin.PULL_UP)
        self.pin_batt = Pin(IO_NUM_BATT, Pin.IN)
        self.adc_batt = ADC(self.pin_batt)
        self.pin_charger = Pin(IO_NUM_CHARGER, Pin.OUT)
        self.pin_buzzer = Pin(IO_NUM_BUZZER, Pin.OUT)
        self.exit_cnt = 0
        self.buzzer_cnt = 0
        self.buzzer_stop = False
        self.q_exit = []
        self.deepsleep=deepsleep
        self.lastwill_cb = lastwill_cb

    def hwinit(self):
        self.lockDisable()
        self.chargerDisable()
        self.pin_buzzer.value(0)
        self.pin_exitbutton.irq(trigger=Pin.IRQ_FALLING, handler=self.callback_exitbutton)

    def getState(self):
        return self.state

    def isOutageOccur(self):
        return bool(self.pin_outage.value())

    def isDoorOpen(self):
        return bool(self.pin_doorstate.value())

    def isExitButtonPressed(self):
        return not self.pin_exitbutton.value()

    def lockEnable(self):
        self.pin_lock.value(0)
        print("lock activated")

    def lockDisable(self):
        self.pin_lock.value(1)
        print("lock deactivated")

    def buzzerEnable(self):
        self.pwm_buzzer = PWM(self.pin_buzzer)
        self.pwm_buzzer.duty_u16(20000)
        self.pwm_buzzer.freq(500)

    def buzzerDisable(self):
        self.pwm_buzzer.deinit()
        self.pin_buzzer.value(0)

    def chargerEnable(self):
        self.pin_charger.value(0)
        print("charger activated")

    def chargerDisable(self):
        self.pin_charger.value(1)
        print("charger activated")

    def getVbatt(self, mcu_vref=3.3, divider_ratio=5.2):
        v_batt = self.adc_batt.read_u16() * mcu_vref / 65535 * divider_ratio
        return v_batt

    def isChargerActivated(self):
        val = self.pin_charger.value()
        return not val

    def chargerCheckRoutine(self):
        v_batt = self.getVbatt()
        print("v_batt=", v_batt)
        if v_batt > V_BATT_FULL:
            self.chargerDisable()
        elif v_batt <= V_BATT_LOW:
            self.chargerEnable()

    def step(self):
        # Run state machine of door lock by step.
        # This function needs to be called every cycle of main loop.

        # Get current state
        state_current = self.state
        state_next = state_current

        # State transition
        if state_current == STATE_IDLE:
            print("step, current state : IDLE")
            # monitor outage
            if self.isOutageOccur():
                self.chargerDisable()
                self.lockEnable()
                self.buzzerEnable()
                self.buzzer_cnt = 20
                self.buzzer_stop = False
                self.pin_exitbutton.irq(trigger=Pin.IRQ_FALLING, handler=self.callback_exitbutton)
                self.q_ext = []
                self.state = STATE_LASTWILL
                if self.lastwill_cb is not None:
                    self.lastwill_cb()
                state_next = STATE_ACTIVE

            else:
                # charger management
                self.chargerCheckRoutine()

                # exit button (in case when door is locked remotely)
                if self.q_exit:
                    self.q_exit.pop()
                    self.lockDisable()

        elif state_current == STATE_ACTIVE:
            print("step, current state : ACTIVE")
            # monitor outage
            if not self.isOutageOccur():
                self.lockDisable()
                self.buzzerDisable()
                state_next = STATE_IDLE
            else:
                # monitor the exit button
                if self.q_exit:
                    self.q_exit.pop()
                    self.lockDisable()
                    self.exit_cnt = 10
                if self.exit_cnt > 0:
                    self.exit_cnt -= 1
                    if self.exit_cnt == 0:
                        self.lockEnable()

                # check buzzer
                if not self.buzzer_stop:
                    if self.buzzer_cnt <= 0:
                        for i in range(8):
                            self.buzzerEnable()
                            time.sleep(0.3)
                            self.buzzerDisable()
                            time.sleep(0.3)
                        self.buzzer_stop = True
                    else:
                        self.buzzer_cnt -= 1

        elif state_current == STATE_EMERG:
            print("step, current state : EMERGENCY")

        # Update state
        self.state = state_next

    def callback_exitbutton(self, pin):
        self.q_exit.append('exit')
        print("exit button is pressed!")


