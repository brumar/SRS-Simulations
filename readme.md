## Notes
Track the workload and retention rate related to a single card in the spaced repetition algorithm. Multiple simulations are runned and meaned for each parameter.
- Tested with python3.7
- No dependencies. 
- Use an external tool of your own to plot the data which are printed. I use http://www.alcula.com/calculators/statistics/scatter-plot/

## Run and analyse the simulation
`python workload_simulation.py --run --output data.pkl` 
`data.pkl` is the filename you chooe where the results of the simulation will be stored. Only your own python can load this file which is just the serialization of a python object.

## Not run, just analyse the pkl file to gain time
`python workload_simulation.py --input data.pkl`. 
