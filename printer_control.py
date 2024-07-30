from printrun.printcore import printcore
from printrun import gcoder
import time
import io
import threading

from pneumatic_control import Pneumatic

class Printer():
    def __init__(self,pneumatic):
        
        self.pneumatic=pneumatic

        self.flag=0
        self.depose=0
        self.p=None
        self.current_response=""
        self.gcode_lines=""
        self.homed=0
        self.speed=500 #printing speed, 
        self.z=1 #printing height
        

        #substrat infos
        self.ydist=15 #start y position for substrat test 
        self.line=self.ydist #moving y position to draw lines 1 by 1
        #self.xsize=120 
        #sample_space=30
        self.sample_size_x=70
        self.sample_size_y=120
        self.line_space=10
        self.x_space_on_borders=5#space left without print when testing lines on each side
        self.sub=6 #height of the substrat, 0 if no substrat


        #safety values
        self.min_z=0.1#[mm]
        self.max_z=20
        self.min_sub=0
        self.max_sub=50
        self.min_speed=500
        self.max_speed=15000
        self.bed_max_y=250#check max safe value
        self.bed_max_x=210
        self.z_offset=1.3#it's negativ her, difference with the 0 of the printer 


        self.stop=0
        self.on_going_print=0 #active for any print including small test and line
        self.multilayer_print=0#active only when a g-code is uploaded and sent
        self.go_next_layer=0#changed by a timer or user input
        #self.self.pneumatic=None
        self.mutex=threading.Lock()

        self.pile_gcode = []
        #self.pile_pneumatic=[]
        self.pile_change_layer=[]
        self.pile_depose=[]
        self.pile_depose.append(0)
        self.thread_state=1
        self.wait_minutes=60
        #self.t_gcode= threading.Thread(target=self.send_gcode_routine)
        #self.t_gcode.start()
    
    def kill_thread(self):
        print("we killed the thread")
        self.thread_state=0
        #self.t_gcode.join()
    
    def send_gcode_routine(self):

        while True:
            if not self.thread_state:
                break

            if not self.stop:
                self.pile_gcode=[]
                self.pile_change_layer=[]
                self.pile_depose=[]
                #empty every array to do something else
            
            if self.pile_gcode!=[]:
                self.go_next_layer=0
                if not self.on_going_print:
                    self.on_going_print=1
                
                self.mutex.acquire()
                try:
                    #send new orders
                    
                    depose=self.pile_depose[0] #update pneumatic state
                    change_layer=self.pile_change_layer[0]
                    self.update(1,depose)
                    layer=self.pile_gcode[0]

                    while layer!=[]:
                        if not self.stop:
                                continue
                        self.p.send_now(layer[0])  #send to printer
                        layer.pop(0)

                        while self.flag!=1:
                            if not self.thread_state:
                                break
                            if not self.stop:
                                continue
                            time.sleep(0.1)#needed to let the GUI update
                    
                        self.flag=0

                    #clean what you just sent
                    self.pile_gcode.pop(0)
                    self.pile_change_layer.pop(0)
                    self.pile_depose.pop(0)

                    #print("we sent the orders")
                finally:
                    self.mutex.release()
                    if change_layer:
                        print("waiting for next layer order")
                        self.p.send_now("G91")#change to relativ coordinate
                        self.p.send_now("G1 Z3")#go up 3mm in z to let dry in peace

                        total_wait_time = self.wait_minutes * 60#self.wait_minutes given by user input
                        elapsed_time = 0
                        interval = 0.5
                        while self.go_next_layer == 0 and elapsed_time < total_wait_time:
                            if not self.thread_state:  # Check if user quit
                                break
                            if not self.stop:
                                continue
                            time.sleep(interval)
                            elapsed_time += interval

                        self.p.send_now("G1 Z-3")#go back 3mm lower
                        self.p.send_now("G90")#back to absolute coordinate
                        self.go_next_layer=0
            else:
                if self.on_going_print:
                    self.on_going_print=0
                
                if self.multilayer_print:
                    self.multilayer_print=0
            time.sleep(0.1)#needed to let the GUI update

        
    
    def add_to_pile(self,print_data):
        
        # Mettre un mutex sur PILE
        self.mutex.acquire()
        try:
            self.pile_gcode.append(print_data[0])
            self.pile_depose.append(print_data[1])
            self.pile_change_layer.append(print_data[2])
            #print("we added to the pile")
        finally:
            self.mutex.release()
        # Libere le mutex sur PILE
        return 0


    def response_callback(self,line):
        current_response = line
        #print(f"Received: {line}")
        if "ok" in line:
            #print(f"Received: {line}")
            self.flag+=1

    
    def update(self,state, depose):

        if depose==0:
            #turn off the buse, keep cart on to stablize pressure, cut ato or it blow everything away
            self.pneumatic.st_Ato=0
            self.pneumatic.st_cart=0
            self.pneumatic.st_point=0
        else: 
           
            self.pneumatic.st_Ato=1
            self.pneumatic.st_cart=1
            self.pneumatic.st_point=1

        if not state:
            #state is 0 when we turn off the GUI
            self.pneumatic.st_Ato=0
            self.pneumatic.st_cart=0
            self.pneumatic.st_point=0
            self.pneumatic.c_ato=0
            self.pneumatic.c_cart=0
        
        self.pneumatic.sendToClient(state) #send the orders to pneumatic with the above updates

    def get_line_and_modify(self):
        depose = 0
        new_layer = 0
        layer=[]
        self.flag=0
        self.stop=0
        change_layer=0

        self.pneumatic.sendToClient(1)#should turn on the pressure but depose is at 0 so nothing else

        for data in self.gcode_lines:

            if data.startswith(';AFTER_LAYER_CHANGE'):#after layer change is when the extruder is off
                change_layer=1

            modified_line = data.split(';')[0]
            #to block homing, hotend temperature, comment, intro line (intro line can be deleted from slicer directly, here is just a security)
            if (data.startswith('M862') or data.startswith('M104')or 
                data.startswith('M109') or data.startswith('\n') or
                data.startswith('G28') or data.startswith(';') or 
                data.startswith('G80') or data.startswith('G1 Z0.2 F720')or 
                data.endswith('G1 Z0.3 F720') or
                data.endswith('go outside print area') or data.endswith('intro line')):
                continue
            elif data.startswith('G1'):
                if 'E' in data:
                    try:
                        E_value = float(data.split('E')[1].split()[0])
                    except (IndexError, ValueError):
                        E_value = None

                    if E_value is not None:
                        if E_value > 0 and depose==0:
                            new_layer=1
                            depose=1
                        elif E_value <= 0 and depose==1:
                            new_layer=1
                            depose=0
                        #normalement il n'y a pas de cas ou le E a juse pas de chiffre pour le stopper mais à verifier
                    
                    
            if not new_layer:
                #still working on the same layer, no need to change the pneumatic
                layer.append(modified_line)
                
            else:
                #new layer, pneumatic will have to change (turn on or off)
                layer.append("M400")
                print_data=[layer,depose, change_layer]
                #print(print_data)
                self.add_to_pile(print_data)
                layer = []
                layer.append(modified_line)
                new_layer=0
                change_layer=0

                

        layer.append("M400")
        print_data=[layer,depose,change_layer]
        self.add_to_pile(print_data)
        #print(print_data)
        return

    def stop_print(self):
        self.stop=1

    def load_gcode(self, path):
        # Load the G-code file
        with open(path, 'r') as file_object:
            self.gcode_lines = file_object.readlines()
        
        return
    
    def next_position(self):
        if self.line<(self.bed_max_y-self.line_space):
            self.line+=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.bed_max_x- self.sample_size_x)+ " Y"+str(self.line)+" F1000.000")

    def prev_position(self):
        if self.line>(self.ydist +self.line_space):
            self.line-=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.bed_max_x- self.sample_size_x)+ " Y"+str(self.line)+" F1000.000")

    def print_line(self):
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-self.z_offset#with the current system the nozle is 1.3mm higher 

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders)+ " Y"+str(self.line) +" F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.bed_max_x-self.x_space_on_borders) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x)+ " Y"+str(self.line)+" F5000.000"
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    
    def test_sample(self):
        ydist=self.ydist
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-self.z_offset#with the current system the nozle is 1mm higher 
            

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            for i in range(0,10):
                gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders)+ " Y"+ str(ydist) + " F1000.000"+ "\n"
                gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
                gcode_string=gcode_string +"G1 X "+str(self.bed_max_x-self.x_space_on_borders) + " E22.4 F"+str(self.speed)+ "\n"
                gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
                gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
                if i%2==1:
                        ydist+=2.5 #there is 2.5 mm space between each different texture on the tested sample
                ydist+=self.line_space
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x-20)+ " Y"+ str(ydist) + " F1000.000"+ "\n" #move out so i can take a pricture
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    

    #fct pour faire une petite plaque 
    def test__full_rectangle(self):
        ydist=self.line #will start the print depending on the current y position
        ywidth=10 #width of the rect
        width_depose=1
        cnt=int((ywidth/width_depose)/2)

        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-self.z_offset#with the current system the nozle is 1.3mm higher 
            
            
            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders)+ " Y"+ str(ydist) + " F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.bed_max_x-self.x_space_on_borders) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 Y"+ str(ydist+ywidth) +"\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders-width_depose)+ "\n"
            for i in range (1,cnt+1):
                gcode_string=gcode_string +"G1 Y"+ str(ydist+i*width_depose)+"\n"
                gcode_string=gcode_string +"G1 X "+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders + self.sample_size_x-i*width_depose)+"\n"
                gcode_string=gcode_string +"G1 Y"+ str(ydist+ywidth-i*width_depose) +"\n"
                gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders+i*width_depose)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x-20)+ " Y"+ str(ydist) + " F1000.000"+ "\n" #move out so i can take a picture
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    def homing(self):
        self.p.send_now("G28 W")
        self.p.send_now("G1 Z10") 
        self.homed=1

    def connect(self):
        # Start communication with the printer
        #self.p = printcore('/dev/ttyACM0', 115200)
        self.flag = 0
        # Set the response callback
        #self.p.loud = True
        #self.p.recvcb = self.response_callback

        # Wait until the printer is connected
        #while not self.p.online:
            #time.sleep(0.1)
        
        #self.homing()
        return 