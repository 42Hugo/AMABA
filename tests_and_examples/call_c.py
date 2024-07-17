import subprocess

def start_c_program():
    # Start the C program as a subprocess
    process = subprocess.Popen(['/home/amaba/Desktop/dev_ws/ighEthercat/ethercat/examples/user/ec_user_example'], stdin=subprocess.PIPE)

    return process

def stop_c_program(process):
    # Terminate the C program
    process.terminate()
    process.wait()

def main():
    # Start the C program
    c_program_process = start_c_program()

    # Example: Pause for a while to simulate your main Python code running
    try:
        while True:
            # Here you can add your main Python code that runs concurrently with the C program
            pass
    except KeyboardInterrupt:
        print("Stopping the C program...")
        stop_c_program(c_program_process)

if __name__ == "__main__":
    main()
