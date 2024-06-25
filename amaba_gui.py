import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
import customtkinter

#for the printer
from printer_control import printer

#for the pneumatic control with ethercat
from pneumatic_control import pneumatic




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
        text="Quit",
        width=200,
        height=50,
        command=lambda: [pneumatic.stop_c_program(), pneumatic.stop_socket(),self.window.destroy()],
        )
        self.modeBtn.pack(side=LEFT, padx=10,pady=10)

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
        pneumatic.sendToClient(1)
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
        pneumatic.sendToClient(1)

    def sliderFa(self, value):
        pneumatic.c_ato=round(value,2)
        self.show_consiA.configure(text=pneumatic.c_ato)
        pneumatic.sendToClient(1)
    
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
        
        #pneumatic.sendToClient(1)
        self.window.update()
        #self.window.after(500, self.update) # run itself again after 500 ms

    #def stop_Updates(self):
    #    self.window.after_cancel(self.update)

pneumatic=pneumatic()
printer = printer()
GUI = amabaGUI()