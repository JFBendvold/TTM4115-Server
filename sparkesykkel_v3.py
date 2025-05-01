import numpy as np
from sense_hat import SenseHat
import time
from PIL import Image
import paho.mqtt.client as mqtt
import json
import os
# Wait for RPi to connect to WIFI
#time.sleep(20)
# Get current directory for images
cwd = os.path.dirname(os.path.realpath(__file__))
print(cwd)
# MQTT
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_COMMAND = 'ttm4115/team_18/command'
MQTT_TOPIC_STATUS = 'ttm4115/team_18/status'

s = SenseHat()
s.low_light = True

#Helper functions
G = (0, 255, 0) #green
Y = (255, 255, 0) #yellow
B = (0, 0, 255) #blue
R = (255, 0, 0) #red
W = (255,255,255) #white
O = (0,0,0) #nothing
P = (255,105, 180) #pink
PU = (128,0,128) #purple
X = W
scooter_colors = [G,Y,B,PU]

def get_index(column, row):
        return 8*row+column

class Numbergrid():
    one = [
    W, W, O, O,
    O, W, O, O,
    O, W, O, O,
    O, W, O, O
    ]

    two = [
    W, W, W, O,
    O, O, W, O,
    O, W, O, O,
    W, W, W, O
    ]

    three = [
    W, W, W, O,
    O, O, W, O,
    O, W, W, O,
    W, W, W, O
    ]

    four = [
    W, O, W, O,
    W, O, W, O,
    W, W, W, O,
    O, O, W, O
    ]

class Scooter_state:
    MISPARKED = False
    MUST_MOVE = False
    RESERVED = False

class Scooter:
    def __init__(self, id):
        self.id = id
        self.states = Scooter_state()
        self.color = scooter_colors[id]
        self.led_indices = np.arange(get_index(0,id),get_index(8,id))
        self.leds = [False]*8
        self.set_init_leds()
        self.img = ""
    
    def update_status(self, value):
        if value == "MISPARKED":
            self.set_missparked()
        elif value == "MUST_MOVE":
            self.set_must_move()
        elif value == "RESERVED":
            self.set_reserved()
        else:
            print("Unknown status")

    def disable_status(self, value):
        if value == "MISPARKED":
            self.disable_missparked()
        elif value == "MUST_MOVE":
            self.disable_must_move()
        elif value == "RESERVED":
            self.disable_reserved()
        else:
            print("Unknown status")

    def get_img_path(self):
        return self.img
    
    def set_img_path(self, path):
        self.img = path

    def set_init_leds(self):
        self.leds[0] = None
        for l in range(4,8):
          self.leds[l] = W
    
    def get_id(self):
      return self.id
    
    def get_led_indices(self):
        return self.led_indices
    
    def get_leds(self):
        return self.leds
    
    def update_leds(self):
        self.leds[1] = self.states.MISPARKED
        self.leds[2] = self.states.MUST_MOVE
        self.leds[3] = self.states.RESERVED
    
    def toggle_missparked(self):
        self.states.MISPARKED = True
        self.update_leds()
        if self.states.MISPARKED:
          msg = {}
          msg["s" + str(self.get_id())] = "MISPARKED"
          mqtt_client.publish(MQTT_TOPIC_COMMAND, json.dumps(msg))
    def toggle_must_move(self):
        self.states.MUST_MOVE = True
        self.update_leds()
        if self.states.MUST_MOVE:
          msg = {}
          msg["s" + str(self.get_id())] = "MUST_MOVE"
          mqtt_client.publish(MQTT_TOPIC_COMMAND, json.dumps(msg))

    def toggle_reserved(self):
        self.states.RESERVED = True
        self.update_leds()
        if self.states.RESERVED:
          msg = {}
          msg["s" + str(self.get_id())] = "RESERVED"
          mqtt_client.publish(MQTT_TOPIC_COMMAND, json.dumps(msg))

    def set_missparked(self):
        self.states.MISPARKED = True
        #self.states.MUST_MOVE = False
        #self.states.RESERVED = False
        self.update_leds()
    def set_must_move(self):
        self.states.MUST_MOVE = True
        #self.states.MISPARKED = False
        #self.states.RESERVED = False
        self.update_leds()
    def set_reserved(self):
        self.states.RESERVED = True
        #self.states.MISPARKED = False
        #self.states.MUST_MOVE = False
        self.update_leds()

    def disable_missparked(self):
        self.states.MISPARKED = False
        self.update_leds()
    def disable_must_move(self):
        self.states.MUST_MOVE = False
        self.update_leds()
    def disable_reserved(self):
        self.states.RESERVED = False
        self.update_leds()

