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
from settings import INDEX_DAY_INVESTIGATION, UNIFORM_CUTOFF, int_or_round_floating_itv, ADJUSTMENT_CUTOFF

# todo: a factor of 2.5 is considered to provide 85% retention rate, this should be changed as parameters
# 200 days =>

SimulationResult = namedtuple("SimulationResult", ("pbt", "r_rate", "w_load", "efficiency", "factor"))

memorize = True
constant = 15


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


def memorize_scheduler(constant, lastinterval):
    current_interval = 0
    while True:
        current_interval += 1
        factor = current_interval/lastinterval
        pb_success = fc.get_pb_success_from_interval_modifier(factor, difficulty=0.90)
        if random.random() < (1 - pb_success)/constant:
            return current_interval


def sim(pb, nsims, onfail, ndays=365, difficulty=settings.difficulty, factor=None, mode="SM2"):
    """simulate N_SIM times, the journey of a single card during N_DAYS, where the algorithm is set up
    such as the probablity of success when a card is shown is pb.
    Extracts two mean statistics : the true retention rate and the number of times the card was presented to the user.
    """
    # Note: statistics are collected only starting from INDEX_DAY_INVESTIGATION
    current_pb_success = pb
    if factor is None:
        factor = fc.factor_interv(pb, difficulty)
    else:
        if mode == "memorize":
            constant = factor
    nb_reviews_list = []
    n_sim = 0
    integral_real_retentions = []
    while n_sim < nsims:
        if settings.ULTRA_RANDOM_CUTOFF:
            #ndays_sim = random.randint(30*2, 30*12*4)
            while True:
                ndays_sim = int(random.expovariate(1/ndays))
                if ndays_sim > 2:
                    break
        elif UNIFORM_CUTOFF:
            ndays_sim = random.randint(int(ndays * 50 / 100), int(ndays * 150 / 100))
        else:
            ndays_sim = ndays
        integral_real_retention = 0
        if INDEX_DAY_INVESTIGATION == 0:
            decay = fc.get_decay(difficulty, 1)
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
                current_pb_success = difficulty
            if nb_days == date_due:
                number_of_review += one_or_zero_if_investigation(nb_days)
                success = random.random() < current_pb_success
                if success:
                    # the real maths used to schedule used latent_interv,
                    # because the effective interval have some constraints
                    # such as be at least 1 and be a round number, which results in a loss of precision
                    if mode == "memorize":
                        effective_interval = memorize_scheduler(constant, current_interv)
                    else:
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
                        current_pb_success = difficulty
                        interval_thresholded = normalize_with_threshold(date_due, effective_interval, ndays=ndays_sim)
                    elif onfail == "stable":
                        effective_interval = int_or_round_floating_itv(max(current_interv/math.sqrt(factor), 1))
                        date_due = date_due + effective_interval
                        interval_thresholded = normalize_with_threshold(date_due, current_interv, ndays=ndays_sim)
                        current_pb_success = difficulty
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


def generate_list_of_factors():
    # trick to get this kind of factor 1.0, 1.1, 1.2, 1.25, 1.3, 1.3333333333333333
    # Why ? These factors produce sensible enough different simulations because intervals are integers
    # Intervals get rounded if they become float, so for the sake of the simulation, let's pick factors that
    # would result in neat intervals
    
    # How ? : take the results of fractions.
    return [i / 120 for i in range(3 * 60, 10 * 200) if (i % 30 == 0) or (i % 40 == 0) or (i % 12 == 0)]


def build_sim(nsimsbyfactor, onfail, ndays, difficulty, param, mode="SM2"):
    pbt = fc.get_pb_success_from_interval_modifier(param / 2.5, difficulty)
    l = sim(pbt, nsims=nsimsbyfactor, onfail=onfail, ndays=ndays, difficulty=difficulty, factor=param, mode=mode)
    quotient = l[0] / l[1]
    return SimulationResult(pbt, l[0], l[1], quotient, param)


def analyse(input):
    try:
        with open(input, "rb") as picklefile:
            total_output = pickle.load(picklefile)
    except:
        raise Exception("problem with input file. Either run a simulation with --run or give a file filepath")
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


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(description="run or analyse simulation of spaced repetition algorithm")
    my_parser.add_argument("--run", action="store_true")
    my_parser.add_argument("--runopti", action="store_true")
    my_parser.add_argument("--runoptimemorize", action="store_true")
    my_parser.add_argument("--analyse", action="store_true")
    my_parser.add_argument("--input", nargs="?", type=str)
    my_parser.add_argument("--onfail", nargs="?", type=str, default="reset")
    my_parser.add_argument("--output", nargs="?", type=str)
    my_parser.add_argument("--outputdir", nargs="?", type=str)
    my_parser.add_argument("--nsimsbyfactor", nargs="?", type=int, default=settings.nsimsbyfactor)
    my_parser.add_argument("--verbose", action="store_true")
    my_parser.add_argument("--ndays", nargs="?", type=int, default=settings.ndays)
    my_parser.add_argument("--difficulty", nargs="?", type=float, default=settings.difficulty)
    args = my_parser.parse_args()
    
    nsimsbyfactor = args.nsimsbyfactor
    onfail = args.onfail
    ndays = args.ndays
    verbose = args.verbose

    if args.runoptimemorize:
        if args.outputdir:
            os.mkdir(args.outputdir)
        else:
            raise ValueError("you need to specify output directory (--outputdir)")
        list_of_q = range(1, 30, 2)
        step = 1
        end = 98
        success_rate = 65
        while success_rate <= end:
            success_rate += step
            difficulty = success_rate/100
            total_output = []
            for q in list_of_q:
                total_output.append(build_sim(nsimsbyfactor, onfail, ndays, difficulty, q, mode="memorize"))
            if verbose:
                best_productivity = max(total_output, key=itemgetter(3))
                print(success_rate, *best_productivity)
            with open(args.outputdir+"/"+str(success_rate)+".pkl", "wb") as picklefile:
                pickle.dump(total_output, picklefile)
        exit(0)
        
    if args.runopti:
        if args.outputdir:
            os.mkdir(args.outputdir)
        else:
            raise ValueError("you need to specify output directory (--outputdir)")
        list_of_factors = generate_list_of_factors()
        step = 1
        end = 98
        success_rate = 65
        while success_rate <= end:
            success_rate += step
            difficulty = success_rate/100
            total_output = []
            for factor in list_of_factors:
                total_output.append(build_sim(nsimsbyfactor, onfail, ndays, difficulty, factor))
            if verbose:
                best_productivity = max(total_output, key=itemgetter(3))
                print(success_rate, *best_productivity)
            with open(args.outputdir+"/"+str(success_rate)+".pkl", "wb") as picklefile:
                pickle.dump(total_output, picklefile)
        exit(0)
            
    if args.run:
        vals_to_print = []
        total_output = []
        list_of_factors = generate_list_of_factors()
        #print_alert_incorrect_spots(list_of_factors, args.ndays)
        focus_output = []
        difficulty = args.difficulty
        for factor in list_of_factors:
            total_output.append(build_sim(nsimsbyfactor, onfail, ndays, difficulty, factor))
        if args.output:
            with open(args.output, "wb") as picklefile:
                pickle.dump(total_output, picklefile)
        if args.verbose:
            analyse(args.output)
        exit(0)

    if args.analyse:
        input = args.input
        analyse(input)
