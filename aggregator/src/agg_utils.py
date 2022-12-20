import pandas as pd
import zipfile
import os
from pretty_html_table import build_table
import base64
from .agg_constants import aggConstants
from loguru import logger
import pyreadr
from pathlib import Path
import shutil
import traceback
import itertools


def get_stratpop_info(inpath, source):

    # extract temporalrily and get the rds file
    inpath = Path(inpath)
    shutil.rmtree(inpath / "script", ignore_errors=True)
    my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
    my_zip.extractall(inpath)

    filelist = []
    for root, dirs, files in os.walk(inpath):
        filelist.extend(os.path.join(root, file) for file in files)

    refer_path = [i for i in filelist if i.endswith("outcomeModelReference.rds")][0]
    refer = pyreadr.read_r(str(inpath / refer_path))[None].query('strataFile != "" ')[
        ["analysisId", "targetId", "comparatorId", "outcomeId", "strataFile"]
    ]
    refer.columns = ["a_id", "t_id", "c_id", "o_id", "pop_name"]

    def get_pop(x):
        return pyreadr.read_r([i for i in filelist if i.endswith(x)][0])[None]

    refer["t_pats"] = refer["pop_name"].map(
        lambda x: len(get_pop(x).query("treatment == 1"))
    )
    refer["c_pats"] = refer["pop_name"].map(
        lambda x: len(get_pop(x).query("treatment == 0"))
    )
    refer["t_o"] = refer["pop_name"].map(
        lambda x: len(get_pop(x).query("treatment == 1 & outcomeCount >= 1"))
    )
    refer["c_o"] = refer["pop_name"].map(
        lambda x: len(get_pop(x).query("treatment == 0 & outcomeCount >= 1"))
    )
    refer["source"] = source
    refer = refer.drop("pop_name", axis=1)
    shutil.rmtree(inpath / "script", ignore_errors=True)
    return refer


def get_data(inpath, source):
    my_zip = zipfile.ZipFile(os.path.join(inpath, f"{source}.zip"))
    csv_names = [
        "negative_control_outcome.csv",
        "covariate_balance.csv",
        "kaplan_meier_dist.csv",
        "cohort_method_result.csv",
        "attrition.csv",
        "preference_score_dist.csv",
    ]
    paths = [
        [i for i in my_zip.namelist() if i.endswith(csv_name)][0]
        for csv_name in csv_names
        if len([i for i in my_zip.namelist() if i.endswith(csv_name)]) != 0
    ]
    strat_pop = get_stratpop_info(inpath, source)

    negative_outcome, covariate_balance, km_dist, cohort_results, attrition, ps_dist = (
        pd.read_csv(my_zip.open(p)).rename(aggConstants.rename_dict, axis=1)
        for p in paths
    )
    cohort_results = cohort_results.round(3)
    cohort_results["source"] = source
    attrition["source"] = source
    attrition["cohort"] = attrition.apply(
        lambda x: "t" if x["e_id"] == x["t_id"] else "c", axis=1
    )

    return (
        negative_outcome,
        cohort_results,
        covariate_balance,
        km_dist,
        attrition,
        ps_dist,
        strat_pop,
    )


def get_data_from_sources(inpath, sources):
    (
        negative_dict,
        results_dict,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
        strat_dict,
    ) = ({} for _ in range(7))
    source_errors = []
    # get data from zipfiles
    sources = [
        source
        for source in sources
        if os.path.exists(os.path.join(inpath, f"{source}.zip"))
    ]
    for source in sources:
        try:
            (
                negative_outcome,
                cohort_results,
                covariate_balance,
                km_dist,
                attrition,
                ps_dist,
                strat_pop,
            ) = get_data(inpath, source)

            negative_dict[source] = negative_outcome
            results_dict[source] = cohort_results
            covariate_dict[source] = covariate_balance
            km_dict[source] = km_dist
            attrition_dict[source] = attrition
            ps_dict[source] = ps_dist
            strat_dict[source] = strat_pop
            logger.info(f"{source} extracted")
        except Exception:
            traceback.print_exc()
            logger.warning(f"{source} not found")
            source_errors.append(source)
    for source in source_errors:
        sources.remove(source)

    negative_ids = list(negative_dict.values())[0].o_id

    results_cated = pd.concat(results_dict.values())
    results = results_cated[~results_cated["o_id"].isin(negative_ids)][
        aggConstants.required_cols
    ]

    return (
        negative_ids,
        results,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
        strat_dict,
        sources,
    )


