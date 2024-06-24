import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
import customtkinter

#for the printer
from printrun.printcore import printcore
from printrun import gcoder
import time

#for the socket com with C
import socket
import select
import subprocess


class printer():
    flag=0
    depose=0
    p=None
    current_response=""
    # Callback function to handle responses from the printer

    def start_c_program():
        # Start the C program as a subprocess
        process = subprocess.Popen(['/home/amaba/Desktop/dev_ws/ighEthercat/ethercat/examples/user/ec_user_example'],  stdin=subprocess.PIPE)
        time.sleep(10)#there needs to be a little delay to allow the c subprocess to start
        return process

    def stop_c_program(process):
        # Terminate the C program
        process.terminate()
        process.wait()

    def send_with_socket(client_socket, mes):
        client_socket.sendall(mes.encode('utf-8'))

        # Receive response
        response = client_socket.recv(1024)
        #print(f"Received from server: {response.decode('utf-8')}")

        if mes == "0":
            return False
        return True

    def start_socket():
        host = 'localhost'
        port = 12345

        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        client_socket.connect((host, port))

        #print("Connected to the server")
        return client_socket

    def response_callback(line):
        current_response = line
        #print(f"Received: {line}")
        if "ok" in line:
            #print(f"Received: {line}")
            printer.flag+=1

    def sendToClient(state, client):
        presAto= int(pneumatic.c_ato*10)
        if (presAto<10):
            presAtostr="0"+str(presAto)
        else:
            presAtostr=str(presAto)
        presCart= int(pneumatic.c_cart*10)
        if (presCart<10):
            presCartstr="0"+str(presCart)
        else:
            presCartstr=str(presCart)
        mes = str(state) + str(pneumatic.st_cart)+  str(pneumatic.st_Ato) + str(pneumatic.st_point) + presCartstr +presAtostr 
        printer.send_with_socket(client, mes)


    def update(gui_instance, client, state):
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
        
        printer.sendToClient(state, client)
        
        #print(f"Mes sent in socket: {mes}")
        amabaGUI.update(gui_instance)


    def get_line_and_modify(gcode_lines,gui_instance):
        #start c process
        c_program_process = printer.start_c_program()
        printer.depose = 0
        new_layer = 0
        printer.flag=0
        layer=""
        count=0
        #printer.update(gui_instance)

        #start com with c
        client=printer.start_socket()
        #print("starting the socket")

        printer.sendToClient(1,client)

        for data in gcode_lines:
            modified_line = data.split(';')[0]

            if (data.startswith('M140') or data.startswith('M862') or 
                data.startswith('M104') or data.startswith('M190') or 
                data.startswith('M109') or data.startswith('\n')):
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
                printer.update(gui_instance, client, 1) #send to c
                

        layer= layer + "\n" + "M400" 
        #if printer.depose==0:
            #print("OFF")#ici c'est la couche actuel dont on a la dépose
        #else:
            #print("ON")  
        printer.update(gui_instance, client, 0)#ligne rajouter sans test à verifier si pose un problème, on envoie 2 fois le message ?
        printer.p.send_now(layer)
        while printer.flag!=(count+1):
            pass

        # Close the connections
        printer.p.disconnect()
        # Close the socket
        client.close()  
        #end c process
        printer.stop_c_program(c_program_process)
        return


    def connect(path):
        # Start communication with the printer
        printer.p = printcore('/dev/ttyACM0', 115200)
        printer.flag = 0
        # Set the response callback
        printer.p.loud = True
        printer.p.recvcb = printer.response_callback

        # Load the G-code file
        with open(path, 'r') as file_object:
            gcode_lines = file_object.readlines()

        # Wait until the printer is connected
        while not printer.p.online:
            time.sleep(0.1)
        
        return gcode_lines

class pneumatic:
    #st 0 ou 1 pour controller les vannes
    st_cart=1
    st_point=0
    st_Ato=1

    #c pour consigne la valeur envoyé à la vanne en bar
    c_cart=0.7 #entre 0 et 2
    c_point=5 #on doit envoyer 5V donc pas de souci tjrs 5V ou plus 
    c_ato=0.2 #entre 0 et 2

    #p pour la pression mesuer
    p_cart=0
    p_point=0
    p_ato=0

    #the g-code file path
    filePath=""

    automatic=0