class Matrix():
    def __init__(self, scooters):
        self.led_matrix = [O]*(8*8)
        self.scooters = scooters
        self.current_scooter = self.scooters[0]
        self.current_state_column = 1
        self.update_grid()

    def get_status_all(self):
        msg = {"command" : "get_status_all"}
        mqtt_client.publish(MQTT_TOPIC_COMMAND, json.dumps(msg))
        print("Requesting Status (ALL)") 
    def get_scooter_status(self):

        msg = {}
        for scooter in matrix.scooters:
            true_values = []
            if scooter.states.MISPARKED:
                true_values.append("MISPARKED")
            if scooter.states.MUST_MOVE:
                true_values.append("MUST_MOVE")
            if scooter.states.RESERVED:
                true_values.append("RESERVED")
            msg["s"+str(scooter.get_id())] = (true_values)
        return msg

    def set_led_matrix(self, pixels):
        if len(pixels) != 64:
            raise ValueError("Pixel list must contain exactly 64 values (8x8 matrix).")
        self.led_matrix = pixels

    def update_grid(self, s0=None, s1=None, s2=None, s3=None):
        for scooter in self.scooters:
            #print(scooter.get_led_indices())
            i = 0
            for index in scooter.get_led_indices():
                if scooter.get_leds()[i] == True:
                    self.led_matrix[index] = G
                elif scooter.get_leds()[i] == False:
                    self.led_matrix[index] = R
                elif scooter.get_leds()[i] == None:
                    self.led_matrix[index] = scooter.color
                else:
                    self.led_matrix[index] = O
                i+=1

        self.draw_number(self.current_scooter.get_id())
        self.draw_battery(self.current_scooter.get_id())

    def toggle_leds_off(self):
        self.led_matrix[get_index(0,self.current_scooter.get_id())] = O
        self.led_matrix[get_index(self.current_state_column,self.current_scooter.get_id())] = O

    def toggle_leds_on(self):
        self.update_grid()
    
    def get_led_matrix(self):
        return self.led_matrix
    
    def print_matrix(self):
        for i in range(8):
            print(self.led_matrix[i*8:i*8+8])
    
    def current_state_column_increment(self):
        self.current_state_column+=1
        if self.current_state_column == 4:
            self.current_state_column = 1
    
    def current_scooter_increment(self):
        self.current_state_column = 1
        if self.current_scooter.get_id() == 3:
            self.current_scooter = self.scooters[0]
        else:
            self.current_scooter=self.scooters[self.current_scooter.get_id()+1]
      
    def current_state_column_decrement(self):
        self.current_state_column-=1
        if self.current_state_column == 0:
            self.current_state_column = 3
    
    def current_scooter_decrement(self):
        self.current_state_column = 1
        if self.current_scooter.get_id() == 0:
            self.current_scooter = self.scooters[3]
        else:
            self.current_scooter=self.scooters[self.current_scooter.get_id()-1]
    
    def draw_number(self, number):
        number_grid = Numbergrid()
        for i in range(4):
            for j in range(3):
                if number == 0:
                    self.led_matrix[get_index(j+5,i)] = number_grid.one[4*i+j]
                elif number == 1:
                    self.led_matrix[get_index(j+5,i)] = number_grid.two[4*i+j]
                elif number == 2:    
                    self.led_matrix[get_index(j+5,i)] = number_grid.three[4*i+j]
                elif number == 3:
                    self.led_matrix[get_index(j+5,i)] = number_grid.four[4*i+j]
    
    def draw_battery(self, number):
        # Load image and resize to 8x8
        img = Image.open(self.current_scooter.get_img_path()).resize((8, 8)).convert('RGB')
        pixels = list(img.getdata())

        # Extract bottom 4 rows from image (rows 4 to 7)
        image_bottom = []
        for row in range(4, 8):  # rows 4,5,6,7
            start = row * 8
            end = start + 8
            image_bottom.extend(pixels[start:end])

        # Create or use your matrix object

        matrix_top = self.get_led_matrix()[0:32]  # First 4 rows: 4*8 = 32 pixels

        # Combine top from matrix + bottom from image
        final_pixels = matrix_top + image_bottom
        # Show it on Sense HAT
        self.set_led_matrix(final_pixels)

