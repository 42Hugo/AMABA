from printrun.printcore import printcore
from printrun import gcoder
import time


# Callback function to handle responses from the printer
def response_callback(line):
    global current_response
    global flag
    current_response = line
    #print(f"Received: {line}")
    if "ok" in line:
        #print(f"Received: {line}")
        flag+=1


def get_line_and_modify(gcode_lines):
    depose = 0
    new_layer = 0
    global flag
    flag=0
    layer=""
    count=0

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
                    if E_value > 0 and depose==0:
                        new_layer=1
                        depose=1
                    elif E_value <= 0 and depose==1:
                        new_layer=1
                        depose=0
                    #normalement il n'y a pas de cas ou le E a juse pas de chiffre pour le stopper mais à verifier
        if new_layer==0:
            #print(f"sending: {modified_line}")
            #p.send_now(modified_line)
            layer = layer + "\n"+ modified_line
            count+=1
            
        else:
            layer= layer + "\n" + "M400"
            if depose==0:
                print("ON")#on dirait c'est inversé c'est par ce que c'est la future couche dont on a l'info dépose
            else:
                print("OFF")
            p.send_now(layer)
            #p.send_now("M400")
            #print(f"sending: {layer}")
            
            while flag!=(count+1):
                pass
            #print("ok received")
            count=1
            #si on doit commencer une nouvelle coucher, couper ou allumer la buse
            layer = ""
            #print("start new layer")
            layer = layer + "\n" + modified_line
            new_layer=0
            flag=0

    layer= layer + "\n" + "M400" 
    if depose==0:
        print("OFF")#ici c'est la couche actuel dont on a la dépose
    else:
        print("ON")  
    p.send_now(layer)
    #print(f"sending: {layer}")
    #print(count)
    while flag!=(count+1):
        pass
    #print("finished")
    return

def connect(path):
    # Start communication with the printer
    p = printcore('COM3', 115200)
    global flag
    flag = 0
    # Set the response callback
    p.loud = True
    p.recvcb = response_callback

    # Load the G-code file
    with open(path, 'r') as file_object:
        gcode_lines = file_object.readlines()

    # Wait until the printer is connected
    while not p.online:
        time.sleep(0.1)
    
    return gcode_lines


#connect ot printer and start com
gcode=connect(path)

# Modify and send the G-code lines
get_line_and_modify(gcode)

# Close the connection
p.disconnect()
