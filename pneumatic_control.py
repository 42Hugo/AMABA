#for the socket com with C
import socket
import select
import subprocess
import time

class Pneumatic:

    def __init__(self):
        #st 0 ou 1 pour controller les vannes
        self.st_cart=0
        self.st_Ato=0
        self.st_point=0

        #c pour consigne la valeur envoyé à la vanne en bar
        self.c_cart=0 #entre 0 et 2
        #self.c_point=5 #on doit envoyer 5V donc pas de souci tjrs 5V ou plus 
        self.c_ato=0 #entre 0 et 2

        #p pour la pression mesurer
        self.p_cart=0
        self.p_point=0
        self.p_ato=0

        #the g-code file path
        self.filePath=""

        self.automatic=0
    
        self.host = 'localhost'
        self.port = 12345

        #launch the c process
        self.process = self.start_c_program()

        #laucn socket
        self.client= self.start_socket()

    def start_c_program(self):
        # Start the C program as a subprocess
        #process = subprocess.Popen(['./socket'],  stdin=subprocess.PIPE)
        process = subprocess.Popen(['/home/amaba/Desktop/dev_ws/ighEthercat/ethercat/examples/user/ec_user_example'],  stdin=subprocess.PIPE)
        time.sleep(1)#there needs to be a little delay to allow the c subprocess to start
        return process

    def stop_c_program(self):
        # Terminate the C program
        print("killing c from python")
        self.process.terminate()
        self.process.wait()
    
    def start_socket(self):
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        client_socket.connect((self.host, self.port))

        #print("Connected to the server")

        return client_socket

    def stop_socket(self):
        print("closing socket from python")
        self.client.close()  


    def send_with_socket(self, mes):
        self.client.sendall(mes.encode('utf-8'))

        # Receive response
        #response = self.client.recv(1024)
        #print(f"Received from server: {response.decode('utf-8')}")

        #if mes == "0":
            #return False
        return 

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
        mes = str(state) +  str(self.st_Ato) + str(self.st_cart)+ str(self.st_point)  +presAtostr + presCartstr
        self.send_with_socket(mes)
        
        return 
