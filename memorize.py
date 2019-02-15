import random
import math
import forgetting_curve as fc

def scheduler(constant, lastinterval):
    # thinning algorithm
    current_interval = 0
    while True:
        current_interval += 1
        factor = current_interval/lastinterval
        pb_success = fc.get_pb_success_from_interval_modifier(factor, difficulty=0.90)
        #print(pb_success)
        if random.random() < (1 - pb_success)/constant:
            #print("------HIT---------")
            #print(constant, current_interval, lastinterval, pb_success)
            #print("---------------")
            return current_interval

if __name__ == "__main__":
    for constant in range(1, 20, 2):
        for last_int in range(1, 100, 10):
            sim = []
            for t in range(1000):
                sim.append(scheduler(constant, last_int))
            print(constant, last_int, sum(sim)/1000)

