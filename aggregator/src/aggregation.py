import itertools
import pandas as pd
import zipfile
import os
from .agg_constants import aggConstants
from .agg_plots import (
    draw_ps,
    draw_cov_bal,
    draw_km_plot,
    draw_raw_km_plot,
    draw_forest_plot,
)
from .agg_utils import (
    make_html,
    get_data_from_sources,
    get_cohort_name,
    get_stratpop_info,
)
from loguru import logger
import pyreadr
from pathlib import Path
from lifelines import CoxPHFitter


def survival_aggregation(inpath, negatives):
    sources = [
        i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")
    ]  # name of hospitals(data sources)
    km_pop_dict = {source: get_stratpop_info(inpath, source) for source in sources}
    inpath, temp_path = Path(inpath), Path("./results")
    cohort_name_dict = get_cohort_name(inpath, sources[0])

    df = pd.DataFrame()
    for source in sources:
        my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
        my_zip.extractall(inpath)
        refer_paths = [
            i for i in my_zip.namelist() if i.endswith("outcomeModelReference.rds")
        ]
        summary_paths = [
            i for i in my_zip.namelist() if i.endswith("analysisSummary.csv")
        ]
        for num, refer_path in enumerate(refer_paths):

            refer = pyreadr.read_r(str(inpath / refer_path))[None].query(
                'strataFile != "" '
            )
            refer_values = refer[
                ["analysisId", "targetId", "comparatorId", "outcomeId", "strataFile"]
            ].values

            counts_path = [
                i for i in my_zip.namelist() if i.endswith("CohortCounts.csv")
            ][num]
            cohort_info = pd.read_csv(str(inpath / counts_path))
            cohort_name_dict = dict(
                zip(cohort_info["cohortDefinitionId"], cohort_info["cohortName"])
            )

            anal_summary = pd.read_csv(str(inpath / summary_paths[num]))
            anal_summary = anal_summary.dropna(subset=["rr"])
            if negatives:
                anal_summary = anal_summary[
                    ~anal_summary["outcomeId"].isin(refer["outcomeId"])
                ]
                anal_summary["hr_ci"] = anal_summary.apply(
                    lambda x: f'{x["rr"]:.3f} ({x["ci95lb"]:.3f}-{x["ci95ub"]:.3f}) ',
                    axis=1,
                )
                anal_summary["treat_outcome"] = anal_summary.apply(
                    lambda x: f'{x["target"]} ({x["eventsTarget"]}) ', axis=1
                )
                anal_summary["nontreat_outcome"] = anal_summary.apply(
                    lambda x: f'{x["comparator"]} ({x["eventsComparator"]}) ', axis=1
                )
                anal_summary["source"] = [source] * len(anal_summary)
                negatives_summ = anal_summary[
                    [
                        "source",
                        "targetName",
                        "comparatorName",
                        "outcomeName",
                        "hr_ci",
                        "treat_outcome",
                        "nontreat_outcome",
                    ]
                ]
                df = pd.concat([df, negatives_summ], axis=0)

            for a, t, c, o, pop_name in refer_values:
                pop_path = [i for i in my_zip.namelist() if i.endswith(pop_name)][0]
                km_pop = pyreadr.read_r(inpath / pop_path)[None][
                    ["treatment", "survivalTime", "outcomeCount"]
                ]
                km_pop_dict[source] = km_pop

                # T,C,O cohort name 얻기
                t_name = cohort_name_dict.get(t)
                c_name = cohort_name_dict.get(c)
                o_name = cohort_name_dict.get(o)
                n_treat, n_nontreat = len(km_pop.query("treatment==1")), len(
                    km_pop.query("treatment==0")
                )
                treat_o, nontreat_o = int(
                    km_pop.query("treatment==1").outcomeCount.sum()
                ), int(km_pop.query("treatment==0").outcomeCount.sum())
                # cph fit 결과 및 N수를 dataframe으로 정리하기
                # csv로 결과 출력
                # source, t_name, c_name, o_name, N, p_value, HR, CI_lower, CI_upper
                if (treat_o == 0) | (treat_o == n_treat):
                    hr, p_value, lb, ub = 0, 0, 0, 0
                else:
                    cph = CoxPHFitter()
                    cph.fit(km_pop, "survivalTime", "outcomeCount")
                    hr = cph.summary["exp(coef)"].item()
                    lb = cph.summary["exp(coef) lower 95%"].item()
                    ub = cph.summary["exp(coef) upper 95%"].item()
                    p_value = cph.summary["p"].item()
                hr_ci = f"{hr:.3f} ({lb:.3f}-{ub:.3f})"  #  ,p={p_value:.4f}
                treat_outcome = f"{n_treat} ({treat_o})"
                nontreat_outcome = f"{n_nontreat} ({nontreat_o})"
                tco_df = pd.DataFrame(
                    [
                        source,
                        t_name,
                        c_name,
                        o_name,
                        hr_ci,
                        treat_outcome,
                        nontreat_outcome,
                    ]
                ).T
                tco_df.columns = [
                    "source",
                    "targetName",
                    "comparatorName",
                    "outcomeName",
                    "hr_ci",
                    "treat_outcome",
                    "nontreat_outcome",
                ]

                df = pd.concat([df, tco_df])

    return df


