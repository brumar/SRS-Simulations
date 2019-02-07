import copy
import random
import pickle
import math
import os
from operator import itemgetter
import forgetting_curve as fc
from collections import namedtuple
import argparse
import settings
from settings import INDEX_DAY_INVESTIGATION, RANDOM_CUTOFF, int_or_round_floating_itv, ADJUSTMENT_CUTOFF

# todo: a factor of 2.5 is considered to provide 85% retention rate, this should be changed as parameters
# 200 days =>

SimulationResult = namedtuple("SimulationResult", ("pbt", "r_rate", "w_load", "efficiency", "factor"))


def normalize_with_threshold(date_due, effective_interval, ndays):
    """cut an interval if it is longer then the number of days of the simulation"""
    # because there is no need to count days that won't be included
    if date_due <= ndays:
        return effective_interval
    else:
        delta = date_due - ndays
        return effective_interval - delta


def one_or_zero_if_investigation(nb_days):
    """count only review if its in the investigation period"""
    if nb_days > INDEX_DAY_INVESTIGATION:
        return 1
    else:
        return 0


def sim(pb, nsims, onfail, ndays, difficulty=settings.difficulty, factor=None):
    """simulate N_SIM times, the journey of a single card during N_DAYS, where the algorithm is set up
    such as the probablity of success when a card is shown is pb.
    Extracts two mean statistics : the true retention rate and the number of times the card was presented to the user.
    """
    # Note: statistics are collected only starting from INDEX_DAY_INVESTIGATION
    current_pb_success = pb
    if factor is None:
        factor = fc.factor_interv(pb, difficulty)
    nb_reviews_list = []
    n_sim = 0
    integral_real_retentions = []
    while n_sim < nsims:
        if settings.ULTRA_RANDOM_CUTOFF:
            #ndays_sim = random.randint(30*2, 30*12*4)
            while True:
                ndays_sim = int(random.expovariate(1/365))
                if ndays_sim > 2:
                    break
        elif RANDOM_CUTOFF:
            ndays_sim = random.randint(int(ndays * 50 / 100), int(ndays * 150 / 100))
        else:
            ndays_sim = ndays
        integral_real_retention = 0
        if INDEX_DAY_INVESTIGATION == 0:
            decay = fc.get_decay(settings.difficulty, 1)
            integral_real_retention += fc.real_retention_rate_by_interval(decay, 0, 1)
        n_sim += 1
        date_due = 1
        current_interv = 1
        number_of_review = 0
        nb_days = 0
        interval_thresholded_list = []
        while nb_days < ndays_sim:
            nb_days += 1
            if nb_days == 1:
                current_pb_success = settings.difficulty
            if nb_days == date_due:
                number_of_review += one_or_zero_if_investigation(nb_days)
                success = random.random() < current_pb_success
                if success:
                    # the real maths used to schedule used latent_interv, because the effective interval have some constraints
                    # such as be at least 1 and be a round number, which results in a loss of precision
                    exact_theoretical_interv = (current_interv * factor)
                    effective_interval = int_or_round_floating_itv(max(exact_theoretical_interv, 1))
                    date_due = date_due + effective_interval
                    interval_thresholded = normalize_with_threshold(date_due, effective_interval, ndays=ndays_sim)
                    current_pb_success = fc.get_current_pb_success(current_interv, interval_thresholded, difficulty)
                else:
                    # the card is reviewed ASAP
                    number_of_review += one_or_zero_if_investigation(nb_days)
                    # anki restarts everything at 0
                    if onfail == "reset":
                        effective_interval = 1
                        date_due = date_due + 1
                        current_pb_success = settings.difficulty
                        interval_thresholded = normalize_with_threshold(date_due, effective_interval, ndays=ndays_sim)
                    elif onfail == "stable":
                        effective_interval = int_or_round_floating_itv(max(current_interv/math.sqrt(factor), 1))
                        date_due = date_due + effective_interval
                        interval_thresholded = normalize_with_threshold(date_due, current_interv, ndays=ndays_sim)
                        current_pb_success = settings.difficulty
                    else:
                        raise Exception("unknown onfail value")
                        
                        # 1 more review, replaned as previously
                
                # as roundings take place, the future probability of success is not exactly pb, and must be computed
                current_interv = effective_interval
                if ADJUSTMENT_CUTOFF and date_due > ndays_sim:
                    # the card is due after the end of the simulation
                    # to be the most fair possible, we add an artificial workload malus for cards scheduled after
                    # the simulation, so that, simulations that scheduled the card just after N_DAYS get punished
                    
                    investigation_delta = (ndays_sim - INDEX_DAY_INVESTIGATION)
                    offset_delta = date_due - ndays_sim
                    number_of_review += investigation_delta / (investigation_delta + offset_delta)
                    # if offset very little (like 1) => nreview almost augmented by one
                    # if offset as large as investigation period, we add 0.5
                if date_due > INDEX_DAY_INVESTIGATION and interval_thresholded != 0:
                    # if the due date enters the investigation period, we need to collect_statistics
                    # todo: collect_statistics must be a function called separately
                    start_integral = max(INDEX_DAY_INVESTIGATION - nb_days, 0)
                    # if nb_days + interval_thresholded < N_DAYS:
                    #    end_integral = interval_thresholded
                    # else:
                    #    end_integral = N_DAYS - nb_days
                    end_integral = interval_thresholded
                    # more fair to count retention rate until the review that is after N_Days
                    decay = fc.get_decay(current_pb_success, interval_thresholded)
                    integral_real_retention += fc.real_retention_rate_by_interval(decay, start_integral, end_integral) * \
                                               (
                                                           end_integral - start_integral)  # real_retention_rate(current_pb_success) * interval_thresholded
                    interval_thresholded_list.append(interval_thresholded)
        if interval_thresholded_list:
            integral_real_retentions.append(integral_real_retention / sum(interval_thresholded_list))
        nb_reviews_list.append(number_of_review)
    real_retention_mean = sum(integral_real_retentions) / nsims
    nrev_mean = (sum(nb_reviews_list) / nsims)
    return [real_retention_mean, nrev_mean]

