from printrun.printcore import printcore
from printrun import gcoder
import time

from pneumatic_control import pneumatic

class printer():
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
        self.bed_max_y=160
        self.bed_max_x=160
        self.line=20#y position of the test line

        
    
    def response_callback(line):
        current_response = line
        #print(f"Received: {line}")
        if "ok" in line:
            #print(f"Received: {line}")
            printer.flag+=1

    
    def update(self, state):
        #print("starting the update loop")
        if printer.depose==0:
            #print("turn off the buse")
            pneumatic.st_Ato=1
            pneumatic.st_cart=1
            pneumatic.st_point=0
        else: 
            #print("turn on the buse")
            if pneumatic.automatic==0:
                pneumatic.st_Ato=1
                pneumatic.st_cart=1
                pneumatic.st_point=1
            else:
                pneumatic.c_ato=0.4#get the F of the g code to mplement here
                pneumatic.c_cart=1.3
                ##send new pressure based on GUI

                pneumatic.st_Ato=1
                pneumatic.st_cart=1
                pneumatic.st_point=1
                #####GPIO here to turn on the vans
        if not state:
            pneumatic.st_Ato=0
            pneumatic.st_cart=0
            pneumatic.c_ato=0
            pneumatic.c_cart=0
        
        pneumatic.sendToClient(state)
        
        #print(f"Mes sent in socket: {mes}")
        #GUI.update(gui_instance)


    def get_line_and_modify(self):
        #start c process
        #c_program_process = printer.start_c_program()
        printer.depose = 0
        new_layer = 0
        printer.flag=0
        layer=""
        count=0
        #printer.update(gui_instance)

        #start com with c
        #client=printer.start_socket()
        #print("starting the socket")

        pneumatic.sendToClient(1)

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
                        if E_value > 0 and printer.depose==0:
                            new_layer=1
                            printer.depose=1
                        elif E_value <= 0 and printer.depose==1:
                            new_layer=1
                            printer.depose=0
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
                printer.p.send_now(layer)  #send to printer
                #p.send_now("M400")
                #print(f"sending: {layer}")
                
                while printer.flag!=(count+1):
                    pass
                #print("ok received")
                count=1
                #si on doit commencer une nouvelle coucher, couper ou allumer la buse
                layer = ""
                #print("start new layer")
                layer = layer + "\n" + modified_line
                new_layer=0
                printer.flag=0
                printer.update(1) #send to c
                

        layer= layer + "\n" + "M400" 
        #if printer.depose==0:
            #print("OFF")#ici c'est la couche actuel dont on a la dépose
        #else:
            #print("ON")  
        printer.update(0)#ligne rajouter sans test à verifier si pose un problème, on envoie 2 fois le message ?
        printer.p.send_now(layer)
        while printer.flag!=(count+1):
            pass

        # Close the connections
        printer.p.disconnect()
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
        if self.line<(self.bed_max_y-20):
            self.line+=20
        self.p.send_now("G1 X10 Y"+str(self.line) +" Z" +str(10 + self.sub))

    def prev_position(self):
        if self.line>20:
            self.line-=20
        self.p.send_now("G1 X10 Y"+str(self.line) +" Z" +str(10 + self.sub))

    def print_line(self):
        if (self.z>=1 and self.sub>=0):
            self.gcode_lines="G1 X10 Y"+str(self.line) +" Z" +str(10 + self.sub)+ "\n"
            self.gcode_lines="G1 Z"+str(self.z+self.sub) + "\n"
            self.gcode_lines="G1 X180 E22.4 F"+str(self.speed)+ "\n"
            self.gcode_lines="G1 E-0.80000 F2100.00000 \n"
            self.gcode_lines="G1 X10 Y"+str(self.line) +" Z" +str(10 + self.sub)+ "\n"
            self.get_line_and_modify
        else:
            print("can't print layer height or z height not valid")


    def connect(self):
        # Start communication with the printer
        self.p = printcore('/dev/ttyACM0', 115200)
        self.flag = 0
        # Set the response callback
        printer.p.loud = True
        printer.p.recvcb = printer.response_callback

        # Wait until the printer is connected
        while not self.p.online:
            time.sleep(0.1)
        
        printer.p.send_now("G28 W")
        printer.p.send_now("G1 Z20") 
        self.homed=1
        return 