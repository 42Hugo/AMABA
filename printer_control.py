from printrun.printcore import printcore
from printrun import gcoder
import time
import io
import threading

from pneumatic_control import Pneumatic

class Printer():
    def __init__(self,pneumatic):
        """Constructor method

        :param pneumatic: shared pneumatic object betwen the class GUI and printer to both update the pneumatic elements
        :type pneumatic: object

        :param pneumatic: Shared pneumatic object between the class GUI and printer to both update the pneumatic elements
        :type pneumatic: object

        :param flag: Flag to indicate "ok" received from the printer, printer sendsok when receiing any g-code line and when receiving M400 waits for the end of movement before sending ok, defaults to 0
        :type flag: int
        :param depose: printing state, on (1) or off(0), defaults to 0
        :type depose: int
        :param p: Placeholder for the printer object, defaults to None
        :type p: object
        :param current_response: Stores the current response from the printer
        :type current_response: str
        :param gcode_lines: Stores the G-code lines to be sent to the printer
        :type gcode_lines: str
        :param homed: Indicates if the printer has done homing since boot, defaults to 0
        :type homed: int
        :param speed: Printing speed, defaults to 1800
        :type speed: int
        :param z: Printing height not including printing bed, defaults to 1
        :type z: int

        :param ydist: Start y position for substrate test, defaults to 15
        :type ydist: int
        :param line: current position when Moving y position with button next line and prev position, defaults to ydist
        :type line: int
        :param sample_size_x: Sample size in x-direction, defaults to 70
        :type sample_size_x: int
        :param sample_size_y: Sample size in y-direction, defaults to 120
        :type sample_size_y: int
        :param line_space: Space between lines drawen with test substrat button or next/prev position, defaults to 10
        :type line_space: int
        :param x_space_on_borders: Space left without print when testing lines on each side, defaults to 5
        :type x_space_on_borders: int
        :param sub: thickness of the substrate, 0 if no substrate, defaults to 6 (PMMA)
        :type sub: int

        :param min_z: Minimum z height, defaults to 0.1
        :type min_z: float
        :param max_z: Maximum z height, defaults to 20
        :type max_z: float
        :param min_sub: Minimum substrate height, defaults to 0
        :type min_sub: int
        :param max_sub: Maximum substrate height, defaults to 50
        :type max_sub: int
        :param min_speed: Minimum printing speed, defaults to 500
        :type min_speed: int
        :param max_speed: Maximum printing speed, defaults to 12000
        :type max_speed: int
        :param bed_max_y: Maximum y-dimension of the print bed, defaults to 250
        :type bed_max_y: int
        :param bed_max_x: Maximum x-dimension of the print bed, defaults to 210
        :type bed_max_x: int
        :param z_offset: Offset in z-direction, taken as a negative value **to verify and change if needed**, defaults to 1.3
        :type z_offset: float

        :param stop: Flag to stop the printing process, defaults to 0
        :type stop: int
        :param on_going_print: Indicates if a print is currently ongoing, defaults to 0
        :type on_going_print: int
        :param multilayer_print: Indicates if a multilayer print from g-code is ongoing, defaults to 0
        :type multilayer_print: int
        :param go_next_layer: Flag to proceed to the next layer, changed by a timer or user input, defaults to 0
        :type go_next_layer: int
        :param mutex: Lock to manage concurrent access with reading and writting on piles
        :type mutex: threading.Lock
        :param pile_gcode: Queue of G-code instructions to be sent (stack by group with the same depose state, printing or movement)
        :type pile_gcode: list
        :param pile_change_layer: Queue of layer change, 1 if after this layer time is needed to dry, defaults to 0
        :type pile_change_layer: list
        :param pile_depose: Queue of depos instructions, 0 mean movement without printing and 1 nozzle, fluid and atomization on, defaults to 0
        :type pile_depose: list
        :param thread_state: State of the thread, defaults to 1 (running)
        :type thread_state: int
        :param wait_minutes: Wait time between layers in minutes, defaults to 60
        :type wait_minutes: int
     
        """
        
        self.pneumatic=pneumatic

        self.flag=0
        self.depose=0
        self.p=None
        self.current_response=""
        self.gcode_lines=""
        self.homed=0
        self.speed=1800 
        self.z=1 
        

        #substrat infos
        self.ydist=15 
        self.line=self.ydist 
        self.sample_size_x=70
        self.sample_size_y=120
        self.line_space=10
        self.x_space_on_borders=5
        self.sub=6 


        #safety values for the printer based on dimensiosn and limitations
        self.min_z=0.1#[mm]
        self.max_z=20
        self.min_sub=0
        self.max_sub=50
        self.min_speed=500
        self.max_speed=12000
        self.bed_max_y=250
        self.bed_max_x=210
        self.z_offset=1.3


        self.stop=0
        self.on_going_print=0 
        self.multilayer_print=0
        self.go_next_layer=0
        self.mutex=threading.Lock()

        #gcdode lists
        self.pile_gcode = []
        self.pile_change_layer=[]
        self.pile_depose=[]
        self.pile_depose.append(0)
        self.thread_state=1
        self.wait_minutes=60

        self.t_gcode= threading.Thread(target=self.send_gcode_routine)
        self.t_gcode.start()
    
    def kill_thread(self):
        """method to kill the thread handling sending g-code to printer
        """
        self.thread_state=0

    
    def send_gcode_routine(self):
        """g-code method to send g-code comands to the printer, is run independently on a seperate thread continuously
        """

        while True:
            if not self.thread_state:
                #stop thread if user input is given
                break

            if self.stop:
                #stop print and empty saved g-code if user input is given
                self.pile_gcode=[]
                self.pile_change_layer=[]
                self.pile_depose=[]
                #empty every array to do something else
                #not working yet
            
            if self.pile_gcode!=[]:
                #when there is g-code listed send it 

                #self.go_next_layer=0

                if not self.on_going_print:
                    #update the state of the GUI to lock it
                    self.on_going_print=1
                
                #prevent send_gcode_routine() and add_to_pile() to access at the same time at the lists
                self.mutex.acquire()

                try:
                    depose=self.pile_depose[0] #update pneumatic state
                    change_layer=self.pile_change_layer[0]
                    self.update(1,depose)
                    layer=self.pile_gcode[0]

                    while layer!=[]:
                        #every element in this loop will have the same state of depose

                        if self.stop:
                            continue
                        
                        #send first line and delete it afterward
                        self.p.send_now(layer[0])  #send to printer
                        layer.pop(0)
                        
                        #wait for the printer to send "ok" before moving to the next movement
                        while self.flag!=1:
                            if not self.thread_state:
                                break
                            if self.stop:
                                continue
                            time.sleep(0.1)#needed to let the GUI update, if not the GUI will freeze while waiting 
                    
                        self.flag=0

                    #clean what was just sent
                    self.pile_gcode.pop(0)
                    self.pile_change_layer.pop(0)
                    self.pile_depose.pop(0)

                finally:
                    self.mutex.release()

                    if change_layer:
                        self.p.send_now("G91")#change to relativ coordinates
                        self.p.send_now("G1 Z3")#go up 3mm in z to let dry (needed for printing without atomization)

                        total_wait_time = self.wait_minutes * 60#self.wait_minutes given by user input
                        elapsed_time = 0
                        interval = 0.5
                        self.go_next_layer=0

                        while self.go_next_layer == 0 and elapsed_time < total_wait_time:
                            if not self.thread_state:  # Check if user quit
                                break
                            if self.stop:
                                continue
                            time.sleep(interval)
                            elapsed_time += interval

                        self.p.send_now("G1 Z-3")#go back 3mm lower
                        self.p.send_now("G90")#back to absolute coordinate
                        time.sleep(0.1)#to make sure the ok was received
                        self.flag=0#the last command was takken as a flag

            else:
                if self.on_going_print:
                    self.on_going_print=0
                
                if self.multilayer_print:
                    self.multilayer_print=0
            time.sleep(0.1)#needed to let the GUI update

        
    
    def add_to_pile(self,print_data):
        """methode to add gcode lines, depose state and layer state to the lists

        :param print_data: this param includes the gcode lines that have the same depose state, the depsoe state and if it's the last sequence before change of layer 
        :type print_data: list
        """
        
        #prevent add_to_pile and send_gcode_routine to write and read at the same time on the  lists
        self.mutex.acquire()
        try:
            self.pile_gcode.append(print_data[0])
            self.pile_depose.append(print_data[1])
            self.pile_change_layer.append(print_data[2])
        finally:
            self.mutex.release()
        return 0


    def response_callback(self,line):
        """continuously listen to the serial comunciation with the printer and if "ok" is sent by the printer flag goes to +1

        :param line: message sent by the printer
        :type line: str
        """
        current_response = line
        if "ok" in line:
            self.flag+=1

    
    def update(self,state, depose):
        """updates the pneumatic according to the gcode instructions

        :param state: State of the subprocess, 1 for running, 0 for stopping, defaults to 1
        :type state: int
        :param depose: state of the depose, printing or simple movment, defaults to 0
        :type depose: int

        """

        if depose==0:
            #turn off the buse
            self.pneumatic.st_ato=0
            self.pneumatic.st_cart=0
            self.pneumatic.st_point=0
        else: 
            self.pneumatic.st_ato=1
            self.pneumatic.st_cart=1
            self.pneumatic.st_point=1

        if not state:
            #state is 0 when we turn off the GUI
            self.pneumatic.st_ato=0
            self.pneumatic.st_cart=0
            self.pneumatic.st_point=0
            self.pneumatic.c_ato=0
            self.pneumatic.c_cart=0
        
        self.pneumatic.sendToClient(state) #send the orders to pneumatic with the above updates

    def get_line_and_modify(self):
        """the gcode lines that have to be sent are first checked here and modified if necessary 

        **Notes on G-code lines used:**

         - M400: This command causes G-code processing to pause and wait in a loop until all moves in the planner are completed, sends okay when done. This command is used to synchronize the pneumatic with the printer.
         - M862:Perform an axis continuity test for position encoder modules
         - M104: Set Hotend Temperature
         - M109: Wait for Hotend Temperature
         - G28: auto home
         - G80: Cancel Current Motion Mode - in the start g-code it also adds the mesh be leveling
         - G1 Z0.2/0.3 F720 : these are the 2 standard oprtions for the intro line of the mk3, they can be deleted from the slicer directly (printer->g-code personalisé -> g-code start) 
        
        Most movments starts with **G1** and **E** stands for extruder, when positive printing is ongoing, when negative the print will stop.
        when there  is no E it is a simple movment

        :param depose: 0 if not currently printing, 1 otherwise, defaults to 0
        :type depse: int
        :param change_depose_state: 0 if the depose state is same as the previosu g-code commande, 1 otherwise, defaults to 0
        :type change_depose_state: int
        :param layer: list of g-code lines with the same depose state
        :type type: list
        :param change_layer: 1 when the current group of command is the last before change of layer, defaults to 0
        :type change_layer: int
        :param print_data: list with 3 informations, a list of g-code commands all having the same depose state, the information if the change of layer is happening. print_data=[layer,depose, change_layer]
        :type print_data: list

        """

        self.flag=0
        self.stop=0
        depose = 0
        change_depose_state = 0
        layer=[]
        change_layer=0
        print_data=[]

        self.pneumatic.sendToClient(1)#should turn on the pressure but depose is at 0 so nothing else

        for data in self.gcode_lines:

            if data.startswith(';AFTER_LAYER_CHANGE'):#after layer change is when the extruder is off
                change_layer=1

            #if a ";" is at the end of the line it will be deleted
            modified_line = data.split(';')[0]

            #to block homing, hotend temperature, comment, intro line (intro line can be deleted from slicer directly, here is just a security)
            if (data.startswith('M862') or data.startswith('M104')or 
                data.startswith('M109') or data.startswith('\n') or
                data.startswith('G28') or data.startswith(';') or 
                data.startswith('G80') or data.startswith('G1 Z0.2 F720')or 
                data.endswith('G1 Z0.3 F720') or
                data.endswith('go outside print area') or data.endswith('intro line')):
                continue

            #movements starts with G1 when printing and when not printing
            elif data.startswith('G1'):

                #E stands for the extruder, posiitve means printing, negative means stop printing
                if 'E' in data:
                    try:
                        E_value = float(data.split('E')[1].split()[0])
                    except (IndexError, ValueError):
                        E_value = None

                    #check if the state of depsoe has changed since last layer
                    if E_value is not None:
                        if E_value > 0 and depose==0:
                            change_depose_state=1
                            depose=1
                        elif E_value <= 0 and depose==1:
                            change_depose_state=1
                            depose=0
                        #E should always give a null or negativ number before stopping but some slicer parameters could change that
                    
                    
            if not change_depose_state:
                #still working on the same group, no need to change the pneumatic
                layer.append(modified_line)
            else:
                #new group (change of depose state), pneumatic will have to change (turn on or off)
                layer.append("M400")#add M400 to wait the end of the movement before change of depsoe state
                print_data=[layer,depose, change_layer]
                self.add_to_pile(print_data)

                #empty the current group that has already been added to the pile
                layer = []

                #the last g-code line had a change of depsoe state so it should be on top of the new group with the new parameters, it is now added to the empti list layer
                layer.append(modified_line)
                change_depose_state=0
                change_layer=0

                
        #all the g-code has been modified just send the last group
        layer.append("M400")
        print_data=[layer,depose,change_layer]
        self.add_to_pile(print_data)
        return

    def stop_print(self):
        """this method is called by the GUI when pressing stop print
        """
        self.stop=1

    def load_gcode(self, path):
        """method to load the gcode from a file to self.gcode_lines
        
        :param path: path to the gcode
        :type path: str
        """
        # Load the G-code file
        with open(path, 'r') as file_object:
            self.gcode_lines = file_object.readlines()
        
        return
    
    def next_position(self):
        """the method is activated from the GUI to move the position of the nozzle on *y* from the distance line_space.
        """
        if self.line<(self.bed_max_y-self.line_space):
            self.line+=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.bed_max_x- self.sample_size_x)+ " Y"+str(self.line)+" F2000.000")

    def prev_position(self):
        """the method is activated from the GUI to move backward the position of the nozzle on *y* from the distance line_space.
        """
        if self.line>(self.ydist +self.line_space):
            self.line-=self.line_space
        self.p.send_now("G1 Z" +str(10 + self.sub+self.z))
        self.p.send_now("G1 X"+str(self.bed_max_x- self.sample_size_x)+ " Y"+str(self.line)+" F2000.000")

    def print_line(self):
        """based on the current position of the nozzle choses with the methods prev_position and next_position print a line of the substrat informations
        """
        if (self.z>=self.min_z and self.z<20 and self.sub>=0 and self.sub<50):#last check if the value are allowed, but they should be checked in GUI already
            self.z=self.z-self.z_offset#with the current system the nozle is higher than it should be 

            gcode_string="G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x+self.x_space_on_borders)+ " Y"+str(self.line) +" F1000.000"+ "\n"
            gcode_string=gcode_string +"G1 Z"+str(self.z+self.sub) + "\n"
            gcode_string=gcode_string +"G1 X "+str(self.bed_max_x-self.x_space_on_borders) + " E22.4 F"+str(self.speed)+ "\n"
            gcode_string=gcode_string +"G1 E-0.80000 F2100.00000 \n"
            gcode_string=gcode_string +"G1 Z" +str(10 + self.sub+self.z)+ "\n"
            gcode_string=gcode_string +"G1 X"+str(self.bed_max_x-self.sample_size_x)+ " Y"+str(self.line)+" F5000.000"

            #the get_line_and_modify fct needs to read line by line the gcode for the for loop to work
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()

            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    
    def test_sample(self):
        """print lines on the whole samples based on the informations of the sample
        """
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
            
            #the get_line_and_modify fct needs to read line by line the gcode for the for loop to work
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()

            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")
    

    def test__full_rectangle(self):
        """this function was made to test making small rectangle with 100% infill, doesn't work well without atomization
        """
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
            
            #the get_line_and_modify fct needs to read line by line the gcode for the for loop to work
            buf=io.StringIO(gcode_string)
            self.gcode_lines=buf.readlines()

            self.get_line_and_modify()
        else:
            print("can't print layer height or z height not valid")

    def homing(self):
        """simple homing method
        """
        self.p.send_now("G28 W")
        self.p.send_now("G1 Z10") 
        self.homed=1

    def connect(self):
        """connection to the printer and start listening
        """

        self.p = printcore('/dev/ttyACM0', 115200)
        self.flag = 0

        #Set the response callback, listen to any message sent by the printer
        self.p.loud = True
        self.p.recvcb = self.response_callback

        #Wait until the printer is connected
        while not self.p.online:
            time.sleep(0.1)
        
        self.homing()
        self.homing()
        return 