#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time
import random
import pandas as pd

def generateDataframe(rows, cols):
    import microlog.api as api
    df = pd.DataFrame()
    api.info(f"Created Empty Dataframe, it has {len(df)} rows")
    for col in range(cols):
        df[f"city-{col}"] = [f"city-{n}" for n in range(rows)] 
        df[f"phones-{col}"] = [random.random() for n in range(rows)]
    api.debug(f"Filled the Dataframe with {len(df)} rows")
    return df    

def count(pdf):
    print(pdf.groupby("city-11")["phones-11"].sum().sort_values(ascending=False).head(10))

def main(run):
    count(generateDataframe(9999, 100))


if __name__ == "__main__":
    def createDataFrames():
        print("Start Pandas DataFrame generation")
        for run in range(5):
            if run:
                time.sleep(0.21)
            print("Run iteration", run)
            main(run)
        print("Done with Pandas DataFrame")

    createDataFrames()
