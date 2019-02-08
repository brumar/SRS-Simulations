# SRS Simulations

## Rationale for this simulation

Anki allows the user to change a crucial parameter in the spaced repetition algorithm.
As you may know, intervals (delay between revisions) can get modified by an Interval Modifier (IM).

The Interval Modifier and the Retention Rate have a precise mathematical relation.
This relation is often used by Anki users to adjust their retention rate.

The relation between the quantity of work and these two variables is less clear. One can be tempted to try large IM's in order to have less work, but as failed cards got an (almost) hard reset, this strategy may or may not backfire by asking the user even more work.

Efficiency is a concept that has its importance in this context. A user who has not a limited set of cards to learn may want to optimize his ratio overall retention rate/work. If he spends less time reviewing, he can spend more on learning new things. 

Are there optimal Interval Modifiers that optimize Efficiency?

## Glossary

**Workload** : Average number of reviews of a single card during the simulation.

**Success Rate** : Probability of answering "yes" at card. Supposed to be constant during a single simulation. I avoided the term retention rate to prevent confusion with "overall retention rate" defined below.

**Overall Retention Rate** : Average success rate if the user was tested at **any random moment** during the simulation. I reger

**Efficiency** : Overall Retention rate / Workload

**Factor** : The constant responsible for the spacing (Interval2 = factor * Interval1). Supposed to be constant during a single simulation.

**IM** : Interval Modifier. The ratio between two factors. By default, this relates to SM2 default factor(2.5). IM = newfactor/2.5

**Period of investigation** : Average length of a simulation (the number of days the card history is tracked).

**Better** : Better efficiency. In the rest of the article, I won't precise that we are in the context of efficiency searching.

## Key results

First of all, this is important to know that these results are valid under a set of assumptions. The main one being that the SM2 memory model is right.

Under default parameters :

- SM2 is pretty inefficient. According to its own model, it clearly values quality over efficiency (see footnote).
- Optimal IM are very sensitive to the user default retention rate. Still, an IM of 140% has always a better efficiency than the default algorithm. If you have a success rate larger than 80%, it can be raised as follow (a more complete plot is provided):
- 70% success -> IM 140%, -5pt retention, -18% workload
- For the "default" 90% success rate, optimized IM is suggested at 270%. Compared to the default IM, it costs -5pts in overall retention traded against 33% less work.
- For a 95% success rate, the optimized IM at 430% cost -4.6 points in overall retention for a decreased workload of 44%.
- Workload have an U shape while retention is (almost) a straight line. This means that large IMs can provides both more work AND less retention than optimal IMs. It's then more damaging to shift optimized IM to the right (equivalent workload for less retention) than to the left.
- The efficiency optimum is very close to provide the same amount of work than the factor givin this optimum (i.e the factor where you have to review your card the least possible).
- Changing the period of investigation does not really change the results.

Few plots:

- [workload for 70% success rate](./images/70_l.png)  
- [retention for 70% success rate](./images/70_ret.png)  
- [efficiency for 70% success_rate](./images/70_ef.png)  
- [workload for 85% success rate](./images/85_l.png)  
- [retention for 85% success rate](./images/85_ret.png)  
- [efficiency for 85% success rate](./images/85_ef.png)

The most useful ones :
- [optimized factors Vs success rate](./images/all.png)
- [retention loss and workload fraction after optimization compared to SM2](./images/all_comparedSM2.png)

## Behind the hood

### How the simulation works

The idea is to follow the path of a single card during 2000 days.
We roll the random module to decide whether or not the card is failed and we schedule this card accordingly (Intervals got multiplied by factor).
We run 10 000 simulations for each factor. Factors are chosen as fractions (2.666, 2.75 etc...) in order to have meaningful distinctions (intervals are rounded).
For each simulation we count :
- How many times the card has been reviewed
- How well this card has been known over time (with a subtlety, integrals are computed to answer to the question
"If I was interrogated at any time during the investigation period, how would have I succeeded ?".).
That's why I used the term "overall retention rate" for less ambiguity.

As the success rate of the user has a large impact on the result of the simulations, we ran this whole set of simulations for a range of success rate between 0.70 and 0.98.


### Assumptions and simplifications

SM2 algorithm schedule cards so that they are at X% chance to be succeeded (X depends on the user and his cards so this is a parameter of the model) 
Failed cards are reviewed ASAP then the day after. After that, they retrieve their normal flow.
The first steps are : 1day, factor days, factor * factor ...etc...
If the interval is a float, its rounded so that it's a number of days
No grading (easy, good etc..). The multiplicative factor stay constant (like only good/fail).
No randomness was added in the dates related to the scheduling or the reviewing of the cards.
All reviews represent the same unity of work (learning, relearning included).

