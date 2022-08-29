# R에서 metafor 패키지 설치해야함.
import matplotlib.pyplot as plt
import os
import argparse
from loguru import logger
from agg_utils import ple_aggregation
from pathlib import Path
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("--inpath", default="./data2")
parser.add_argument(
    "--add_analysis",
    default=None,
    help="Add analysis for meta-analysis outside of zipfiles",
)  # source, target_outcome, target_negative, comparator_outcome, comparator_negative
parser.add_argument(
    "--dpi",
    default=100,
    type=int,
    help="Add analysis for meta-analysis outside of zipfiles",
)  # source, target_outcome, target_negative, comparator_outcome, comparator_negative
parser.add_argument(
    "--title",
    default="my PLE",
    help="Add analysis for meta-analysis outside of zipfiles",
)
parser.add_argument(
    "--km_method",
    default="adjusted",  # 'raw' or 'adjusted'
    help="Add analysis for meta-analysis outside of zipfiles",
)
parser.add_argument(
    "--only_main",
    default=False,  # 'raw' or 'adjusted'
    help="Only show main results",
)

args = parser.parse_args()

# os.chdir(
#     "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/aggregator"
# )
os.makedirs("./results", exist_ok=True)


if __name__ == "__main__":
    # 외부 혹은 다른 논문에서 분석된 자료를 함께 meta-analysis하기 위해서...add_analysis 사용
    # target subject, comparator_subject, target_outcome, comparator_outcome, t,c, o_id
    # add_analysis = [("Samsung", 7839, 1746, 7839, 1558, 0, 0, 0)]
    add_analysis = [("AUMC", 454, 1785, 31, 104, 1140, 1149, 1131),
                    ("AUMC", 208, 745, 26, 59, 1143, 1150, 1131),
                    ("AUMC", 900, 3540, 55, 149, 1141, 1152, 1131)] 
    
    args.inpath = "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/data/noncardiac/noncardiac_pace_cond"
    os.chdir("/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/aggregator")
    logger.add("./log.log")
    ple_aggregation(
        inpath=args.inpath,
        title=args.title,
        add_analysis=add_analysis,
        dpi=args.dpi,
        km_method='adjusted',
    )
    logger.info("DONE!!!!!")

