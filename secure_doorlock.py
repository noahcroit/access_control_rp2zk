from machine import Pin
from machine import ADC
import time



# Constants for SecureDoor Class
STATE_IDLE   = const("IDLE")
STATE_ACTIVE = const("ACTIVE")
STATE_EMERG  = const("EMERG")
IO_NUM_OUTAGE = const(3)
IO_NUM_CHARGER = const(4)
IO_NUM_LOCK = const(5)
IO_NUM_DOORSTATE = const(6)
IO_NUM_EXITBUTTON = const(22)
IO_NUM_BATT = const(26)
V_BATT_FULL = const(13.0)
V_BATT_LOW  = const(11.0)

class SecureDoor:
    def __init__(self):
        self.state = STATE_IDLE
        self.state_charger = STATE_IDLE
        self.pin_outage = Pin(IO_NUM_OUTAGE, Pin.IN, Pin.PULL_UP)
        self.pin_lock   = Pin(IO_NUM_LOCK, Pin.OUT)
        self.pin_doorstate = Pin(IO_NUM_DOORSTATE, Pin.IN, Pin.PULL_UP)
        self.pin_exitbutton = Pin(IO_NUM_EXITBUTTON, Pin.IN, Pin.PULL_UP)
        self.pin_batt = Pin(IO_NUM_BATT, Pin.IN)
        self.adc_batt = ADC(self.pin_batt)
        self.pin_charger = Pin(IO_NUM_CHARGER, Pin.OUT)
        self.exit_cnt = 0
        self.q_exit = []

    def hwinit(self):
        self.lockDisable()
        self.chargerDisable()

    def getState(self):
        return self.state

    def isOutageOccur(self):
        return self.pin_outage.value()

    def isDoorLock(self):
        return not self.pin_doorstate.value()

    def isExitButtonPressed(self):
        return not self.pin_exitbutton.value()

    def lockEnable(self):
        self.pin_lock.value(0)
        print("lock activated")

    def lockDisable(self):
        self.pin_lock.value(1)
        print("lock deactivated")

    def chargerEnable(self):
        self.pin_charger.value(0)
        print("charger activated")

    def chargerDisable(self):
        self.pin_charger.value(1)
        print("charger activated")

    def getVbatt(self, mcu_vref=3.3, divider_ratio=5.2):
        v_batt = self.adc_batt.read_u16() * mcu_vref / 65535 * divider_ratio
        return v_batt

    def getChargerState(self):
        return self.state_charger

    def chargerCheckRoutine(self):
        v_batt = self.getVbatt()
        print("v_batt=", v_batt)
        if v_batt > V_BATT_FULL:
            self.chargerDisable()
            self.state_charger = STATE_IDLE
        elif v_batt <= V_BATT_LOW:
            self.chargerEnable()
            self.state_charger = STATE_ACTIVE

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
                self.pin_exitbutton.irq(trigger=Pin.IRQ_FALLING, handler=self.callback_exitbutton)
                state_next = STATE_ACTIVE
            else:
                # charger management
                self.chargerCheckRoutine()

            # sleep for 10 sec (low power)
            # cannot use deep sleep
            time.sleep(10)

        elif state_current == STATE_ACTIVE:
            print("step, current state : ACTIVE")
            # monitor outage
            if not self.isOutageOccur():
                self.lockDisable()
                self.pin_exitbutton.irq(handler=None)
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

            # normal sleep for 1 sec (active)
            time.sleep(1)

        elif state_current == STATE_EMERG:
            print("step, current state : EMERGENCY")

            # normal sleep for 1 sec (active)
            time.sleep(1)

        # Update state
        self.state = state_next

    def callback_exitbutton(self, pin):
        self.q_exit.append('exit')
        print("exit button is pressed!")


