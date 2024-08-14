Ethercat comunication documentation
=========================
The ethercat comunication is handled thanks to etherlabmaster and the exmple code provided by the etherlabmaster exemple "user" was used as starting point for the comunication.
The system is not running on a real time kernel.

.. note::
    If the PERIOD_NS (the task period) is to low the VPPM (Proportional Pressure Regulators) will face pressure drop, it works at 1ms



.. doxygenfile:: main.c
   :project: AMABA