def make_html(
    title,
    text,
    attritions,
    results,
    outpath="html_report.html",
    km_method="adjusted",
):

    results_text = "Estimation summary"
    attrition_text = "Attritions"

    attrition2 = attritions.reset_index()
    attrition2.columns = list(attrition2.columns)
    if "Original cohorts" in attrition2.columns:
        attrition2.drop(columns=["Original cohorts"], inplace=True)

    plots = ["forest_plot", "ps_density", "cov_bal", "km_plot"]
    if km_method == "raw":
        plots[3] = "km_raw_plot"

    forest_uri, ps_uri, cov_uri, km_uri = (
        base64.b64encode(open(f"./results/{plot_name}.png", "rb").read()).decode(
            "utf-8"
        )
        for plot_name in plots
    )

    results["t(o)"] = results.apply(lambda x: f'{x["t_pats"]} ({x["t_o"]})', axis=1)
    results["c(o)"] = results.apply(
        lambda x: f'{x["c_pats"]} ({x["c_o"]})',
        axis=1,
    )
    results2 = results[aggConstants.report_cols]

    # 2. Combine them together using a long f-string
    html = f"""
        <html>
            <head>
                <title>My report</title>
            </head>
            <body>
                <h1>{title}</h1>
                <p>{text}</p>

                <h3>{results_text}</h3>
                {build_table(results2.query('o_id != -999'), 'blue_light')}
                <h3>Forest plot</h3>
                <img src="data:image/png;base64,{forest_uri}" width="900"> 
                
                <h3>Kaplan-Meier curve</h3>
                <img src="data:image/png;base64,{km_uri}" width="1100">
                
                <h3>{attrition_text}</h3>
                {build_table(attrition2, 'green_light')}
                
                <h3>PS distribution</h3>
                <img src="data:image/png;base64,{ps_uri}" width="1100">
                
                <h3>Covariate balance</h3>
                <img src="data:image/png;base64,{cov_uri}" width="1100">

            </body>
        </html>
        """

    # 3. Write the html string as an HTML file
    with open(outpath, "w") as f:
        f.write(html)


def get_cohort_name(inpath, source):
    my_zip = zipfile.ZipFile(os.path.join(inpath, f"{source}.zip"))

    analysis_summ_path = [
        i for i in my_zip.namelist() if i.endswith("analysisSummary.csv")
    ][0]

    anal_summary = pd.read_csv(my_zip.open(analysis_summ_path)).drop_duplicates()

    return {
        **dict(zip(anal_summary.outcomeId, anal_summary.outcomeName)),
        **dict(zip(anal_summary.comparatorId, anal_summary.comparatorName)),
        **dict(zip(anal_summary.targetId, anal_summary.targetName)),
        "analysis": dict(
            zip(anal_summary.analysisId, anal_summary.analysisDescription)
        ),
    }


def add_analysis_func(df, add_analysis):
    for anal in add_analysis:
        add_t, add_c, add_o = int(anal[5]), int(anal[6]), int(anal[7])
        df = df.append(
            pd.DataFrame(
                {
                    "source": anal[0],
                    "t_id": add_t,
                    "c_id": add_c,
                    "o_id": add_o,
                    "a_id": 1,
                    "t_pats": int(anal[1]),
                    "c_pats": int(anal[2]),
                    "t_o": int(anal[3]),
                    "c_o": int(anal[4]),
                },
                index=[0],
            )
        )
    return df


def check_smaller_than_5(results_filter):
    check_cols = ["t_pats", "c_pats", "t_o", "c_o"]
    error_source = []
    for (_, row), col in itertools.product(results_filter.iterrows(), check_cols):
        if row[col] <= 0:
            logger.warning(f"{row['source']} has non-positive value in {col} ")
            error_source.append(row["source"])
    results_filter = results_filter[
        ~results_filter["source"].isin(error_source)
    ].sort_values("source")
    return results_filter


def get_km_pop_dict(inpath, temp_path, sources, t_id, c_id, o_id, a_id):
    km_pop_dict = {}
    for source in sources:
        my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
        km_pop_path = [
            i
            for i in my_zip.namelist()
            if ("StratPop" in i)
            & (f"t{t_id}_c{c_id}" in i)
            & (f"o{o_id}" in i)
            & (f"s{a_id}" in i)  # a 추가해야함.
        ][0]
        # ZipFile .extract (member, path=None, pwd=None)
        my_zip.extract(km_pop_path, temp_path)
        km_pop = pyreadr.read_r(temp_path / km_pop_path)[None][
            ["treatment", "survivalTime", "outcomeCount"]
        ]
        km_pop_dict[source] = km_pop
    return km_pop_dict
