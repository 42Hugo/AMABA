from printrun.printcore import printcore
from printrun import gcoder
import time
import io
import threading

from pneumatic_control import pneumatic

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
        self.sub=0 #height of the substrat, 0 if no substrat
        self.bed_max_y=180#check max safe value
        self.bed_max_x=160
        self.line=20#y position of the test line
        self.min_z=0.1#[mm]
        self.max_z=20
        self.min_sub=0
        self.max_sub=50
        self.min_speed=500
        self.max_speed=15000
        self.pneumatic_inst=None

        self.pile_gcode = []
        t_gcode= threading.Thread(target=self.send_gcode_routine)
        t_gcode.start()
    
    def send_gcode_routine(self):

        
        # Mettre un mutex sur PILE
        # si liste pas vide
        # Lire premier element pile
        # liberer le mutex sur PILE

        # Send de la premiere ligne gcode
        # Attendre la reponse

        # Mettre un mutex sur PILE
        # retirer premier element pile
        # liberer le mutex sur PILE
        return 0
    
    def add_to_pile(self,gcodeLine):
        # Mettre un mutex sur PILE
        self.pile_gcode.append(gcodeLine)
        # Libere le mutex sur PILE
        return 0


    def response_callback(self,line):
        current_response = line
        #print(f"Received: {line}")
        if "ok" in line:
            #print(f"Received: {line}")
            self.flag+=1

    
    def update(self,pneumatic_inst, state):
        #print("starting the update loop")
        if self.depose==0:
            #print("turn off the buse")
            pneumatic_inst.st_Ato=0
            pneumatic_inst.st_cart=1
            pneumatic_inst.st_point=0
        else: 
            #print("turn on the buse")
            """
            if pneumatic.automatic==0:
                pneumatic.st_Ato=1
                pneumatic.st_cart=1
                pneumatic.st_point=1
            else:
            pneumatic_inst.c_ato=0.4#get the F of the g code to mplement here
            pneumatic_inst.c_cart=1.3
            ##send new pressure based on GUI
            """
            pneumatic_inst.st_Ato=1
            pneumatic_inst.st_cart=1
            pneumatic_inst.st_point=1
                #####GPIO here to turn on the vans
        if not state:
            pneumatic_inst.st_Ato=0
            pneumatic_inst.st_cart=0
            pneumatic_inst.c_ato=0
            pneumatic_inst.c_cart=0
        
        pneumatic.sendToClient(pneumatic_inst, state)
        
        #print(f"Mes sent in socket: {mes}")
        #GUI.update(gui_instance)

    def get_line_and_modify(self,pneumatic_inst):
        #start c process
        #c_program_process = printer.start_c_program()
        self.depose = 0
        new_layer = 0
        self.flag=0
        layer=""
        count=0
        
        #valeurs reçu mais pas pris en compte pour le moment
        print(f"Printing Speed: {self.speed}")
        print(f"Printing Height (z): {self.z}")
        print(f"Substrate Height (sub): {self.sub}")
        print(f"Y Position of the Test Line: {self.line}")

        pneumatic.sendToClient(pneumatic_inst,1)
        print(f"what's gonne be printed: {self.gcode_lines}")

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
                        if E_value > 0 and self.depose==0:
                            new_layer=1
                            self.depose=1
                        elif E_value <= 0 and self.depose==1:
                            new_layer=1
                            self.depose=0
                        #normalement il n'y a pas de cas ou le E a juse pas de chiffre pour le stopper mais à verifier
                    
                    
            if new_layer==0:
                #print(f"sending: {modified_line}")
                #p.send_now(modified_line)
                layer = layer + "\n"+ modified_line
                count+=1
                
            else:
                layer= layer + "\n" + "M400"
                #if printer.depose==0:
                    #print("ON")#on dirait c'est inversé c'est par ce que c'est la future couche dont on a l'info dépose
                #else:
                    #print("OFF")
                self.p.send_now(layer)  #send to printer
                #p.send_now("M400")
                #print(f"sending: {layer}")
                
                while self.flag!=(count+1):
                    pass
                #print("ok received")
                count=1
                #si on doit commencer une nouvelle coucher, couper ou allumer la buse
                layer = ""
                #print("start new layer")
                layer = layer + "\n" + modified_line
                new_layer=0
                self.flag=0
                self.update(pneumatic_inst, 1) #send to c
                

        layer= layer + "\n" + "M400" 
        #if printer.depose==0:
            #print("OFF")#ici c'est la couche actuel dont on a la dépose
        #else:
            #print("ON")  
        self.update(pneumatic_inst, 1)#ligne rajouter sans test à verifier si pose un problème, on envoie 2 fois le message ?
        self.p.send_now(layer)
        while self.flag!=(count+1):
            pass

        # Close the connections
        #self.p.disconnect()
        # Close the socket
        #client.close()  
        #end c process
        #printer.stop_c_program(c_program_process)
        return

    def load_gcode(self, path):
        # Load the G-code file
        with open(path, 'r') as file_object:
            self.gcode_lines = file_object.readlines()
        
        return
    
    def next_position(self):
        if self.line<(self.bed_max_y-10):
            self.line+=10
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X20 Y"+str(self.line)+" F1000.000")

    def prev_position(self):
        if self.line>(self.bed_min_y+10):
            self.line-=10
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X20 Y"+str(self.line)+" F1000.000")

    def print_line(self, pneumatic_inst):
        if (self.z>=1 and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string + "G1 X20 Y"+str(self.line) +" F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X180 E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X20 Y"+str(self.line) +" F5000.000\n"
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify(pneumatic_inst)
        else:
            print("can't print layer height or z height not valid")
    
    def test_sample(self):
        if (self.z>=0.1 and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            ydist=15 #changing in the for loop, start y position
            xdist=120
            #sample_space=30
            sample_size=70
            line_space=10
            self.z=self.z-1#withy the current system the nozle is 1mm higher 

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            for i in range(0,10):
                gcode_string=gcode_string +"G1 X"+str(xdist)+ " Y"+ str(ydist) + " F1000.000"+ "\n"
                gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
                gcode_string=gcode_string +"G1 X "+str(xdist + sample_size) + " E22.4 F"+str(self.speed)+ "\n"
                gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
                gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
                if i%2==1:
                        ydist+=2.5
                ydist+=line_space
            gcode_string=gcode_string +"G1 X"+str(xdist-20)+ " Y"+ str(ydist) + " F1000.000"+ "\n" #move out so i can take a pricture
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()
            self.get_line_and_modify(self.pneumatic_inst)
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