s0 = Scooter(0)
s1 = Scooter(1)
s2 = Scooter(2)
s3 = Scooter(3)
s0.set_img_path(f"{cwd}/batterylow.png")
s1.set_img_path(f"{cwd}/batteryhigh.png")
s2.set_img_path(f"{cwd}/batterymed.png")
s3.set_img_path(f"{cwd}/batterydead.png")
matrix = Matrix([s0,s1,s2,s3])

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe(MQTT_TOPIC_STATUS)

def on_message(mqtt_client, userdata, msg):
    try:
            payload = json.loads(msg.payload.decode('utf-8'))
            print(payload)
            if not payload:
                print("test")
                s0.disable_missparked()
                s1.disable_missparked()
                s2.disable_missparked()
                s3.disable_missparked()
                s0.disable_must_move()
                s1.disable_must_move()
                s2.disable_must_move()
                s3.disable_must_move()
                s0.disable_reserved()
                s1.disable_reserved()
            
                s2.disable_reserved()
                s3.disable_reserved()
            
            for (key, value) in payload.items():
                  missing_values = []
                  expected_values = ["MISPARKED","MUST_MOVE","RESERVED"]
                  missing_values = [val for val in expected_values if val not in value]
                  if not value:
                      if key == "s0":
                          s0.disable_must_move()
                          s0.disable_missparked()
                          s0.disable_reserved()
                      elif key == "s1":
                          s1.disable_must_move()
                          s1.disable_missparked()
                          s1.disable_reserved()    
                      elif key == "s2":
                          s2.disable_must_move()
                          s2.disable_missparked()
                          s2.disable_reserved()    
                      elif key == "s3":
                          s3.disable_must_move()
                          s3.disable_missparked()
                          s3.disable_reserved()    
                  for e in value:
                      
                    if key == "s0":
                        for missing in missing_values:
                            s0.disable_status(missing)
                        s0.update_status(e)
                    elif key == "s1":
                        for missing in missing_values: 
                            s1.disable_status(missing)
                        s1.update_status(e)
                    elif key == "s2":   
                        for missing in missing_values: 
                            s2.disable_status(missing)
                        s2.update_status(e)
                    elif key == "s3":
                        for missing in missing_values: 
                            s3.disable_status(missing)
                        s3.update_status(e)
            

            print("Received MQTT Payload")
    except Exception as e:
            print(f"Failed to process message: {e}")
    finally:
        test = matrix.get_scooter_status()

def on_connect(client, userdata, flags, rc):
        # we just log that we are connected
        print('MQTT connected to {}'.format(client))


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_start()
matrix.get_status_all()
while True:
    matrix.toggle_leds_off()
    s.set_pixels(matrix.get_led_matrix())
    time.sleep(.2)
    matrix.toggle_leds_on()
    s.set_pixels(matrix.get_led_matrix())
    time.sleep(.2)
    
    for event in s.stick.get_events():
        if event.direction == "right" and event.action == "pressed":
            matrix.current_state_column_increment()
        elif event.direction == "down" and event.action == "pressed":
            matrix.current_scooter_increment()
        elif event.direction == "left" and event.action == "pressed":
            matrix.current_state_column_decrement()
            matrix.get_status_all()
        elif event.direction == "up" and event.action == "pressed":
            matrix.current_scooter_decrement()
        elif event.direction == "middle" and event.action == "pressed":
            if matrix.current_state_column == 1:
                matrix.current_scooter.toggle_missparked()
                matrix.current_scooter.toggle_must_move()
            elif matrix.current_state_column == 2:
                matrix.current_scooter.toggle_must_move()
                matrix.current_scooter.toggle_missparked()
            elif matrix.current_state_column == 3:
                matrix.current_scooter.toggle_reserved()
