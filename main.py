#for the printer
from printer_control import Printer
#for the pneumatic control with ethercat
from pneumatic_control import Pneumatic
#for the GUI
from amaba_gui import amabaGUI

shared_pneumatic=Pneumatic()#shard object that we'll ba passed to the 2 others so they can both interact with it

printer = Printer(shared_pneumatic)
GUI = amabaGUI(shared_pneumatic, printer)