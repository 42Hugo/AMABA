printer control documentation
==============================

Initialization
^^^^^^^^^^^^^^^^

.. automethod:: printer_control.Printer.__init__

Connection to printer
^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: printer_control.Printer.connect

Disconnect printer
^^^^^^^^^^^^^^^^^^

.. automethod:: printer_control.Printer.kill_thread


Update pneumatic
^^^^^^^^^^^^^^^^^^

.. automethod:: printer_control.Printer.update

Listen to printer resonse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: printer_control.Printer.response_callback

Stop print
^^^^^^^^^^^^^^

.. automethod:: printer_control.Printer.stop_print


Gcode handling
^^^^^^^^^^^^^^^^^^
The library printrun is used to handle the comunication with the printer including the serial comunication.
an object called p is created and is linked to the printer.
calling 'self.p.send_now('G1 X1 Y10')' is a function provided by the library to inject g-code to the printer and it is the method used to handle the g-code injection

.. automethod:: printer_control.Printer.send_gcode_routine

.. automethod:: printer_control.Printer.add_to_pile

.. automethod:: printer_control.Printer.get_line_and_modify

.. automethod:: printer_control.Printer.load_gcode

.. automethod:: printer_control.Printer.next_position

.. automethod:: printer_control.Printer.prev_position

.. automethod:: printer_control.Printer.print_line

.. automethod:: printer_control.Printer.test_sample

.. automethod:: printer_control.Printer.test__full_rectangle

.. automethod:: printer_control.Printer.homing