def ple_aggregation(
    inpath,
    report_path="./reports",
    title="PLE Aggregation",
    add_analysis=False,
    dpi=100,
    km_method="adjusted",
    target_id=0,
    comparator_id=0,
    outcome_id=0,
):
    required_cols = aggConstants.required_cols
    sources = [
        i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")
    ]  # name of hospitals(data sources)
    inpath = Path(inpath)
    temp_path = Path("./results")
    report_path = Path(report_path)
    (
        negative_dict,
        results_dict,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
        strat_dict,
        sources,  # after remove error sources
    ) = get_data_from_sources(inpath, sources)

    cohort_name_dict = get_cohort_name(inpath, sources[0])

    negative_ids = list(negative_dict.values())[0].outcome_id
    # concated results
    results_cated = pd.concat(results_dict.values())
    results = results_cated[~results_cated["outcome_id"].isin(negative_ids)][
        required_cols
    ]

    # get study population
    tcoa_id = (
        results[["target_id", "comparator_id", "outcome_id", "analysis_id"]]
        .drop_duplicates()
        .values
    )
    check_cols = [
        "target_subjects",
        "comparator_subjects",
        "target_outcomes",
        "comparator_outcomes",
        "target_no_outcomes",
        "comparator_no_outcomes",
    ]
    # if target, comparator, outcome are not specified, use the first one
    for target_id, comparator_id, outcome_id, analysis_id in tcoa_id:
        logger.info(
            f"target_id: {target_id}, comparator_id: {comparator_id}, outcome_id: {outcome_id}"
        )
        # if additional analysis(from other paper) is added, add it to results

        results_filter = results.query(
            "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id and analysis_id == @analysis_id"
        ).copy()

        if km_method == "raw":
            km_pop_dict = {}
            for source in sources:
                my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
                km_pop_path = [
                    i
                    for i in my_zip.namelist()
                    if ("StratPop" in i)
                    & (f"t{target_id}_c{comparator_id}" in i)
                    & (f"o{outcome_id}" in i)
                ][0]
                # ZipFile .extract (member, path=None, pwd=None)
                my_zip.extract(km_pop_path, temp_path)
                km_pop = pyreadr.read_r(temp_path / km_pop_path)[None][
                    ["treatment", "survivalTime", "outcomeCount"]
                ]
                km_pop_dict[source] = km_pop

        # get non significants rate of negative outcomes
        results_cated = results_cated.query(
            " target_id == @target_id & comparator_id == @comparator_id and analysis_id == @analysis_id "
        )

        # get attrition dataframe

        attrition_cated = pd.concat(attrition_dict.values())
        attrition_cated = attrition_cated.query(
            "target_id == @target_id & comparator_id == @comparator_id & outcome_id == @outcome_id and analysis_id == @analysis_id"
        )
        attritions = attrition_cated.pivot(
            index=["source", "cohort"], columns="description", values="subjects"
        )
        results_filter = results_filter.dropna(subset=["rr"])

        # if row in results have abnormal values...warn about source

        results_filter["target_no_outcomes"] = (
            results_filter["target_subjects"] - results_filter["target_outcomes"]
        )
        results_filter["comparator_no_outcomes"] = (
            results_filter["comparator_subjects"]
            - results_filter["comparator_outcomes"]
        )

        error_source = []
        for (_, row), col in itertools.product(results_filter.iterrows(), check_cols):
            if row[col] <= 0:
                logger.warning(f"{row['source']} has non-positive value in {col} ")
                error_source.append(row["source"])
        results_filter = results_filter[
            ~results_filter["source"].isin(error_source)
        ].sort_values("source")
        sources = results_filter.source.unique().tolist()

        if len(results_filter) == 0:
            continue

        # temporary sav start_pop for using R metafor packages
        strat_df = pd.concat(strat_dict.values())

        if add_analysis:
            for anal in add_analysis:
                add_t, add_c, add_o = int(anal[5]), int(anal[6]), int(anal[7])
                strat_df = strat_df.append(
                    pd.DataFrame(
                        {
                            "source": anal[0],
                            "target_id": add_t,
                            "comparator_id": add_c,
                            "outcome_id": add_o,
                            "analysis_id": 1,
                            "target_subjects": int(anal[1]),
                            "comparator_subjects": int(anal[2]),
                            "target_outcomes": int(anal[3]),
                            "comparator_outcomes": int(anal[4]),
                        },
                        index=[0],
                    )
                )
        strat_df = strat_df.query(
            "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id and analysis_id == @analysis_id"
        ).copy()

        strat_df.loc[:, "target_no_outcomes"] = (
            strat_df.loc[:, "target_subjects"] - strat_df.loc[:, "target_outcomes"]
        )
        strat_df.loc[:, "comparator_no_outcomes"] = (
            strat_df.loc[:, "comparator_subjects"]
            - strat_df.loc[:, "comparator_outcomes"]
        )

        strat_df.sort_values("source").to_csv("./results/temp_results.csv")
        # use R metafor packages to get meta-analysis
        # metafor is selected of crenditality of results and aesthetics of plots
        os.system("Rscript metafor_script.R")
        # (aggConstants.metafor_script)
        os.makedirs("./results", exist_ok=True)
        # Illustrate PS distribution
        ps_fig = draw_ps(
            ps_dict, sources, target_id, comparator_id, outcome_id, analysis_id
        )
        ps_fig.savefig("./results/ps_density.png", dpi=dpi)

        # Illustrate covariate balance
        cov_bal_fig = draw_cov_bal(
            covariate_dict, sources, target_id, comparator_id, outcome_id, analysis_id
        )
        cov_bal_fig.savefig("./results/cov_bal.png", dpi=dpi)

        # Illustrate KM distribution
        km_fig = draw_km_plot(
            km_dict, sources, target_id, comparator_id, outcome_id, analysis_id
        )
        km_fig.savefig("./results/km_plot.png", dpi=dpi)

        if km_method == "raw":
            km_raw_fig = draw_raw_km_plot(km_pop_dict, sources)
            km_raw_fig.savefig("./results/km_raw_plot.png", dpi=dpi)

        # Extract forest plot and save to png
        forest_fig = draw_forest_plot()
        forest_fig.savefig("./results/forest_plot.png", dpi=dpi)

        # make_html

        text = f"""
                target: {cohort_name_dict[target_id]}, \n
                Comparator : {cohort_name_dict[comparator_id]}, \n
                Outcome : {cohort_name_dict[outcome_id]}, \n
                Analysis : {cohort_name_dict['analysis'][analysis_id]}, \n
                """
        outpath = (
            f"report_t{target_id}_c{comparator_id}_o{outcome_id}_a{analysis_id}.html"
        )
        logger.info(f"{text} to {outpath}")

        outpath = report_path / str(inpath).split("/")[-1] / outpath
        os.makedirs(report_path / str(inpath).split("/")[-1], exist_ok=True)
        make_html(
            title=title,
            text=text,
            attritions=attritions,
            results=results_filter,
            outpath=outpath,
            km_method=km_method,
        )
