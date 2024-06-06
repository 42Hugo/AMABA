M201 X1000 Y1000 Z1000 ; sets maximum accelerations, mm/sec^2
M203 X200 Y200 Z12 ; sets maximum feedrates, mm/sec
M204 P1250 R1250 T1250 ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2
M205 X8.00 Y8.00 Z0.40 ; sets the jerk limits, mm/sec
M115 U3.8.1 ; tell printer latest fw version
G90 ; use absolute coordinates

G28 W ; home all without mesh bed level

G21 ; set units to millimeters
G90 ; use absolute coordinates

G1 Z20 ;
G1 X10 Y10 F1000.000 ; point de départ de trajectoire 
G1 Z13.3 F1000.000 ; hauteur avec offset de 12,3mm (thorlabs + erreur)
G1 X175 E22.4 F1000.000 ; point de fin de trajectoire
G1 E-0.80000 F2100.00000 ;

G1 Z40 ;

