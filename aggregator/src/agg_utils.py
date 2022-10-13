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


def get_stratpop_info(inpath, source):

    inpath = Path(inpath)
    shutil.rmtree(inpath / "script", ignore_errors=True)
    my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
    my_zip.extractall(inpath)
    refer_path = [
        i for i in my_zip.namelist() if i.endswith("outcomeModelReference.rds")
    ][0]
    refer = pyreadr.read_r(str(inpath / refer_path))[None].query('strataFile != "" ')
    refer_values = refer[
        ["analysisId", "targetId", "comparatorId", "outcomeId", "strataFile"]
    ].values
    src, t, c, o, a = [], [], [], [], []
    t_counts, c_counts, t_o_counts, c_o_counts = [], [], [], []

    for a_id, t_id, c_id, o_id, pop_name in refer_values:
        src.append(source)
        t.append(t_id)
        c.append(c_id)
        o.append(o_id)
        a.append(a_id)
        filelist = []
        for root, dirs, files in os.walk(inpath):
            filelist.extend(os.path.join(root, file) for file in files)
        pop = pyreadr.read_r([i for i in filelist if i.endswith(pop_name)][0])[None]
        t_counts.append(len(pop.query("treatment == 1")))
        c_counts.append(len(pop.query("treatment == 0")))
        t_o_counts.append(len(pop.query("treatment == 1 & outcomeCount == 1")))
        c_o_counts.append(len(pop.query("treatment == 0 & outcomeCount == 1")))

    shutil.rmtree(inpath / "script", ignore_errors=True)
    return pd.DataFrame(
        {
            "source": src,
            "target_id": t,
            "comparator_id": c,
            "outcome_id": o,
            "analysis_id": a,
            "target_subjects": t_counts,
            "comparator_subjects": c_counts,
            "target_outcomes": t_o_counts,
            "comparator_outcomes": c_o_counts,
        }
    )


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
        pd.read_csv(my_zip.open(p)) for p in paths
    )
    cohort_results["source"] = source
    attrition["source"] = source
    attrition["cohort"] = attrition.apply(
        lambda x: "target" if x["exposure_id"] == x["target_id"] else "comparator",
        axis=1,
    )

    return (
        negative_outcome,
        cohort_results.round(3),
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
    print(1)
    return (
        negative_dict,
        results_dict,
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

    results["target(outcome)"] = results.apply(
        lambda x: f'{x["target_subjects"]} ({x["target_outcomes"]})', axis=1
    )
    results["comparator(outcome)"] = results.apply(
        lambda x: f'{x["comparator_subjects"]} ({x["comparator_outcomes"]})',
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
                {build_table(results2.query('outcome_id != -999'), 'blue_light')}
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
    cohort_count_path = [
        i for i in my_zip.namelist() if i.endswith("CohortCounts.csv")
    ][0]

    cohort_df = pd.read_csv(my_zip.open(cohort_count_path))
    analysis_summ_path = [
        i for i in my_zip.namelist() if i.endswith("analysisSummary.csv")
    ][0]

    anal_summary = pd.read_csv(my_zip.open(analysis_summ_path))[
        ["analysisId", "analysisDescription"]
    ].drop_duplicates()

    return {
        **dict(zip(cohort_df.cohortDefinitionId, cohort_df.cohortName)),
        "analysis": dict(
            zip(anal_summary.analysisId, anal_summary.analysisDescription)
        ),
    }
