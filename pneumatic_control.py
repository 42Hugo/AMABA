#for the socket com with C
import socket
import select
import subprocess
import time

class Pneumatic:
    def __init__(self):
        #st 0 ou 1 pour controller les vannes
        self.st_cart=0
        self.st_ato=0
        self.st_point=0

        #c pour controler la valeur envoyé à la vanne en bar
        self.c_cart=0 #entre 0 et 2
        self.c_ato=0 #entre 0 et 2
        #no need of c_point as it is a constant pressure to open or close

        #the g-code file path
        self.filePath=""
    
        self.host = 'localhost'
        self.port = 12345
        self.connected=0

        #start c process and socket communication
        self.start_connection()
    
    def start_connection(self):
        try:
            #launch the c process
            self.process = subprocess.Popen(['/home/amaba/Desktop/dev_ws/ighEthercat/ethercat/examples/user/ec_user_example'],  stdin=subprocess.PIPE)
            self.connected+=1
        except:
            print("An error occured when trying to start c_process")
        
        try:
            #laucn socket
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to the server
            self.client.connect((self.host, self.port))
            self.connected+=1
        except:
            print("An error occured when trying to start the socket")

    def stop_c_program(self):
        # Terminate the C program
        ##############################################
        self.sendToClient(0)
        #to check but should make sure that everything is turned to 0 before switch off
        self.process.terminate()
        self.process.wait()
        self.client.close()  

    def sendToClient(self,state):
        self.presAto= int(self.c_ato*10)
        if (self.presAto<10):
            presAtostr="0"+str(self.presAto)
        elif (self.presAto==0):
            presAtostr="00"
        else:
            presAtostr=str(self.presAto)
        presCart= int(self.c_cart*10)
        if (presCart<10):
            presCartstr="0"+str(presCart)
        elif(presCart==0):
            presCart="00"
        else:
            presCartstr=str(presCart)
        mes = str(state) +  str(self.st_ato) + str(self.st_cart)+ str(self.st_point)  +presAtostr + presCartstr
        self.send_with_socket(mes)
        
        return 

    def send_with_socket(self, mes):
        self.client.sendall(mes.encode('utf-8'))
        return 


    def stop_print(self):
        self.st_ato=0
        self.st_cart=0
        self.st_point=0
        self.sendToClient(1)