from printrun.printcore import printcore
from printrun import gcoder
import time
import io
import threading

from pneumatic_control import Pneumatic

class Printer():
    def __init__(self):
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
        self.on_going_print=0
        self.pneumatic_inst=None
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
    
    """
    def stop_print(self):
        self.p.send_now("M410")
        self.pause=1
        self.mutex.acquire()
        try:
            self.pile_gcode=[]
            self.pile_count=[]
            self.pile_depose=[]
            self.pile_depose.append(0)
        finally:
            self.mutex.release()
        self.pause=0
        self.homed=0
    """
    
    def send_gcode_routine(self):

        while True:
            # Mettre un mutex sur PILE
            # si liste pas vide
            # Lire premier element pile
            # liberer le mutex sur PILE

            # Send de la premiere ligne gcode
            # Attendre la reponse

            # Mettre un mutex sur PILE
            # retirer premier element pile
            # liberer le mutex sur PILE
            if not self.thread_state:
                break
            #print("thread runing\n")
            if self.pile_gcode!=[]:
                if not self.on_going_print:
                    self.on_going_print=1
                
                self.mutex.acquire()
                try:
                    #send new orders
                    self.p.send_now(self.pile_gcode[0])  #send to printer
                    depose=self.pile_depose[0] #update pneumatic state
                    self.update(self.pneumatic_inst,1,depose)
                    layer_count=self.pile_count[0]+1
                    
                    #clean what you just sent
                    self.pile_gcode.pop(0)
                    self.pile_count.pop(0)
                    self.pile_depose.pop(0)

                    #print("we sent the orders")
                finally:
                    self.mutex.release()
                # Libere le mutex sur PILE
                print("the count:")
                print(layer_count)
                while self.flag!=(layer_count):
                    if not self.thread_state:
                        break
                    time.sleep(0.1)#needed to let the GUI update
                    pass
                self.flag=0
            else:
                if self.on_going_print:
                    self.on_going_print=0
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

    
    def update(self,pneumatic_inst,state, depose):

        if depose==0:
            #turn off the buse, keep cart on to stablize pressure, cut ato or it blow everything away
            pneumatic_inst.st_Ato=0
            pneumatic_inst.st_cart=1
            pneumatic_inst.st_point=0
        else: 
           
            pneumatic_inst.st_Ato=1
            pneumatic_inst.st_cart=1
            pneumatic_inst.st_point=1

        if not state:
            #state is 0 when we turn off the GUI
            pneumatic_inst.st_Ato=0
            pneumatic_inst.st_cart=0
            pneumatic_inst.st_point=0
            pneumatic_inst.c_ato=0
            pneumatic_inst.c_cart=0
        
        Pneumatic.sendToClient(pneumatic_inst, state) #send the orders to pneumatic with the above updates

    def get_line_and_modify(self,pneumatic_inst):
        depose = 0
        new_layer = 0
        layer=""
        count=0
        self.flag=0
        self.pause=0

        Pneumatic.sendToClient(pneumatic_inst,1)#should turn on the pressure but depose is at 0 so nothing else

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
                layer = layer + "\n"+ modified_line
                count+=1
                
            else:
                #new layer, pneumatic will have to change (turn on or off)
                layer= layer + "\n" + "M400"
                self.pneumatic_inst=pneumatic_inst
                print_data=[layer,depose, count]
                print(print_data)
                self.add_to_pile(print_data)
                layer = ""
                layer = layer + "\n" + modified_line
                new_layer=0
                count=1
                

        layer= layer + "\n" + "M400" 
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

    def print_line(self, pneumatic_inst):
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-1#with the current system the nozle is 1mm higher 

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+str(self.line) +" F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+str(self.line)+" F5000.000"
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify(pneumatic_inst)
        else:
            print("can't print layer height or z height not valid")
    
    def test_sample(self, pneumatic_inst):
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-1#with the current system the nozle is 1mm higher 
            ydist=self.ydist

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            for i in range(0,10):
                gcode_string=gcode_string +"G1 X"+str(self.xdist)+ " Y"+ str(self.ydist) + " F1000.000"+ "\n"
                gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
                gcode_string=gcode_string +"G1 X "+str(self.xdist + self.sample_size) + " E22.4 F"+str(self.speed)+ "\n"
                gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
                gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
                if i%2==1:
                        ydist+=2.5
                ydist+=self.line_space
            gcode_string=gcode_string +"G1 X"+str(self.xdist-20)+ " Y"+ str(self.ydist) + " F1000.000"+ "\n" #move out so i can take a pricture
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify(pneumatic_inst)
        else:
            print("can't print layer height or z height not valid")

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
        
        self.p.send_now("G28 W")
        self.p.send_now("G1 Z10") 
        self.homed=1
        return 