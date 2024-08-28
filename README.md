AMABA
======

AMABA: Additive Manufacturing of Aqueous Phase Material-Based Actuators

This repository provides an intuitive Graphical User Interface (GUI) for testing and experimenting with the additive manufacturing of aqueous phase materials.

Features
--------

- G-code injection for 3D printers
- EtherCAT control for three pneumatic valves
- Easy testing on various substrates

<!-- 
Documentation regarding installation and usage of the project can be found in the Sphinx documentation. Please refer to the following path: `documentation/docs/build/html/index.html`.
-->


Installation
------------

To use AMABA, first make sure etherlabmaster is supported. A first test was made with a Raspberry Pi 2b and it wasn't successful. The installation was then made on the Raspberry Pi 5 following the installation described [here](https://embeng.dynv6.net/igh-ethercat-master-on-bbb-rpi). There is no need for a real-time kernel, and the standard Raspbian OS 64-bit was enough.

After installation, the basic commands needed are:

```console
sudo ethercatctl start
```

Then check if you can detect the slaves linked to the Beckhoff coupler:

```console
ethercat slaves
```

If yes, then the installation worked and it's enough for the rest of the project. Otherwise, try installing the etherlabmaster repositories again or change the hardware.

If it hasn't been done already, clone the project:

```console
git clone https://github.com/42Hugo/amaba.git
```

You can then change the file `main.c` located in the example user of the etherlabmaster project to the one provided in the amaba project.

```console
cd etherlabmaster/examples/user
```

Then you can compile the new version of `main.c`. The makefile is already provided in the standard etherlabmaster project and should make a file called `ec_user_example`.

```console
sudo make
```

In `pneumatic_control.py`, you have to change the directory of the `ec_user_example` file to the one you just compiled.

```python
self.process = subprocess.Popen(['/home/amaba/Desktop/dev_ws/ighEthercat/ethercat/examples/user/ec_user_example'],  stdin=subprocess.PIPE)
```

Depending on the USB port you're using, you might have to change the port in the `printer_control.py` file:

```python
self.serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
```

If you're using a Raspberry Pi, you'll have to create a Python virtual environment to install the required packages. It is usually recommended:

```python
pip install customtkinter # this is a custom tkinter version that is needed for the GUI
pip install printrun # this is the package that will allow you to send G-code to the printer
```

And any other package that might be missing.

Start the GUI by running the `main.py` file. The right Python virtual environment should be activated:

```console
python main.py
```

The `run_amaba.sh` file will start a defined virtual environment and run the `main.py` file to start the GUI.

