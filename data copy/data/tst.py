import pandas as pd
import wfdb

annotation = wfdb.rdann('C1med', 'qrs')#qrs file
print(annotation.__dict__)

wfdb.plot_wfdb(annotation=annotation, time_units='seconds')
