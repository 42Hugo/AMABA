import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
import customtkinter
import time
import threading
import easygui 

#for the printer
from printer_control import Printer

#for the pneumatic control with ethercat
from pneumatic_control import Pneumatic




class amabaGUI:

    def __init__(self,pneumatic,printer):
        """constructor method that also implements every GUI elements: buttons, frames, entry... the methods relative to the GUI are defined later in the code

        :param pneumatic: shared pneumatic object betwen the class GUI and printer to both update the pneumatic elements
        :type pneumatic: object
        :param printer: object to interact with the printer variables and methods 
        :type printer: object
        :param raspberryPi: varible to specify is currently running on the raspberry pi with the toutch screen, if 1 the mouse won't be visible and full screen will be on
        :type raspberryPi: int
        :param filePath: path to the g-code file to print
        :type filePath: str
        :param locked: state of the GUI, locked is equal to 1 when a print is ongoing to prevent specific buttons to be activated, defaults to 0
        :type state: int
        """
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

        # Set column weight for proper alignment
        self.main_frame.grid_columnconfigure(0, weight=1)  # Left column (control_frame)
        self.main_frame.grid_columnconfigure(1, weight=0)  # Middle column (title_frame)
        self.main_frame.grid_columnconfigure(2, weight=0)  # Empty space column
        self.main_frame.grid_columnconfigure(3, weight=0)  # Right column (buttons)

        # Set row weight for proper alignment
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top row (buttons)
        self.main_frame.grid_rowconfigure(1, weight=0)  # Space between buttons
        self.main_frame.grid_rowconfigure(2, weight=0)  # Middle row (title_frame)
        self.main_frame.grid_rowconfigure(3, weight=0)  # Bottom row (control_frame)
        self.main_frame.grid_rowconfigure(4, weight=1)  # bottom stays empty


        self.quit_Btn = customtkinter.CTkButton(
        master =self.main_frame,
        text="Quit",
        width=80,
        height=30,
        command=self.quit,
        )
        self.quit_Btn.grid(row=0,column=3, padx=5, pady=5, sticky ="n")

        self.homing_btn = customtkinter.CTkButton(
        master =self.main_frame,
        text="Homing",
        command=self.printer.homing,
        width=80,
        height=30,
        )
        self.homing_btn.grid(row=1,column=3, padx=5, pady=5, sticky ="n")


        
        #defining in grid every seperate frame
        self.control_frame = customtkinter.CTkFrame(master = self.main_frame)
        self.control_frame.grid(row=0,column=0, rowspan=10, padx=1, pady=1, sticky="w")
        self.title_frame = customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.title_frame.grid(row=2,column=1, padx=5, pady=5, sticky="n")
        

        #sub frame for each pressure control element
        self.pointeau_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.pointeau_frame.pack(side=BOTTOM, fill="both", padx=10, pady=12) #il va falloir l'empècher de devenir trop petit
        self.cartouche_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.cartouche_frame.pack(side=BOTTOM, pady=12,padx=10)
        self.atom_frame = customtkinter.CTkFrame(master = self.control_frame, fg_color="transparent")
        self.atom_frame.pack(side=BOTTOM, pady=12,padx=10)

        #sub frame for each mode
        self.para_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.test_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.substrat_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")
        self.print_frame= customtkinter.CTkFrame(master = self.main_frame, fg_color="transparent")

        

        #Top frame

        #title
        self.title = customtkinter.CTkLabel(
        master = self.title_frame,
        text="AMABA",
        font=("Roboto",40, "bold"),
        text_color="#3a7ebf",
        )
        self.title.grid(row=2,column=1, padx=5, pady=5,columnspan=3)

        #button to activate "test g-code" the options to choose a g-code file and run it will be availabe
        self.gcode = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test g-code",
        command = self.gcodeF,
        width=100,
        height=40,
        )
        self.gcode.grid(row=3,column=1, padx=5, pady=5)

        #button to activate the options to test line by line with different parameters printing lines
        self.depose = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test print",
        command = self.test_depose,
        width=100,
        height=40,
        )
        self.depose.grid(row=3,column=2, padx=5, pady=5)

        #button to activate the options to test multiple lines in a row on a single substrat
        self.substrat = customtkinter.CTkButton(
        master =self.title_frame,
        text="Test substrat",
        command = self.test_substrat,
        width=100,
        height=40,
        )
        self.substrat.grid(row=3,column=3, padx=5, pady=5)





        #######frame pneumatic control#####
        self.title_control = customtkinter.CTkLabel(
        master = self.control_frame,
        text="Pneumatic",
        font=("Roboto", 20, "bold"),
        text_color="#3a7ebf",
        )
        self.title_control.pack(padx=10,pady=10, side= TOP)

        ####frame cartouche 
        self.title_cart = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text="Cartouche",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_cart.pack(padx=10,pady=5)

        #Swith to turn on or off the pressure on the fluid
        self.on_cart = customtkinter.CTkSwitch(
        master =self.cartouche_frame,
        text="OFF",
        command=lambda: self.onF("c"),
        switch_width=40,
        switch_height=25,
        )
        self.on_cart.pack(padx=10,pady=5)

        #Label to display the current pressure on the fluid
        self.show_consi = customtkinter.CTkLabel(
        master = self.cartouche_frame,
        text=round(self.pneumatic.c_cart,2),#round the number to 2 digit
        )
        self.show_consi.pack(padx=10,pady=0)

        #slider to control the pressure on the fluid between zero and 1.7 bar, it should be maximum 2 bar but it only worked up to 1.7
        self.cart_bar = customtkinter.CTkSlider(
        master = self.cartouche_frame,
        from_=0, to=1.7, 
        command=self.sliderFc,
        width = 200,
        height=20,
        number_of_steps=17,
        )
        self.cart_bar.set(self.pneumatic.c_cart)#set the position of the slidder to the current pneumatic state
        self.cart_bar.pack(padx=10,pady=5)




        ####frame atomization
        self.title_ato = customtkinter.CTkLabel(
        master = self.atom_frame,
        text="Atomisation",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_ato.pack(padx=10,pady=5)

        #Swith to turn on or off the pressure to spray the fluid
        self.on_ato = customtkinter.CTkSwitch(
        master =self.atom_frame,
        text="OFF",
        command=lambda: self.onF("a"),
        switch_width=40,
        switch_height=25,
        )
        self.on_ato.pack(padx=10,pady=5)

        #display the current pressure of atomization
        self.show_consiA= customtkinter.CTkLabel(
        master = self.atom_frame,
        text=round(self.pneumatic.c_ato,2),
        )
        self.show_consiA.pack(padx=10,pady=5)

        #slider to control the atomization pressure
        self.ato_bar = customtkinter.CTkSlider(
        master = self.atom_frame,
        from_=0, to=2,
        command = self.sliderFa,
        width = 200,
        height=20,
        number_of_steps=20,
        )
        self.ato_bar.set(self.pneumatic.c_ato)
        self.ato_bar.pack(padx=10,pady=5)



        ####frame pointeau
        self.title_point = customtkinter.CTkLabel(
        master = self.pointeau_frame,
        text="Pointeau",
        font=("Roboto",20),
        text_color="#3a7ebf",
        )
        self.title_point.pack(padx=10,pady=5)

        #Swith to turn on or off the nozzle
        self.on_point = customtkinter.CTkSwitch(
        master =self.pointeau_frame,
        text="OFF",
        command=lambda: self.onF("p"),
        switch_width=40,
        switch_height=25,
        )
        self.on_point.pack(padx=10,pady=5)



        ###para frame####
        
        #option menu to choose a predefined substrat size
        self.substrat_options = customtkinter.CTkOptionMenu(
            master=self.para_frame, 
            values=["95x95 PMMA", "120x70 PMMA", "60x60 PMMA", "other"],
            command=self.choose_substrat)
        self.substrat_options.set("95x95 PMMA")
        self.substrat_options.grid(row = 0, column = 0, columnspan=5, pady = 5, padx=5)

        #label displaying width, refering to the size of the substrat being tested
        self.x_width_label=customtkinter.CTkLabel(
        master = self.para_frame,
        text="width",
        )
        self.x_width_label.grid(row = 1, column = 0, pady = 5, padx=5)

        #entry to fill in the width of the substrat
        self.x_width=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 30,
            height=20,
            placeholder_text=95,
        )
        self.x_width.grid(row = 1, column = 1, pady = 5, padx=5)

        #label displaying length, refering to the size of the substrat being tested
        self.y_width_label=customtkinter.CTkLabel(
        master = self.para_frame,
        text="length",
        )
        self.y_width_label.grid(row = 1, column = 2, pady = 5, padx=5)

        #entry to fill in the length of the substrat
        self.y_width=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 30,
            height=20,
            placeholder_text=95,
        )
        self.y_width.grid(row = 1, column = 3, pady = 5, padx=5)

        #label for the thickness
        self.t_substrat=customtkinter.CTkLabel(
            master = self.para_frame,
            text="Thickness",
        )
        self.t_substrat.grid(row = 2, column = 0, pady = 5, padx=5)

        #entry to fill in the thickness of the substrat
        self.t_substrat_v=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 30,
            height=20,
            placeholder_text="6",
        )
        self.t_substrat_v.grid(row = 2, column = 1, pady = 5, padx=5)

        #label for the space beteen every line printed
        self.line_space_btn=customtkinter.CTkLabel(
        master = self.para_frame,
        text="space [mm]",
        )
        self.line_space_btn.grid(row = 2, column = 2, pady = 5, padx=5)

        #Entry for the space between every line printed
        self.line_space=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 30,
            height=20,
            placeholder_text=10,
        )
        self.line_space.grid(row = 2, column = 3, pady = 5, padx=5)

        #Label referig to the printing height
        self.z_layer=customtkinter.CTkLabel(
        master = self.para_frame,
        text="layer height",
        )
        self.z_layer.grid(row = 3, column = 0, pady = 5, padx=5)

        #Entry to indicate the prining height 
        self.z_layer_v=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 30,
            height=20,
            placeholder_text="1",
        )
        self.z_layer_v.grid(row = 3, column = 1, pady = 5, padx=5)

        #Label to indicate the printing speed
        self.speed=customtkinter.CTkLabel(
        master = self.para_frame,
        text="Speed [mm/min]",
        )
        self.speed.grid(row = 3, column = 2, pady = 5, padx=5)

        #Entry to indicate the printing speed
        self.speed_v=customtkinter.CTkEntry(
            master = self.para_frame,
            width = 60,
            height=20,
            placeholder_text="500",
        )
        self.speed_v.grid(row = 3, column = 3, pady =5, padx=5)



        #### test_frame ####
        #This frame is opened by the button depose, it allows to move the printer head on the Y axes and to print a line with defined parameters

        #Button to move from minus the line_space in y 
        self.p_line = customtkinter.CTkButton(
            master =self.test_frame,
            text="Previous Position",
            command = lambda: self.printer.prev_position() if self.test_sent_parameters() else None,
            width=80,
            height=30,
        )
        self.p_line.grid(row=0,column=0, pady=2, padx=2)

        #Buton to print 1 line with the defined parameters
        self.draw_line = customtkinter.CTkButton(
            master =self.test_frame,
            text="Print Line",
            command=lambda: self.printer.print_line() if self.test_sent_parameters() else None,
            width=80,
            height=30,
        )
        self.draw_line.grid(row=0,column=1, pady=2, padx=2)

        #Button to move from plus the line_space in y 
        self.n_line = customtkinter.CTkButton(
            master =self.test_frame,
            text="Next Position",
            command = lambda: self.printer.next_position() if self.test_sent_parameters() else None,
            width=80,
            height=30,
        )
        self.n_line.grid(row=0,column=2, pady=2, padx=2)




        #####print_frame########

        #Button to open a window allowing to choose a file and save the path to this file
        self.filebtn = customtkinter.CTkButton(
            master =self.print_frame,
            text="Choose file",
            command = self.choose_file,
            width=80,
            height=30,
        )
        self.filebtn.grid(row=0,column=1, pady = 2, padx=2)

        #Label for the drying time
        self.wait_time_l=customtkinter.CTkLabel(
            master = self.print_frame,
            text="Drying time\nbetween layers (minutes)",
        )
        self.wait_time_l.grid(row = 1, column = 0, columnspan=2,  pady = 10, padx=2)

        #Entry for the drying time in minutes
        self.wait_time_entry=customtkinter.CTkEntry(
            master = self.print_frame,
            width = 60,
            height=20,
            placeholder_text="60",
        )
        self.wait_time_entry.grid(row = 1, column = 2, pady = 10, padx=2)

        #Button to start the g-code define with the filebtn
        self.start_gcode = customtkinter.CTkButton(
            master =self.print_frame,
            text="start print",
            command = self.send_gcode,
            width=80,
            height=30,
        )
        self.start_gcode.grid(row=2,column=0, pady=10, padx=2)

        #Button to skip the drying time and start the next layer, defaults to disabled outside of ongoing print
        self.next_layer_btn = customtkinter.CTkButton(
            master =self.print_frame,
            text="next layer",
            command=self.print_next_layer,
            width=80,
            height=30,
        )
        self.next_layer_btn.grid(row=2,column=1, pady=10, padx=2)
        self.next_layer_btn.configure(state="disabled")

        #Button to stop an ongoing print without quitting the whole GUI
        self.stop_btn = customtkinter.CTkButton(
        master =self.print_frame,
        text="stop print",
        command = lambda: [self.printer.stop_print(),self.pneumatic.stop_print()],
        width=80,
        height=30,
        )
        self.stop_btn.grid(row=2,column=2, pady=10, padx=2)
        self.stop_btn.configure(state="disabled")

        
        
        ### substrat frame ####

        #Button to print multiple lines in a row on the substrat
        self.test_sub_btn = customtkinter.CTkButton(
            master =self.substrat_frame,
            text="Test sandard sample",
            command=self.run_test_sub,
            width=80,
            height=30,
        )
        self.test_sub_btn.grid(row = 0, column = 0, pady = 2, padx=2)

        #Button to print a circle (tested but doesn't work really well)
        self.test_full_rect_btn = customtkinter.CTkButton(
            master =self.substrat_frame,
            text="Test full rectangle",
            command=self.printer.test__full_rectangle,
            width=80,
            height=30,
        )
        self.test_full_rect_btn.grid(row = 0, column = 1, pady = 2, padx=2)
        
        #we start a loop to regularly send info to the ethercat
        self.window.after(2000,self.send_loop) 
        

        self.window.mainloop()
    

    def print_next_layer(self):
        """change the state of go_next_layer to 1
        """
        self.printer.go_next_layer=1
    
    def quit(self):
        """Stop pneumatic and printer comunicaqtion and close the window
        """
        self.pneumatic.stop_c_program()
        self.printer.kill_thread()
        if self.printer.homed:
            self.printer.p.disconnect()
        self.window.destroy() 
    
    def choose_substrat(self,sub):
        """called by the option menu of the substrat, allows to use predefned substrat characteristics
        new substrat can be added with a new elif with the name as well as adding the new name to the option "substrat_options"" 

        :param sub: name of the substrat choosen by the user
        :type sub: str
        """
        if sub=="95x95 PMMA":
            self.printer.sample_size_x=95
            self.printer.sample_size_y=95
            self.printer.line_space=5
            self.printer.sub=6

            self.t_substrat_v.configure(placeholder_text=6)
            self.x_width.configure(placeholder_text=95)
            self.y_width.configure(placeholder_text=95)
            self.line_space.configure(placeholder_text=5)
        elif sub=="120x70 PMMA":
            self.printer.sample_size_x=70
            self.printer.sample_size_y=120
            self.printer.line_space=10
            self.printer.sub=5

            self.t_substrat_v.configure(placeholder_text=6)
            self.x_width.configure(placeholder_text=70)
            self.y_width.configure(placeholder_text=120)
            self.line_space.configure(placeholder_text=5)
        elif sub=="60x60 PMMA":
            self.printer.sample_size_x=60
            self.printer.sample_size_y=60
            self.printer.line_space=5
            self.printer.sub=6

            self.t_substrat_v.configure(placeholder_text=6)
            self.x_width.configure(placeholder_text=60)
            self.y_width.configure(placeholder_text=60)
            self.line_space.configure(placeholder_text=5)
        else:
            self.printer.sample_size_x=120
            self.printer.sample_size_y=120
            self.printer.line_space=5
            self.printer.sub=6

    def lock_gui(self):
        """allows to lock or unlock the GUI to prevent certain actions by the user during a print
        """
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
            self.homing_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.next_layer_btn.configure(state="normal")
            self.x_width.configure(state="disabled")
            self.y_width.configure(state="disabled")
            self.t_substrat_v.configure(state="disabled")
            self.line_space.configure(state="disabled")


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
            self.homing_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.next_layer_btn.configure(state="disabled")
            self.x_width.configure(state="normal")
            self.y_width.configure(state="normal")
            self.t_substrat_v.configure(state="normal")
            self.line_space.configure(state="normal")
            self.locked=0



    def send_loop(self):
        """Loop occuring every 500ms to update the GUI 
        """
        #could be improved by sending only if changed happened 
        self.update() 
        self.pneumatic.sendToClient(1)
        if self.locked!=self.printer.on_going_print:
            self.lock_gui()
        self.window.after(500,self.send_loop)


    def choose_file(self):
        """method to open a window that lets the user choose a file to print, currently crashed if used multiple times
        """

        
        self.window.update()
        self.filePath = ""
        self.filePath  = easygui.fileopenbox()#the fd.askopenfile() was making the GUI crash, this one works better
        self.window.update()
        """

        #let's try a second method from stackoverflow:
        root = Tk(); root.attributes('-alpha',0.01)
        root.attributes('-topmost',True)
        root.tk.eval(f'tk::PlaceWindow {root._w} center')
        root.withdraw()
        self.filePath = ""
        self.filePath  = fd.askopenfilename()
        root.destroy()"""

    def test_sent_parameters(self):
        """here check if parameters input by user are valide and disply when needed an error
        """
        if self.z_layer_v.get()!='':
            if float(self.z_layer_v.get())>=self.printer.min_z and float(self.z_layer_v.get())<=self.printer.max_z:
                self.printer.z=float(self.z_layer_v.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a Z higher than 0.1mm")
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
                tk.messagebox.showinfo("send g-code", "Please choose a speed higher than 500 and lower than 12000")
                return 0
        if self.x_width.get()!='':
            if float(self.x_width.get())>0 and float(self.x_width.get())<=self.printer.bed_max_x:
                self.printer.sample_size_x=float(self.x_width.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a x width higher than 0 and lower than 210")
                return 0

        if self.y_width.get()!='':
            if float(self.y_width.get())>0 and float(self.y_width.get())<=self.printer.bed_max_y:
                self.printer.sample_size_y=float(self.y_width.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a y length higher than 0 and lower than 250")
                return 0

        if self.line_space.get()!='':
            if float(self.line_space.get())>0 and float(self.line_space.get())<=100:
                self.printer.line_space=float(self.line_space.get())
            else:
                tk.messagebox.showinfo("send g-code", "Please choose a line space higher than 0 and lower than 100")
                return 0
        return 1


    def run_test_sub(self):
        """method to test the parameters before starting the method test_sample
        """
        if self.test_sent_parameters():
            self.printer.test_sample()

    def send_gcode(self):
        """Method to start a g-code from a file
        """
        if self.filePath.endswith(".gcode"):
            self.printer.multilayer_print=1
            self.printer.load_gcode(self.filePath)
            self.printer.get_line_and_modify()
        else:
            tk.messagebox.showinfo("send g-code", "Please choose a g-code file")

    def gcodeF(self):
        """opening the g-code frame with options to start g-code from a file. First connection with the printer is started and a homing is made, be careful homing can't be cancelled
        """
        def connect_and_calibrate():
            if not self.printer.connect():
                tk.messagebox.showinfo("Test g-code", "Printer is not connected")
                return
            #hide not needed btns
            self.para_frame.grid_forget()
            self.test_frame.grid_forget()
            self.substrat_frame.grid_forget()

            #make the send_g-code frame display
            self.print_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
            
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            threading.Thread(target=connect_and_calibrate, daemon=True).start()
        
        if self.printer.homed==1:
            #hide not needed btns
            self.para_frame.grid_forget()
            self.test_frame.grid_forget()
            self.substrat_frame.grid_forget()

            #make the send_g-code frame display
            self.print_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")


    def test_depose(self):
        """opening the test depose frame with options to draw lines without a file. First connection with the printer is started and a homing is made, be careful homing can't be cancelled
        """
        def connect_and_calibrate():
            if not self.printer.connect():
                tk.messagebox.showinfo("Test g-code", "Printer is not connected")
                return
            #hide not needed btns
            self.print_frame.grid_forget()
            self.substrat_frame.grid_forget()

            #make the send_g-code frame displa
            self.para_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
            self.test_frame.grid(row=4,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
        
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            threading.Thread(target=connect_and_calibrate, daemon=True).start()
        
        if self.printer.homed==1:
            #hide not needed btns
            self.print_frame.grid_forget()
            self.substrat_frame.grid_forget()

            #make the send_g-code frame displa
            self.para_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
            self.test_frame.grid(row=4,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")


    def test_substrat(self):
        """opening the g-test substrat frame with options to test a substrat with multiple line print without a file. First connection with the printer is started and a homing is made, be careful homing can't be cancelled
        """
        def connect_and_calibrate():
            if not self.printer.connect():
                print("printer not co")
                tk.messagebox.showinfo("Test g-code", "Printer is not connected")
                return
            #hide not needed btns
            self.print_frame.grid_forget()
            self.test_frame.grid_forget()

            #make the send_g-code frame displa
            self.para_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
            self.substrat_frame.grid(row=4,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
        
        if self.printer.homed==0:
            tk.messagebox.showinfo("Test g-code", "Calibration will start, make sure only the Prusa Bed is mounted on the printer") 
            threading.Thread(target=connect_and_calibrate, daemon=True).start()
        
        if self.printer.homed==1:
            #hide not needed btns
            self.print_frame.grid_forget()
            self.test_frame.grid_forget()

            #make the send_g-code frame displa
            self.para_frame.grid(row=3,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")
            self.substrat_frame.grid(row=4,column=1,rowspan=1, columnspan=1, padx=5, pady=5, sticky="n")



    def onF(self,case):
        """function to control the 3 solenoid valves from the GUI with switch

        :param case: string to indicate which switch was activated, 'p' for pointeau (nozle), 'c' for cartouche (pressure on the fluid), 'a' for atomization (spaying pressure)
        :type case: str
        """
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
            if self.pneumatic.st_ato:
                self.on_ato.configure(text = "OFF")
                self.pneumatic.st_ato = 0
            else:
                self.on_ato.configure(text = "ON")
                self.pneumatic.st_ato = 1

    def sliderFc(self, value):
        """method to update the label of the cartouche based on the slider

        :param value: value between 0 and 1.7 bar with 2 digits
        :type value: float
        """
        self.pneumatic.c_cart=round(value,2)
        self.show_consi.configure(text=self.pneumatic.c_cart)


    def sliderFa(self, value):
        """method to update the label of the atomization based on the slider

        :param value: value between 0 and 2 bar with 2 digits
        :type value: float
        """
        self.pneumatic.c_ato=round(value,2)
        self.show_consiA.configure(text=self.pneumatic.c_ato)
  
    
    def update(self):
        """update every label and slider according to the current values on the pneumati elements
        """

        #update the labels
        self.show_consi.configure(text=self.pneumatic.c_cart)
        self.show_consiA.configure(text=self.pneumatic.c_ato)

        #update the slides
        self.cart_bar.set(self.pneumatic.c_cart)
        self.ato_bar.set(self.pneumatic.c_ato)

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
        if self.pneumatic.st_ato:
            self.on_ato.configure(text = "ON")
            self.on_ato.select()
        else:
            self.on_ato.configure(text = "OFF")
            self.on_ato.deselect()
        
        if self.wait_time_entry.get()!='':
            self.printer.wait_minutes=float(self.wait_time_entry.get())
            
        self.window.update()

