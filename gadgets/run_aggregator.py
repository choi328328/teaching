# R에서 metafor 패키지 설치해야함.
import matplotlib.pyplot as plt
import pandas as pd
import zipfile
import os
from rpy2.robjects import r
from pretty_html_table import build_table
from pdf2image import convert_from_path
import base64
from PIL import Image
import argparse
from agg_constants import aggConstants

import pyreadr
from agg_utils import (
    get_data,
    get_data_from_sources,
    draw_ps,
    draw_km_plot,
    draw_raw_km_plot,
    draw_cov_bal,
    draw_forest_plot,
    make_html,
)

plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("--inpath", default="./data")
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
    default="adjusted",
    help="Add analysis for meta-analysis outside of zipfiles",
)

args = parser.parse_args()

os.chdir(
    "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/gadgets"
)
os.makedirs("./results", exist_ok=True)


def ple_aggregation(inpath, title, text, add_analysis, dpi, km_method):
    required_cols = aggConstants.required_cols
    sources = [
        i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")
    ]  # name of hospitals(data sources)

    (
        negative_dict,
        results_dict,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
    ) = get_data_from_sources(inpath, sources)
    negative_ids = list(negative_dict.values())[0].outcome_id
    # concated results
    results_cated = pd.concat(results_dict.values())
    results = results_cated[~results_cated["outcome_id"].isin(negative_ids)][
        required_cols
    ]

    # get study population
    tco_id = (
        results[["target_id", "comparator_id", "outcome_id"]].drop_duplicates().values
    )
    target_id, comparator_id, outcome_id = tco_id[0]  # TODO : 현재는 첫번째 TCO만 raw plot 그려줌
    km_pop_dict = {}
    for source in sources:
        my_zip = zipfile.ZipFile(os.path.join(inpath, f"{source}.zip"))
        km_pop_path = [
            i
            for i in my_zip.namelist()
            if ("StratPop" in i)
            & (f"t{target_id}_c{comparator_id}" in i)
            & (f"o{outcome_id}" in i)
        ][0]
        # ZipFile .extract (member, path=None, pwd=None)
        my_zip.extract(km_pop_path, "./results")
        km_pop = pyreadr.read_r(os.path.join("./results", km_pop_path))[None][
            ["treatment", "survivalTime", "outcomeCount"]
        ]
        km_pop_dict[source] = km_pop

    # get non significants rate of negative outcomes

    negative_cated = results_cated[results_cated["outcome_id"].isin(negative_ids)]
    negatives_nonsig = pd.DataFrame(
        negative_cated[required_cols]
        .dropna(subset=["rr"])
        .query("p>0.05")
        .groupby("source")
        .count()["rr"]
    )
    negatives_nonsig.columns = ["Negative outcomes"]
    negatives_nonsig["Non-signifcant percent"] = (
        negatives_nonsig["Negative outcomes"] / len(negative_ids) * 100
    )

    # get attrition dataframe
    attrition_cated = pd.concat(attrition_dict.values())
    attritions = attrition_cated.pivot(
        index=["source", "cohort",], columns="description", values="subjects"
    )

    # if additional analysis(from other paper) is added, add it to results
    if add_analysis:
        for anal in add_analysis:
            results = results.append(
                pd.DataFrame(
                    {
                        "source": anal[0],
                        "target_id": -999,
                        "comparator_id": -999,
                        "outcome_id": -999,
                        "rr": 1,
                        "ci_95_lb": 0,
                        "ci_95_ub": 1,
                        "p": 1,
                        "target_subjects": int(anal[1]),
                        "comparator_subjects": int(anal[3]),
                        "target_outcomes": int(anal[2]),
                        "comparator_outcomes": int(anal[4]),
                    },
                    index=[0],
                )
            )

    results["target_no_outcomes"] = (
        results["target_subjects"] - results["target_outcomes"]
    )
    results["comparator_no_outcomes"] = (
        results["comparator_subjects"] - results["comparator_outcomes"]
    )
    # temporary save for using R metafor packages
    results.to_csv("./results/temp_results.csv")

    # use R metafor packages to get meta-analysis
    # metafor is selected of crenditality of results and aesthetics of plots
    r(aggConstants.metafor_script)

    # Illustrate PS distribution
    ps_fig = draw_ps(ps_dict, sources)
    ps_fig.savefig("./results/ps_density.png", dpi=dpi)

    # Illustrate covariate balance
    cov_bal_fig = draw_cov_bal(covariate_dict, sources)
    cov_bal_fig.savefig("./results/cov_bal.png", dpi=dpi)

    # Illustrate KM distribution
    km_fig = draw_km_plot(km_dict, sources)
    km_fig.savefig("./results/km_plot.png", dpi=dpi)

    km_raw_fig = draw_raw_km_plot(km_pop_dict, sources)
    km_raw_fig.savefig("./results/km_raw_plot.png", dpi=dpi)

    # Extract forest plot and save to png
    forest_fig = draw_forest_plot()
    forest_fig.savefig("./results/forest_plot.png", dpi=dpi)

    # make_html

    make_html(
        title=title,
        text=text,
        attritions=attritions,
        results=results,
        outpath="html_report.html",
        km_method=km_method,
    )


if __name__ == "__main__":
    # 외부 혹은 다른 논문에서 분석된 자료를 함께 meta-analysis하기 위해서...add_analysis 사용
    # target subject, target_outcome, comparator_subject, comparator_outcome
    add_analysis = [("Samsung", 7839, 1746, 7839, 1558)]

    ple_aggregation(
        inpath=args.inpath,
        title=args.title,
        text="Target : PACE, Comparator : No PACE, Outcome : Death",
        add_analysis=add_analysis,
        dpi=args.dpi,
        km_method=args.km_method,
    )
    print("DONE!!!!!")

