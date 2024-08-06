GUI documentation
======================
The Graphical user interface is made with the library customtkinter (see documentation here: https://customtkinter.tomschimansky.com/) 
The GUI will interact with both the printer object and the pneumatic object.

Initialisation
^^^^^^^^^^^^^^^^
.. automethod:: amaba_gui.amabaGUI.__init__
    
GUI specific Methods
^^^^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: amaba_gui.amabaGUI.lock_gui

.. automethod:: amaba_gui.amabaGUI.send_loop

.. automethod:: amaba_gui.amabaGUI.gcodeF

.. automethod:: amaba_gui.amabaGUI.test_depose

.. automethod:: amaba_gui.amabaGUI.test_substrat

.. automethod:: amaba_gui.amabaGUI.onF

.. automethod:: amaba_gui.amabaGUI.sliderFc

.. automethod:: amaba_gui.amabaGUI.sliderFa

.. automethod:: amaba_gui.amabaGUI.update

Printer interaction Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: amaba_gui.amabaGUI.print_next_layer

.. automethod:: amaba_gui.amabaGUI.choose_substrat

.. automethod:: amaba_gui.amabaGUI.choose_file

.. automethod:: amaba_gui.amabaGUI.test_sent_parameters

.. automethod:: amaba_gui.amabaGUI.run_test_sub

.. automethod:: amaba_gui.amabaGUI.send_gcode


Disconnect Method
.. automethod:: amaba_gui.amabaGUI.quit