Many of these factors can be changed. If you think that one must be changed or passed as a parameter of the model, tell me, or fork me and PR me. 
The code here is not perfect, you may be put off by the big-fat-loop of the simulations. Sorry about that.

### The problem of the cutoff

Every simulation has an end. In the context of spaced repetition, choosing the end has consequences.
Let say I put a static limit at 200 days. On the opposite, if the card is planed just before, we have just the opposite effect. I identified two ways to counteract this limit. If the card is reviewed just before the 200 days cutoff, the simulation got more workload for not a big increase in retention. After many trial and errors (see footnote 2). I opted in for a random cutoff following an exponential distribution pararametrized so that the average length of a simulation is one year.


## Against the U shaped workload

This is not really a U, but you get the idea.
With a thousand feets view, this result is weird. As a user, you should always be able to trade workload against overall retention.
Is it the side-effect of an algorithm (too) harsh on failed cards ? From another angle, reseting cards is fairly counter-intuitive from a cognitive perspective. This goes a bit against the idea that storage strengh has been improved over time. 

So, what if failed cards do not deserve a full reset? I am not the first personn to suggest that of course.
Another simulation is provided with an alternative model where failed cards are less severly punished. A failed card deserve one more review during the same day, and the next interval is a fraction of the previous own (lapse on fail cards). I tried several things (stable interval, divide the interval by two) but that was not harsh enough and very large intervals were suggested by the system. I realized that if the dividing factor was not raising with the current factor, the simulation find "optimizations" for really large factors. I tried to divide by the factor itself (equivalent to go 1 interval back), but the U pattern came back. Finally I went to divide by sqrt(factor) and got a nice shaped curves. This could also be interpreted as "half a step back" since steps have a geometric progression.

Results on optimized IM are not very much different with this new algorithm.
Optimal IMs are found to be higher than the original study compared to SM2 (also with this new policy on failed cards):
- optimized IM at 230% for success rate for 70% difficulty -8pt retention, -25% workload.
- optimized IM at 370% for success rate for 90% difficulty -7pt retention, -40% workload.
- optimized IM at 580% for success rate for 95% difficulty -6pt retention, -48% workload.
The shape of the workload happens to be "fixed" ([70%](images/workload_70_after_partial_reset.png), [95%](images/workload_95_after_partial_reset.png))

An user is still able to trade workload against retention (but at an higher and higher cost once he passed through the optimized IM). I don't think the niceness of the curves are a strong argument in favor of this memory model and strategy. This would be much better to have empirical data on this subject.


## Footnotes
1. This result is not new and noted in Piotr Wosniak websites. However he thought that optimization could be done by setting an "efficient" forgetting index. This simulation shows that optimal factors depends largely on the current forgetting index of the user. And that optimized IM are associated with new F.I that vary much (between .90 and .58).

https://www.supermemo.com/help/fi.htm
"It is difficult to determine exactly what forgetting index brings the highest acquisition rate.
Simulation experiments have consistently pointed to the value of 25-30%"

2.The first is to apply bonus or malus on workload or retention rate depending on how far the next review is planned after the cutoff.
For example adding a fraction of review depending on how far the next review is planned provockes a negative effect.
The second is too have a random cutoff.
The first did not solve my problem very much (curves were malformed, and my bonus/malus system were ad'hoc and arguable).

Random cutoff, on the opposite ended up working quite well (with a lot of pain involved though, see the footnote) but that recquires to simulate more to limit the extra variance added the simulation.
After few trials, I picked a radical 'ultra random cutoff' where a single simulation is between 2 months and 4 years (uniform random).
That smoothed well the curve (with still a noticable discrepancy though).
Even with this very large smoothing, sweet spots for factors were still visible and perfectly predictible.
This is problem. At these specific sweetspots were lying the first version of our optimized factors.
That would have saved me some cpu cycles to solve a polynomial expression than running thousands of simulations.

Few plots :

- [retention](images/midsmooth_ret.png)
- [work](images/midsmooth_work.png)
- [efficiency](images/midsmooth_eff.png)

Note that without a random cutoff the curves were even uglier.

Black lines are the results of the solutions of the following equations :

- x^2 + x + 1 = 30 * 12 * 4
- x^3 + x^2 + x + 1 = 30 * 12 * 4
- x^4 + x^3 + x^2 + 1 = 30 * 12 * 4

These were the exact factor allowing the simulation to be absolutely sure to leave in (3, 4 or 5 steps).
Increasing the factor after these spots brings no benefit because the simulation won't leave in less steps the investigation period, but get more chances to get a card failed.

I changed the uniform random for a gaussian random (normal distribution) hoping to get more smoothing, which apparently made things worse.
At this point, I almost raged quit this simulation project.
Then I changed to an exponential distribution. And FINAL-FUCKING-LY, it gave something smooth.



After thinking about this, I believe this is a good model.
Each day passing, you have the same probability to get rid of your card.
