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
        self.speed=4000 #printing speed, keep g-code info if 0
        self.z=1 #printing height, keep the g-code info if 0
        

        #substrat infos
        self.ydist=15 #changing in the for loop, start y position
        self.line=self.ydist#y position of the test line
        self.xdist=120
        #sample_space=30
        self.sample_size=70
        self.line_space=10
        self.sub=0 #height of the substrat, 0 if no substrat


        #safety values
        self.min_z=0.1#[mm]
        self.max_z=20
        self.min_sub=0
        self.max_sub=50
        self.min_speed=500
        self.max_speed=15000
        self.bed_max_y=180#check max safe value
        self.bed_max_x=160


        #self.pause=0
        self.on_going_print=0 #active for any print including small test and line
        self.multilayer_print=0#active only when a g-code is uploaded and sent
        self.go_next_layer=0#changed by a timer or user input
        self.drying_time=42#we can put a max at 59 minutes or it will be decided by the user
        #self.self.pneumatic=None
        self.mutex=threading.Lock()

        self.pile_gcode = []
        #self.pile_pneumatic=[]
        self.pile_count=[]
        self.pile_depose=[]
        self.pile_depose.append(0)
        self.thread_state=1
        self.t_gcode= threading.Thread(target=self.send_gcode_routine)
        self.t_gcode.start()
    
    def kill_thread(self):
        print("we killed the thread")
        self.thread_state=0
        #self.t_gcode.join()
    
    def send_gcode_routine(self):

        while True:
            if not self.thread_state:
                break
            
            if self.pile_gcode!=[]:
                self.go_next_layer=0
                if not self.on_going_print:
                    self.on_going_print=1
                
                self.mutex.acquire()
                try:
                    #send new orders
                    
                    depose=self.pile_depose[0] #update pneumatic state
                    self.update(1,depose)
                    #layer_count=self.pile_count[0]+1
                    layer=self.pile_gcode[0]

                    while layer!=[]:
                        self.p.send_now(layer[0])  #send to printer
                        layer.pop(0)

                        while self.flag!=1:
                            if not self.thread_state:
                                break
                            time.sleep(0.1)#needed to let the GUI update
                    
                        self.flag=0

                    #clean what you just sent
                    self.pile_gcode.pop(0)
                    self.pile_count.pop(0)
                    self.pile_depose.pop(0)

                    #print("we sent the orders")
                finally:
                    self.mutex.release()
                    if self.multilayer_print!=0 and not depose:
                        while self.go_next_layer!=0:
                            #time.sleep()#we can maybe just put inside the number of minutes in a time.sleep
                            time.sleep(0.5)
                # Libere le mutex sur PILE
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
            self.pile_count.append(print_data[2])
            print("we added to the pile")
        finally:
            self.mutex.release()
        # Libere le mutex sur PILE
        return 0


    def response_callback(self,line):
        current_response = line
        #print(f"Received: {line}")
        if "ok" in line:
            print(f"Received: {line}")
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
        count=0
        self.flag=0
        self.pause=0

        self.pneumatic.sendToClient(1)#should turn on the pressure but depose is at 0 so nothing else

        for data in self.gcode_lines:
            modified_line = data.split(';')[0]

            if (data.startswith('M140') or data.startswith('M862') or 
                data.startswith('M104') or data.startswith('M190') or 
                data.startswith('M109') or data.startswith('\n') or
                data.startswith('G28')):
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
                count+=1
                
            else:
                #new layer, pneumatic will have to change (turn on or off)
                layer.append("M400")
                print_data=[layer,depose, count]
                print(print_data)
                self.add_to_pile(print_data)
                layer = []
                layer.append(modified_line)
                new_layer=0
                count=1
                

        layer.append("M400")
        print_data=[layer,depose,count]
        self.add_to_pile(print_data)
        print(print_data)
        return

    def load_gcode(self, path):
        # Load the G-code file
        with open(path, 'r') as file_object:
            self.gcode_lines = file_object.readlines()
        
        return
    
    def next_position(self):
        if self.line<(self.bed_max_y-self.line_space):
            self.line+=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.xdist)+ " Y"+str(self.line)+" F1000.000")

    def prev_position(self):
        if self.line>=(self.ydist +self.line_space):
            self.line-=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.xdist)+ " Y"+str(self.line)+" F1000.000")

    def print_line(self):
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-1.3#with the current system the nozle is 1mm higher 

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+str(self.line) +" F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+str(self.line)+" F5000.000"
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    """
    def test_sample(self, self.pneumatic):
        ydist=self.ydist
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-1.3#with the current system the nozle is 1mm higher 
            

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            for i in range(0,10):
                gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+ str(ydist) + " F1000.000"+ "\n"
                gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
                gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size) + " E22.4 F"+str(self.speed)+ "\n"
                gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
                gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
                if i%2==1:
                        ydist+=2.5
                ydist+=self.line_space
            gcode_string=gcode_string +"G1 X"+str(self.xdist-20)+ " Y"+ str(ydist) + " F1000.000"+ "\n" #move out so i can take a pricture
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify(self.pneumatic)
        else:
            print("can't print layer height or z height not valid")
    """
    #fct pour faire une petite plaque 
    def test_sample(self):
        ydist=self.line
        ywidth=10 #width of the rect
        width_depose=1
        cnt=int((ywidth/width_depose)/2)

        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-1.3#with the current system the nozle is 1.3mm higher 
            
            
            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+ str(ydist) + " F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 Y"+ str(ydist+ywidth) +"\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist-width_depose)+ "\n"
            for i in range (1,cnt+1):
                gcode_string=gcode_string +"G1 Y"+ str(ydist+i*width_depose)+"\n"
                gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size-i*width_depose)+"\n"
                gcode_string=gcode_string +"G1 Y"+ str(ydist+ywidth-i*width_depose) +"\n"
                gcode_string=gcode_string +"G1 X"+str(self.xdist+i*width_depose)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist-20)+ " Y"+ str(ydist) + " F1000.000"+ "\n" #move out so i can take a picture
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
        self.p = printcore('/dev/ttyACM0', 115200)
        self.flag = 0
        # Set the response callback
        self.p.loud = True
        self.p.recvcb = self.response_callback

        # Wait until the printer is connected
        while not self.p.online:
            time.sleep(0.1)
        
        self.homing()
        return 