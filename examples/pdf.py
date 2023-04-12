#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")

import microlog

import time
import random
import pandas as pd
import numpy as np
from itertools import cycle

@microlog.trace
def generateDataframe(rows, cols):
    df = pd.DataFrame()
    microlog.info(f"Created Empty Dataframe, it has {len(df)} rows")
    for col in range(cols):
        df[f"city-{col}"] = [f"city-{n}" for n in range(rows)] 
        df[f"phones-{col}"] = [random.random() for n in range(rows)]
    microlog.debug(f"Filled the Dataframe with {len(df)} rows")
    return df    

@microlog.trace
def count(pdf):
    print(pdf.groupby("city-11")["phones-11"].sum().sort_values(ascending=False).head(10))

@microlog.trace
def main(run):
    count(generateDataframe(9999, 100))


if __name__ == "__main__":
    microlog.start(
        application="Pandas-DataFrame",
        version=1.0,
        info="Create a huge dataframe",
        showInBrowser=True,
        verbose=False,
    )

    print("Start Pandas DataFrame generation")
    for run in range(15):
        if run:
            time.sleep(0.21)
        print("Run iteration", run)
        main(run)
    print("Done with Pandas DataFrame")

