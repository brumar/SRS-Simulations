# WARNING

This documentation is bad and outdated.
Have a look on https://github.com/brumar/SRS-Simulations/blob/master/after_expo.ipynb and on https://github.com/brumar/SRS-Simulations/blob/master/article.md to get a sense of what's going on there.


## Notes
Track the workload and retention rate related to a single card in the spaced repetition algorithm. Multiple simulations are runned and meaned for each parameters.
- Tested with python3.7
- workload_simulation.py has no dependencies, but the notebooks depends on numpy, scikit-learnn matplotlib  

## Run and analyse the simulation

Examples :

`python3.7 workload_simulation.py --run --nsimsbyfactor 100 --difficulty 0.90 --output data.pkl`
`python3.7 workload_simulation.py --runopti --nsimsbyfactor 100 --outputdir ./output`


`data.pkl` is the filename you chooe where the results of the simulation will be stored. You can load safely this kind of file only in your own environment.

## Not run, just analyse the pkl file to gain time
`python workload_simulation.py --input data.pkl`.

You can also use Python notebooks.


