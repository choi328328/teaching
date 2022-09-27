# R에서 metafor 패키지 설치해야함.
import matplotlib.pyplot as plt
import os
import argparse
from loguru import logger
from agg_utils import ple_aggregation
from pathlib import Path
import zipfile
import pandas as pd
import pyreadr

plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("--inpath", default="./data2")

args = parser.parse_args()

# os.chdir(
#     "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/aggregator"
# )
os.makedirs("./results", exist_ok=True)


if __name__ == "__main__":
    args.inpath = "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/data/CTcont/CT_AUMC"
    os.chdir(
        "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/aggregator"
    )
    logger.add("./log.log")
    sources = [
        i.split(".zip")[0] for i in os.listdir(args.inpath) if i.endswith(".zip")
    ]  # name of hospitals(data sources)

    for source in sources:
        my_zip = zipfile.ZipFile(os.path.join(args.inpath, f"{source}.zip"))

        my_zip.extractall(args.inpath)
        refer_path = [
            i for i in my_zip.namelist() if i.endswith("outcomeModelReference.rds")
        ][0]
        refer = pyreadr.read_r(os.path.join(args.inpath, refer_path))[None].query(
            'strataFile != "" '
        )
        outcomes = refer["outcomeId"].drop_duplicates().astype(int).tolist()

        csv_name = "analysisSummary.csv"
        path = [i for i in my_zip.namelist() if i.endswith(csv_name)][0]
        summ = pd.read_csv(my_zip.open(path))
        summ = summ[summ["outcomeId"].map(lambda x: x in outcomes)]
        summ = summ[
            [
                "analysisId",
                "outcomeName",
                "comparatorName",
                "targetName",
                "rr",
                "ci95lb",
                "ci95ub",
                "p",
                "target",
                "comparator",
            ]
        ]  # only required columns
        for i in ("rr", "ci95lb", "ci95ub", "p"):
            summ.loc[:, i] = summ.loc[:, i].map(lambda x: round(x, 3))

        summ["HR"] = summ.apply(
            lambda x: str(x["rr"])
            + "("
            + str(x["ci95lb"])
            + "-"
            + str(x["ci95ub"])
            + ")",
            axis=1,
        )
        logger.info(
            f"""source: {source}, \n
                    Summary : \n
                    {summ[['outcomeName','targetName','comparatorName','HR', 'target', 'comparator']]} 
                    """
        )