class amabaGUI:

    def __init__(self):

        #if 1 the GUI will adapt to toutch screen and size
        self.raspberryPi=0

        #Main window
        customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("dark-blue")
        self.window = customtkinter.CTk()
        self.window.title("AMABA") 

        
        #raspberry pi specifications
        if self.raspberryPi:
            self.window.attributes('-fullscreen', True)
            self.window.configure(cursor="none")
        else:
            self.window.geometry("800x480")
        
        #a main frame to center properly
        self.main_frame = customtkinter.CTkFrame(master = self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        #defining in grid every frame seperate frame
        self.title_frame = customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.title_frame.pack(padx=10,pady=10,side=TOP)
        self.control_frame = customtkinter.CTkFrame(master = self.main_frame)
        self.control_frame.pack(padx=10,pady=10, side=BOTTOM)

        #sub frame for each pressure control element
        self.pointeau_frame = customtkinter.CTkFrame(master = self.control_frame)
        self.pointeau_frame.pack(side=LEFT, fill="both", expand=True, padx=10, pady=10) #il va falloir l'empècher de devenir trop petit
        self.cartouche_frame = customtkinter.CTkFrame(master = self.control_frame)
        self.cartouche_frame.pack(side=LEFT, pady=10,padx=10)
        self.atom_frame = customtkinter.CTkFrame(master = self.control_frame)
        self.atom_frame.pack(side=LEFT, pady=10,padx=10)



        #buttons for the Top frame
        self.title = customtkinter.CTkLabel(
        master = self.title_frame,
        text="AMABA Control",
        font=("Roboto",40),
        text_color="#3a7ebf",
        )
        self.title.pack(padx=0,pady=0)

        self.automaticBtn = customtkinter.CTkSwitch(
        master =self.title_frame,
        command = self.autoF,
        text="Manual",
        switch_width=40,
        switch_height=25,
        )
        self.automaticBtn.pack(padx=10,pady=10)

        #plusieurs modes peut être pour plus tard
        self.modeBtn = customtkinter.CTkButton(
        master =self.title_frame,
        text="Mode",
        #command = self.next_turn
        )
        #self.modeBtn.pack(side=LEFT, padx=10,pady=10)

        self.gcode = customtkinter.CTkButton(
        master =self.title_frame,
        text="Send g-code",
        command = self.gcodeF,
        width=200,
        height=50,
        )
        self.gcode.pack(padx=10,pady=5)


        #frame cartouche 
        self.title_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Cartouche",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_cart.pack(padx=10,pady=10)

        self.on_cart = customtkinter.CTkSwitch(
        master =self.cartouche_frame,
        text="OFF",
        command=lambda: self.onF("c"),
        switch_width=40,
        switch_height=25,
        )
        self.on_cart.pack(padx=10,pady=10)

        self.consi_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Consigne",
        #command = self.next_turn
        )
        self.consi_cart.pack(padx=10,pady=0)


        self.cart_bar = customtkinter.CTkSlider(
        master = self.cartouche_frame,
        from_=0, to=2, 
        command=self.sliderFc,
        width = 200,
        height=20,
        number_of_steps=20,
        )
        self.cart_bar.set(pneumatic.c_cart)

        self.show_consi = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text=round(self.cart_bar.get(),2),
        )
        self.show_consi.pack(padx=10,pady=0)
        self.cart_bar.pack(padx=10,pady=10)

        self.press_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Pression",
        #command = self.next_turn
        )
        self.press_cart.pack(padx=10,pady=0)

        self.show_press = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text=pneumatic.p_cart,
        #command = self.next_turn
        )
        self.show_press.pack(padx=10,pady=0)




        #frame pointeau
        self.title_point = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text="Pointeau",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_point.pack(padx=10,pady=10)

        self.on_point = customtkinter.CTkSwitch(
        master =self.pointeau_frame,
        text="OFF",
        command=lambda: self.onF("p"),
        switch_width=40,
        switch_height=25,
        )
        self.on_point.pack(padx=10,pady=10)

        #We just have to pressure sensor so maybe not this one
        self.press_point = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text="Pression",
        #command = self.next_turn
        )
        #self.press_point.pack(padx=10,pady=0) 

        self.show_pressP = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text=pneumatic.p_point,
        #command = self.next_turn
        )
        #self.show_pressP.pack(padx=10,pady=0)



        #frame atmisation
        self.title_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Atomisation",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_ato.pack(padx=10,pady=10)

        self.on_ato = customtkinter.CTkSwitch(
        master =self.atom_frame,
        text="OFF",
        command=lambda: self.onF("a"),
        switch_width=40,
        switch_height=25,
        )
        self.on_ato.pack(padx=10,pady=10)

        self.consi_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Consigne",
        #command = self.next_turn
        )
        self.consi_ato.pack(padx=10,pady=0)

        self.ato_bar = customtkinter.CTkSlider(
        master = self.atom_frame,
        from_=0, to=2,
        command = self.sliderFa,
        width = 200,
        height=20,
        number_of_steps=20,
        )
        self.ato_bar.set(pneumatic.c_ato)

        self.show_consiA= customtkinter.CTkLabel(
        master = self.atom_frame,
        text=round(self.ato_bar.get(),2),
        )
        self.show_consiA.pack(padx=10,pady=0)
        self.ato_bar.pack(padx=10,pady=10)

        self.press_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Pression",
        #command = self.next_turn
        )
        self.press_ato.pack(padx=10,pady=0)

        self.show_pressA = customtkinter.CTkLabel(
        master = self.atom_frame,
        text=pneumatic.p_ato,
        #command = self.next_turn
        )
        self.show_pressA.pack(padx=10,pady=0)
        
        self.window.mainloop()
    
    def gcodeF(self):
        pneumatic.filePath = fd.askopenfilename()
        #print("chosen file:")
        #print(pneumatic.filePath)

        #self.update() #it should update continuously afterwards
        #connect ot printer and start com
        gcode=printer.connect(pneumatic.filePath)
        # Modify and send the G-code lines
        printer.get_line_and_modify(gcode,self)
        #self.stop_Updates()



    def onF(self,case):
        if case == "p":
            if pneumatic.st_point:
                self.on_point.configure(text = "OFF")
                pneumatic.st_point = 0
            else:
                self.on_point.configure(text = "ON")
                pneumatic.st_point = 1
        elif case=="c":
            if pneumatic.st_cart:
                self.on_cart.configure(text = "OFF")
                pneumatic.st_cart = 0
            else:
                self.on_cart.configure(text = "ON")
                pneumatic.st_cart = 1
        elif case=="a":
            if pneumatic.st_Ato:
                self.on_ato.configure(text = "OFF")
                pneumatic.st_Ato = 0
            else:
                self.on_ato.configure(text = "ON")
                pneumatic.st_Ato = 1
    def autoF(self):
        if pneumatic.automatic:
            self.automaticBtn.configure(text = "Manual")
            pneumatic.automatic = 0
        else:
            self.automaticBtn.configure(text = "Automatic")
            pneumatic.automatic = 1

    def sliderFc(self, value):
        pneumatic.c_cart=round(value,2)
        self.show_consi.configure(text=pneumatic.c_cart)

    def sliderFa(self, value):
        pneumatic.c_ato=round(value,2)
        self.show_consiA.configure(text=pneumatic.c_ato)
    
    def update(self):
        #print("we re updating the GUI")
        #update the labels
        self.show_consi.configure(text=pneumatic.c_cart)
        self.show_consiA.configure(text=pneumatic.c_ato)

        #update the slides
        self.cart_bar.set(pneumatic.c_cart)
        self.ato_bar.set(pneumatic.c_ato)

        #update the pressure
        self.show_pressA.configure(text=pneumatic.p_ato)
        self.show_press.configure(text=pneumatic.p_cart)

        #update the on/off
        if pneumatic.st_point:
            self.on_point.configure(text = "ON")
            self.on_point.select()
        else:
            self.on_point.configure(text = "OFF")
            self.on_point.deselect()
        if pneumatic.st_cart:
            self.on_cart.configure(text = "ON")
            self.on_cart.select()
        else:
            self.on_cart.configure(text = "OFF")
            self.on_cart.deselect()
        if pneumatic.st_Ato:
            self.on_ato.configure(text = "ON")
            self.on_ato.select()
        else:
            self.on_ato.configure(text = "OFF")
            self.on_ato.deselect()

        self.window.update()
        #self.window.after(500, self.update) # run itself again after 500 ms

    #def stop_Updates(self):
    #    self.window.after_cancel(self.update)

        

amabaGUI()