def get_simdata(filepath):
    return pickle.load(open(filepath, "rb"))


def remove_irrelevant_options(outputs):
    """remove points for which unambiguous better options exist (both smaller retention and bigger workload)"""
    results = outputs[:]
    print("lenght before removals " + str(len(results)))
    sorted_results = sorted(total_output, key=itemgetter(3), reverse=True)
    for r_good in sorted_results[:]:
        for r in results[:]:
            if r[1] < r_good[1] and r[2] > r_good[2]:  # smaller retention and bigger workload
                try:
                    results.remove(r)
                except:
                    pass
    print("lenght after removals " + str(len(results)))
    return results


def print_couple(v1, v2):
    print(f"{v1:0.3f},{v2:0.3f}")


def print_alert_incorrect_spots(list_of_factor, ndays):
    """select factors producing due dates around the cutoff in few steps only"""
    for f, factor in enumerate(list_of_factor):
        itv = settings.default_interval
        new_itv = itv
        nbsteps = 0
        index_day = itv
        while index_day < ndays:
            nbsteps +=1
            nbsteps = 1
            if nbsteps > 8 or index_day > ndays * 105/100:
                break
            new_itv = int_or_round_floating_itv(new_itv * factor)
            index_day += new_itv
            #print(factor, itv, ndays)
            if ndays*95/100 < index_day < ndays*105/100:
                print("the simulation may be incorrect on the viscinity of this factor " + str(factor))
    
    


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(description="run or analyse simulation of spaced repetition algorithm")
    my_parser.add_argument("--run", action="store_true")
    my_parser.add_argument("--runopti", action="store_true")
    my_parser.add_argument("--input", nargs="?", type=str)
    my_parser.add_argument("--onfail", nargs="?", type=str, default="reset")
    my_parser.add_argument("--output", nargs="?", type=str)
    my_parser.add_argument("--outputdir", nargs="?", type=str)
    my_parser.add_argument("--nsimsbyfactor", nargs="?", type=int, default=3000)
    my_parser.add_argument("--ndays", nargs="?", type=int, default=200)
    my_parser.add_argument("--difficulty", nargs="?", type=float, default=settings.difficulty)
    #my_parser.add_argument("--ndays_start", nargs="?", type=int, default=6*30)
    #my_parser.add_argument("--ndays_end", nargs="?", type=int, default=30*12*6)
    args = my_parser.parse_args()
    
    if args.runopti:
        if args.outputdir:
            os.mkdir(args.outputdir)
        list_of_factors = [i / 120 for i in range(3 * 60, 10 * 200) if (i % 30 == 0) or (i % 40 == 0) or (i % 12 == 0)]
        #print_alert_incorrect_spots(list_of_factors, args.ndays)
        step = 0.5
        end = 98
        success_rate = 69.5
        while success_rate <= end:
            success_rate += step
            total_output = []
            difficulty = success_rate/100
            # print_alert_incorrect_spots(list_of_factors, args.ndays)
            focus_output = []
            focus_output_too_high = []
            focus_output_too_low = []
            for factor in list_of_factors:
                pbt = fc.get_pb_success_from_interval_modifier(factor / 2.5, difficulty)
                l = sim(pbt, nsims=args.nsimsbyfactor, onfail="reset", ndays=1, difficulty=difficulty, factor=factor)
                quotient = l[0] / l[1]
                row = SimulationResult(pbt, l[0], l[1], quotient, factor)
                total_output.append(row)
            best_productivity = max(total_output, key=itemgetter(3))
            print(success_rate, *best_productivity)
            if args.outputdir:
                with open(args.outputdir+"/"+str(success_rate)+".pkl", "wb") as picklefile:
                    pickle.dump(total_output, picklefile)
            
    
    if args.run:
        vals_to_print = []
        total_output = []
        # trick to get this kind of factor 1.0, 1.1, 1.2, 1.25, 1.3, 1.3333333333333333
        # Why ? These factors produce sensible enough different simulations because intervals are integers 
        # Intervals get rounded if they become float, so for the sake of the simulation, let's pick factors that
        # would result in neat intervals
        
        # How ? : take floats that would be close to integers when multiplied by common integers
        list_of_factors = [i / 120 for i in range(3 * 60, 10 * 200) if (i % 30 == 0) or (i % 40 == 0) or (i % 12 == 0)]
        print_alert_incorrect_spots(list_of_factors, args.ndays)
        focus_output = []
        focus_output_too_high = []
        focus_output_too_low = []

        for factor in list_of_factors:
            pbt = fc.get_pb_success_from_interval_modifier(factor / 2.5)
            l = sim(pbt, nsims=args.nsimsbyfactor, onfail=args.onfail, ndays=args.ndays,
                    difficulty=args.difficulty, factor=factor)
            quotient = l[0] / l[1]
            row = SimulationResult(pbt, l[0], l[1], quotient, factor)
            total_output.append(row)
        if args.output:
            with open(args.outputdir, "wb") as picklefile:
                pickle.dump(total_output, picklefile)
    else:
        try:
            with open(args.input, "rb") as picklefile:
                total_output = pickle.load(picklefile)
        except:
            print("problem with input file. Either run a simulation with --run or give a file filepath")
            raise
    
    
    print("only good points taken")
    new_output_cleaned = remove_irrelevant_options(total_output)
    for output in new_output_cleaned:
        print_couple(output[2], output[1])
    
    print(" ")
    print("factors used")
    for output in new_output_cleaned:
        print(fc.factor_interv(output[0]), output)
    print("factor value versus retention rate")
    
    print(" ")
    print("factor value versus retention rate")
    print("----------")
    for output in total_output:
        print_couple(output.factor, output.r_rate)
    
    print(" ")
    print("factor value versus efficiency")
    print("----------")
    for output in total_output:
        print_couple(output.factor, output.efficiency)
    print(" ")
    print("factor value versus work")
    print("----------")
    for output in total_output:
        print_couple(output.factor, output.w_load)
    
    
    print("outputs : recall proba, real retention rate, workload, retention/workload")
    best_productivity = max(total_output, key=itemgetter(3))
    print("best_productivity")
    print(best_productivity)
    print("factor used")
    print(best_productivity.factor)

    least_work = min(total_output, key=itemgetter(2))
    print("least work")
    print(least_work)
    print("factor used")
    print(least_work[4])
    for output in total_output:
        if output[0] == settings.difficulty:
            print("workload on default algorithm")
            print(output)
            break
