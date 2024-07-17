import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
import customtkinter
import time
import threading

#for the printer
from printer_control import Printer

#for the pneumatic control with ethercat
from pneumatic_control import Pneumatic




class amabaGUI:

    def __init__(self,pneumatic,printer):

        self.pneumatic=pneumatic
        self.printer=printer

        #if 1 the GUI will adapt to toutch screen and size
        self.raspberryPi=0
        self.filePath=""
        self.locked=0

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
        self.control_frame = customtkinter.CTkFrame(master = self.main_frame)
        self.control_frame.pack(padx=0,pady=0, side=LEFT, fill="y")
        self.title_frame = customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.title_frame.pack(padx=10,pady=10,fil="both")
        

        #sub frame for each pressure control element
        self.pointeau_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.pointeau_frame.pack(side=BOTTOM, fill="both", padx=10, pady=12) #il va falloir l'empècher de devenir trop petit
        self.cartouche_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.cartouche_frame.pack(side=BOTTOM, pady=12,padx=10)
        self.atom_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.atom_frame.pack(side=BOTTOM, pady=12,padx=10)

        #sub frame for each mode
        self.gcode_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.test_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.substrat_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")

        self.modeBtn = customtkinter.CTkButton(
        master =self.title_frame,
        text="Quit",
        width=80,
        height=30,
        command=self.quit,
        )
        self.modeBtn.pack(side=RIGHT, anchor=NE, padx=0,pady=0)


        #buttons for the Top frame
        self.title = customtkinter.CTkLabel(
        master = self.title_frame,
        text="AMABA",
        font=("Roboto",40, "bold"),
        text_color="#3a7ebf",
        )
        self.title.pack(padx=10,pady=10, side= TOP, anchor=CENTER)

        self.automaticBtn = customtkinter.CTkSwitch(
        master =self.title_frame,
        command = self.autoF,
        text="Manual",
        switch_width=40,
        switch_height=25,
        )
        #self.automaticBtn.pack(padx=10,pady=10)

        self.gcode = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test g-code",
        command = self.gcodeF,
        width=100,
        height=40,
        )
        self.gcode.pack(side= LEFT, padx=20,pady=10)

        self.depose = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test print",
        command = self.test_depose,
        width=100,
        height=40,
        )
        self.depose.pack(side= LEFT, padx=20,pady=10)

        self.substrat = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test substrat",
        command = self.test_substrat,
        width=100,
        height=40,
        )
        self.substrat.pack(side= LEFT, padx=20,pady=10)

        #frame control pneumatic 
        self.title_control = customtkinter.CTkLabel(
        master = self.control_frame,
        text="Pneumatic",
        font=("Roboto", 20, "bold"),
        text_color="#3a7ebf",
        )
        self.title_control.pack(padx=10,pady=10, side= TOP)

        #frame cartouche 
        self.title_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Cartouche",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_cart.pack(padx=10,pady=5)

        self.on_cart = customtkinter.CTkSwitch(
        master =self.cartouche_frame,
        text="OFF",
        command=lambda: self.onF("c"),
        switch_width=40,
        switch_height=25,
        )
        self.on_cart.pack(padx=10,pady=5)

        self.consi_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Consigne",
        #command = self.next_turn
        )
        #self.consi_cart.pack(padx=10,pady=0)


        self.cart_bar = customtkinter.CTkSlider(
        master = self.cartouche_frame,
        from_=0, to=1.7, 
        command=self.sliderFc,
        width = 200,
        height=20,
        number_of_steps=17,
        )
        self.cart_bar.set(self.pneumatic.c_cart)

        self.show_consi = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text=round(self.cart_bar.get(),2),
        )
        self.show_consi.pack(padx=10,pady=0)
        self.cart_bar.pack(padx=10,pady=5)

        self.press_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Pression",
        #command = self.next_turn
        )
        #self.press_cart.pack(padx=10,pady=0)

        self.show_press = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text=self.pneumatic.p_cart,
        #command = self.next_turn
        )
        #self.show_press.pack(padx=10,pady=0)




        #frame pointeau
        self.title_point = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text="Pointeau",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_point.pack(padx=10,pady=5)

        self.on_point = customtkinter.CTkSwitch(
        master =self.pointeau_frame,
        text="OFF",
        command=lambda: self.onF("p"),
        switch_width=40,
        switch_height=25,
        )
        self.on_point.pack(padx=10,pady=5)

        #We just have to pressure sensor so maybe not this one
        self.press_point = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text="Pression",
        #command = self.next_turn
        )
        #self.press_point.pack(padx=10,pady=0) 

        self.show_pressP = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text=self.pneumatic.p_point,
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
        self.title_ato.pack(padx=10,pady=5)

        self.on_ato = customtkinter.CTkSwitch(
        master =self.atom_frame,
        text="OFF",
        command=lambda: self.onF("a"),
        switch_width=40,
        switch_height=25,
        )
        self.on_ato.pack(padx=10,pady=5)

        self.consi_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Consigne",
        #command = self.next_turn
        )
        #self.consi_ato.pack(padx=10,pady=5)

        self.ato_bar = customtkinter.CTkSlider(
        master = self.atom_frame,
        from_=0, to=2,
        command = self.sliderFa,
        width = 200,
        height=20,
        number_of_steps=20,
        )
        self.ato_bar.set(self.pneumatic.c_ato)

        self.show_consiA= customtkinter.CTkLabel(
        master = self.atom_frame,
        text=round(self.ato_bar.get(),2),
        )
        self.show_consiA.pack(padx=10,pady=5)
        self.ato_bar.pack(padx=10,pady=5)

        self.press_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Pression",
        #command = self.next_turn
        )
        #self.press_ato.pack(padx=10,pady=0)

        self.show_pressA = customtkinter.CTkLabel(
        master = self.atom_frame,
        text=self.pneumatic.p_ato,
        #command = self.next_turn
        )
        #self.show_pressA.pack(padx=10,pady=0)

        ###gcode mode frame
        self.t_substrat=customtkinter.CTkLabel(
        master = self.gcode_frame,
        text="Thickness of the substrat [mm] \n (0 being the prusa bed)",
        )
        self.t_substrat.grid(row = 0, column = 0, pady = 2, padx=2)

        self.t_substrat_v=customtkinter.CTkEntry(
            master = self.gcode_frame,
            width = 30,
            height=20,
            placeholder_text="0",
        )
        self.t_substrat_v.grid(row = 0, column = 1, pady = 2, padx=2)

        self.z_layer=customtkinter.CTkLabel(
        master = self.gcode_frame,
        text="layer height",
        )
        self.z_layer.grid(row = 1, column = 0, pady = 2, padx=2)

        self.z_layer_v=customtkinter.CTkEntry(
            master = self.gcode_frame,
            width = 30,
            height=20,
            placeholder_text="1",
        )
        self.z_layer_v.grid(row = 1, column = 1, pady = 2, padx=2)

        self.speed=customtkinter.CTkLabel(
        master = self.gcode_frame,
        text="Speed [mm/s]",
        )
        self.speed.grid(row = 2, column = 0, pady = 2, padx=2)

        self.speed_v=customtkinter.CTkEntry(
            master = self.gcode_frame,
            width = 60,
            height=20,
            placeholder_text="500",
        )
        self.speed_v.grid(row = 2, column = 1, pady = 2, padx=2)

        self.filebtn = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Choose file",
        command = self.choose_file,
        width=80,
        height=30,
        )

        self.start_gcode = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="start print",
        command = self.send_gcode,
        width=80,
        height=30,
        )

        self.n_line = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Next Position",
        command = lambda: [self.test_sent_parameters(),self.printer.next_position()],
        width=80,
        height=30,
        )

        self.p_line = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Previous Position",
        command = lambda: [self.test_sent_parameters(),self.printer.prev_position()],
        width=80,
        height=30,
        )

        self.draw_line = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Print Line",
        command=lambda: [self.test_sent_parameters(), self.printer.print_line()],
        width=80,
        height=30,
        )

        self.test_sub_btn = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Test sandard sample",
        command=self.run_test_sub,
        width=80,
        height=30,
        )
        """
        self.stop_btn = customtkinter.CTkButton(
        master =self.gcode_frame,
        text="Stop print",
        command=self.stop_print,
        width=80,
        height=30,
        )
        """
        self.window.after(2000,self.send_loop) 
        #we start a loop to regularly send info to the ethercat, 
        #send message when the slides bar are moved is giving to many request = crash
        self.window.mainloop()
    
    """
    def stop_print(self):
        pneumatic.stop_print()
        printer.stop_print()

        #on ferme tt les fenêtres pour obliger à faire un homing
        self.gcode_frame.forget_pack()
        pass
    """
    def quit(self):
        self.pneumatic.stop_c_program()
        self.pneumatic.stop_socket()
        self.printer.kill_thread()
        if self.printer.homed:
            self.printer.p.disconnect()
        self.window.destroy() 


    def lock_gui(self):
        print("lock/unlock GUI")
        if self.printer.on_going_print:
            self.on_ato.configure(state="disabled")
            self.on_cart.configure(state="disabled")
            self.on_point.configure(state="disabled")
            self.start_gcode.configure(state="disabled")
            self.p_line.configure(state="disabled")
            self.n_line.configure(state="disabled")
            self.draw_line.configure(state="disabled")
            self.test_sub_btn.configure(state="disabled")
            self.locked=1
        else:
            self.on_ato.configure(state="normal")
            self.on_cart.configure(state="normal")
            self.on_point.configure(state="normal")
            self.start_gcode.configure(state="normal")
            self.p_line.configure(state="normal")
            self.n_line.configure(state="normal")
            self.draw_line.configure(state="normal")
            self.test_sub_btn.configure(state="normal")
            self.locked=0



    def send_loop(self):
        #could be improved by sending only if changed happened on the slidding bars
        self.update() #on peut mettre tout le monde à jour ?
        self.pneumatic.sendToClient(1)
        if self.locked!=self.printer.on_going_print:
            self.lock_gui()
        self.window.after(500,self.send_loop)


    def choose_file(self):
        self.window.update()
        self.filePath = ""
        self.filePath  = fd.askopenfilename()#crash when used multiple time, only works once, find a solution
        self.window.update()

    def test_sent_parameters(self):
        #here check if parameters input by user are valide and disply when needed an error
        if self.z_layer_v.get()!='':
            if float(self.z_layer_v.get())>=self.printer.min_z and float(self.z_layer_v.get())<=self.printer.max_z:
                self.printer.z=float(self.z_layer_v.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a Z higher than 1mm")
                return 0
        if self.t_substrat_v.get()!='':
            if float(self.t_substrat_v.get())>=self.printer.min_sub and float(self.t_substrat_v.get())<=self.printer.max_sub:
                self.printer.sub=float(self.t_substrat_v.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a substrat thicker than 0mm")
                return 0
        if self.speed_v.get()!='':
            if float(self.speed_v.get())>=self.printer.min_speed and float(self.speed_v.get())<=self.printer.max_speed:
                self.printer.speed=float(self.speed_v.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a speed higher than 500")
                return 0
        return 1


    def run_test_sub(self):
        if self.test_sent_parameters():
            self.printer.test_sample()

    def send_gcode(self):
        if self.test_sent_parameters():
            if self.filePath.endswith(".gcode"):
                self.printer.load_gcode(self.filePath)
                self.printer.get_line_and_modify(self.pneumatic)
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a g-code file")

    def gcodeF(self):
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            self.printer.connect()#connect and do calibration
        
        #hide not needed btns
        self.p_line.grid_forget()
        self.draw_line.grid_forget()
        self.n_line.grid_forget()

        #make the send_g-code frame display
        self.gcode_frame.pack(padx=10,pady=10)
        self.filebtn.grid(row = 3, column = 0, columnspan = 2, pady=5)
        self.start_gcode.grid(row = 4, column = 0, columnspan = 2, pady=5)
        #self.stop_btn.grid(row = 5, column = 2,padx=10)

    def test_depose(self):
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            self.printer.connect()#connect and do calibration
        # mettre a 6mm la valeur de base du sample

        #hide uneeded btn
        self.filebtn.grid_forget()
        self.start_gcode.grid_forget()
        self.test_sub_btn.grid_forget()

        #make the send_g-code frame display
        self.gcode_frame.pack(padx=10,pady=10)
        self.p_line.grid(row = 3, column = 0, padx=10)
        self.draw_line.grid(row = 3, column = 1,padx=10)
        self.n_line.grid(row = 3, column = 2,padx=10)
        #self.stop_btn.grid(row = 5, column = 2,padx=10)

    def test_substrat(self):
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            self.printer.connect()#connect and do calibration
        
        #hide not needed btns
        self.p_line.grid_forget()
        self.draw_line.grid_forget()
        self.n_line.grid_forget()
        self.filebtn.grid_forget()
        self.start_gcode.grid_forget()

        #make the send_g-code frame display
        self.gcode_frame.pack(padx=10,pady=10)
        self.test_sub_btn.grid(row = 3, column = 0, columnspan = 2, pady=10,padx=10)
        #self.stop_btn.grid(row = 5, column = 2,padx=10)



    def onF(self,case):
        if case == "p":
            if self.pneumatic.st_point:
                self.on_point.configure(text = "OFF")
                self.pneumatic.st_point = 0
            else:
                self.on_point.configure(text = "ON")
                self.pneumatic.st_point = 1
        elif case=="c":
            if self.pneumatic.st_cart:
                self.on_cart.configure(text = "OFF")
                self.pneumatic.st_cart = 0
            else:
                self.on_cart.configure(text = "ON")
                self.pneumatic.st_cart = 1
        elif case=="a":
            if self.pneumatic.st_Ato:
                self.on_ato.configure(text = "OFF")
                self.pneumatic.st_Ato = 0
            else:
                self.on_ato.configure(text = "ON")
                self.pneumatic.st_Ato = 1
        #pneumatic.sendToClient(1)
    def autoF(self):
        if self.pneumatic.automatic:
            self.automaticBtn.configure(text = "Manual")
            self.pneumatic.automatic = 0
        else:
            self.automaticBtn.configure(text = "Automatic")
            self.neumatic.automatic = 1

    def sliderFc(self, value):
        self.pneumatic.c_cart=round(value,2)
        self.show_consi.configure(text=self.pneumatic.c_cart)
        #pneumatic.sendToClient(1)

    def sliderFa(self, value):
        self.pneumatic.c_ato=round(value,2)
        self.show_consiA.configure(text=self.pneumatic.c_ato)
        #pneumatic.sendToClient(1)
    
    def update(self):
        #print("we re updating the GUI")
        #update the labels
        self.show_consi.configure(text=self.pneumatic.c_cart)
        self.show_consiA.configure(text=self.pneumatic.c_ato)

        #update the slides
        self.cart_bar.set(self.pneumatic.c_cart)
        self.ato_bar.set(self.pneumatic.c_ato)

        #update the pressure
        self.show_pressA.configure(text=self.pneumatic.p_ato)
        self.show_press.configure(text=self.pneumatic.p_cart)

        #update the on/off
        if self.pneumatic.st_point:
            self.on_point.configure(text = "ON")
            self.on_point.select()
        else:
            self.on_point.configure(text = "OFF")
            self.on_point.deselect()
        if self.pneumatic.st_cart:
            self.on_cart.configure(text = "ON")
            self.on_cart.select()
        else:
            self.on_cart.configure(text = "OFF")
            self.on_cart.deselect()
        if self.pneumatic.st_Ato:
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


