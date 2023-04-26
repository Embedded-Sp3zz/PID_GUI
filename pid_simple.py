#Tutorial https://www.oreilly.com/library/view/intelligent-iot-projects/9781787286429/26242fa7-713e-4e5d-b1dc-b5566a39d5b7.xhtml

import time
import os.path

targetT = 35
P = 10
I = 1
D = 1

def PID(Kp, Ki, Kd, MV_bar=0):
    # initialize stored data
    e_prev = 0
    t_prev = -100
    I = 0
    print("swag")
    
    # initial control
    MV = MV_bar
    
    while True:
        # yield MV, wait for new t, PV, SP
        t, PV, SP = yield MV
        
        # PID calculations
        e = SP - PV
        
        P = Kp*e
        I = I + Ki*e*(t - t_prev)
        D = Kd*(e - e_prev)/(t - t_prev)
        
        MV = MV_bar + P + I + D

        print(MV)
        
        # update stored data for next iteration
        e_prev = e
        t_prev = t


return_val = PID(P, I, D, targetT)