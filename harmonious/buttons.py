#from gpiozero import LED, Button
from time import sleep
from pythonosc import udp_client
from signal import pause
from liblo import *

class LightOSC(ServerThread):
    def __init__(self, port, led1, led2, led3, led4):
        ServerThread.__init__(self, port)
        self.leds = [led1, led2, led3, led4]
    
    @make_method(None, None)
    def handleMessage(self, path, args, types, src):
        print('message recieved: ', args)
        if path == '/light':
            ledon, ledoff = args[:2]
            self.leds[ledoff].off()
            self.leds[ledon].on()

sender = udp_client.SimpleUDPClient('127.0.0.1', 4559)

def make_toggle(tower_id, led=None):
    state = False
    def pressed():
        nonlocal state
        # perform the toggle
        state = not state
        print('button with tower id {i} is now {state}'.format(i=tower_id, state=state))
        sender.send_message('/button', [tower_id, 1 if state else 0])
        if led is not None:
            led.on() if state else led.off()
    
    return pressed, lambda: None

def make_push_button(tower_id, led=None):
    def pressed():
        print('button with tower id {i} was pressed'.format(i=tower_id))
        sender.send_message('/button', [tower_id, 1])
        if led is not None: led.on()
    
    def released():
        print('button with tower id {i} was released'.format(i=tower_id))
        sender.send_message('/button', [tower_id, 0])
        if led is not None: led.off()
    
    return pressed, released


class StubLED:
  def __init__(self, id):
    self.id = id
  
  def on(self):
    print(f"{self.id} was turned on")
  
  def off(self):
    print(f"{self.id} was turned off")

try:
    osc = LightOSC(3334, StubLED(1), StubLED(2), StubLED(3), StubLED(4))
    #osc = LightOSC(3334, LED(5), LED(6), LED(12), LED(13))
    osc.start()
except ServerError as err:
    sys.exit(err)
    
pause()
