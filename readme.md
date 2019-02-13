# SRS Simulations

This documentation is more than brief for the moment.
You can have a look on analysis.ipynb and article.md to get a sense of what's going on there.

## Goal

Track the workload and retention rate related to a single card in the spaced repetition algorithm (simplified SM2 only at the moment). Multiple simulations are runned and averaged for each parameters.
- Tested with python3.7
- workload_simulation.py has no dependencies, but the notebook depends on numpy, scikit-learn matplotlib , ipywidgets

## Run and analyse the simulation

You can run.

`python3.7 workload_simulation.py --run --ndays 365 --nsimsbyfactor 100 --difficulty 0.90 --output data.pkl`

0r, to test for a range of difficulty :

`python3.7 workload_simulation.py --runopti --ndays 365 --nsimsbyfactor 100 --outputdir ./output`

0r, to print in the console the result of a simulation:

`python3.7 workload_simulation.py --analyse --input data.pkl`

`data.pkl` is the filename you chooe where the results of the simulation will be stored. You can load safely this kind of file only in your own environment.

