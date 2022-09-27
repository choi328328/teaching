# R에서 metafor 패키지 설치해야함.
import matplotlib.pyplot as plt
import os
import argparse
from loguru import logger
from src.aggregation import survival_aggregation
from pathlib import Path

plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

os.makedirs("./results", exist_ok=True)


if __name__ == "__main__":

    inpath = "/Users/choibyungjin/Downloads/gas_pace"
    os.chdir(
        "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/aggregator"
    )
    # logger.add("./log.log")
    survival_df = survival_aggregation(
        inpath=inpath,
        negatives =True
    )
    survival_df.columns = [
        "source",
        "target",
        "comparator",
        "outcome",
        "HR",
        "target_n(outcome)",
        "comparator_n(outcome)",
    ]
    print(survival_df.sort_values("target"))
    survival_df.to_csv(f"./{inpath.split('/')[-1]}.csv")
    logger.info("DONE!!!!!")
