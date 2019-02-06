import math
import settings

def get_decay(pbt, interval):
    """get the s parameter of exp(-t/s))"""
    # math.log(pb) = -interval/decay
    return -1*(interval/math.log(pbt))

def real_retention_rate_by_interval(decay, start, end):
    """real retention rate is the integral of the forgetting curve divided by the interval"""
    return -decay*(math.exp(-end/decay) - math.exp(-start/decay))/(end-start)


def real_retention_rate(pb_success):
    """get real retention rate given the probability of success at a single time"""
    # real retention rate is by definition superior than success probability
    # source for this formula https://www.supermemo.com/help/fi.htm
    # can be computed by taking the integral between 0 and t of the the forgetting curve, divided by t itself.
    # Integral_between_0_And_TREVIEW(exp(-t/s))/TREVIEW = [-(s*e(-t/s)]0,TREVIEW 
    # = -s/TREVIEW(1/l - psucess_l/l) 
    # = - (1-p_success)/ln(exp(-TREVIEW/s)) 
    # = -(1-p_success)/ln(psuccess)
    if pb_success == 1:
        return 1
    return -(1-pb_success) / math.log(pb_success)


def factor_interv(pb, difficulty=settings.difficulty):
    """compute easiness factor, given a target of success probability"""
    # source: anki manual
    # can be retrieved by this reasonning
    # SM2 default for EF is 2.5, granting 0.85 probability success at t1 the time of interrogation
    # Multiplying EF by an extra factor would result by having a success
    # pb = exp(-extraFactor*t1/s) = (exp(-t1/s))^extraFactor = 0.85^extraFactor
    # which gives the line below
    extra_factor = math.log(pb)/math.log(difficulty)
    return settings.default_interval*extra_factor


def get_current_pb_success(old_interval, effective_interval, difficulty=settings.difficulty):
    """get probability of success given learning history"""
    factor_used = effective_interval/old_interval
    # the ratio between interval is the unique value we need to compute the probability of recall
    multiplier_used = factor_used/settings.default_interval
    return get_pb_success_from_interval_modifier(multiplier_used, difficulty)


def get_pb_success_from_interval_modifier(factor, difficulty=settings.difficulty):
    # this is derived from the formula used in the factor_interv function where pb is the value to find
    return math.exp(factor * math.log(difficulty))

