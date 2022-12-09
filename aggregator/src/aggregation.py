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
    add_analysis_func,
    check_smaller_than_5,
    get_km_pop_dict,
)
from loguru import logger
import pyreadr
from pathlib import Path


# def survival_aggregation(inpath, negatives):  # get survival_aggregation from stratpop
#     sources = [
#         i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")
#     ]  # name of hospitals(data sources)
#     km_pop_dict = {source: get_stratpop_info(inpath, source) for source in sources}
#     inpath = Path(inpath)
#     cohort_name_dict = get_cohort_name(inpath, sources[0])

#     df = pd.DataFrame()
#     for source in sources:
#         my_zip = zipfile.ZipFile(inpath / f"{source}.zip")
#         my_zip.extractall(inpath)
#         refer_paths = [
#             i for i in my_zip.namelist() if i.endswith("outcomeModelReference.rds")
#         ]
#         summary_paths = [
#             i for i in my_zip.namelist() if i.endswith("analysisSummary.csv")
#         ]
#         for num, refer_path in enumerate(refer_paths):

#             refer = pyreadr.read_r(str(inpath / refer_path))[None].query(
#                 'strataFile != "" '
#             )
#             refer_values = refer[
#                 ["analysisId", "targetId", "comparatorId", "outcomeId", "strataFile"]
#             ].values

#             counts_path = [
#                 i for i in my_zip.namelist() if i.endswith("CohortCounts.csv")
#             ][num]
#             cohort_info = pd.read_csv(str(inpath / counts_path))
#             cohort_name_dict = dict(
#                 zip(cohort_info["cohortDefinitionId"], cohort_info["cohortName"])
#             )

#             anal_summary = pd.read_csv(str(inpath / summary_paths[num]))
#             anal_summary = anal_summary.dropna(subset=["rr", "ci95lb"])
#             anal_summary = anal_summary[
#                 (anal_summary["ci95lb"] > 1) | (anal_summary["ci95ub"] < 1)
#             ]
#             if negatives:
#                 anal_summary = anal_summary[
#                     ~anal_summary["outcomeId"].isin(refer["outcomeId"])
#                 ]
#                 if len(anal_summary) == 0:
#                     continue
#                 anal_summary["hr_ci"] = anal_summary.apply(
#                     lambda x: f'{x["rr"]:.3f} ({x["ci95lb"]:.3f}-{x["ci95ub"]:.3f}) ',
#                     axis=1,
#                 )
#                 anal_summary["treat_outcome"] = anal_summary.apply(
#                     lambda x: f'{x["target"]} ({x["eventsTarget"]}) ', axis=1
#                 )
#                 anal_summary["nontreat_outcome"] = anal_summary.apply(
#                     lambda x: f'{x["comparator"]} ({x["eventsComparator"]}) ', axis=1
#                 )
#                 anal_summary["source"] = [source] * len(anal_summary)
#                 negatives_summ = anal_summary[
#                     [
#                         "source",
#                         "targetName",
#                         "comparatorName",
#                         "outcomeName",
#                         "hr_ci",
#                         "treat_outcome",
#                         "nontreat_outcome",
#                     ]
#                 ]
#                 df = pd.concat([df, negatives_summ], axis=0)

#             for a, t, c, o, pop_name in refer_values:
#                 pop_path = [i for i in my_zip.namelist() if i.endswith(pop_name)][0]
#                 km_pop = pyreadr.read_r(inpath / pop_path)[None][
#                     ["treatment", "survivalTime", "outcomeCount"]
#                 ]
#                 km_pop_dict[source] = km_pop

#                 # T,C,O cohort name 얻기
#                 t_name = cohort_name_dict.get(t)
#                 c_name = cohort_name_dict.get(c)
#                 o_name = cohort_name_dict.get(o)
#                 n_treat, n_nontreat = (
#                     len(km_pop.query("treatment==1")),
#                     len(km_pop.query("treatment==0")),
#                 )
#                 treat_o, nontreat_o = (
#                     int(km_pop.query("treatment==1").outcomeCount.sum()),
#                     int(km_pop.query("treatment==0").outcomeCount.sum()),
#                 )
#                 # cph fit 결과 및 N수를 dataframe으로 정리하기
#                 # csv로 결과 출력
#                 # source, t_name, c_name, o_name, N, p_value, HR, CI_lower, CI_upper
#                 if (treat_o == 0) | (treat_o == n_treat):
#                     hr, p_value, lb, ub = 0, 0, 0, 0
#                 else:
#                     cph = CoxPHFitter()
#                     cph.fit(km_pop, "survivalTime", "outcomeCount")
#                     hr = cph.summary["exp(coef)"].item()
#                     lb = cph.summary["exp(coef) lower 95%"].item()
#                     ub = cph.summary["exp(coef) upper 95%"].item()
#                     p_value = cph.summary["p"].item()
#                 hr_ci = f"{hr:.3f} ({lb:.3f}-{ub:.3f})"  #  ,p={p_value:.4f}
#                 treat_outcome = f"{n_treat} ({treat_o})"
#                 nontreat_outcome = f"{n_nontreat} ({nontreat_o})"
#                 tco_df = pd.DataFrame(
#                     [
#                         source,
#                         t_name,
#                         c_name,
#                         o_name,
#                         hr_ci,
#                         treat_outcome,
#                         nontreat_outcome,
#                     ]
#                 ).T
#                 tco_df.columns = [
#                     "source",
#                     "targetName",
#                     "comparatorName",
#                     "outcomeName",
#                     "hr_ci",
#                     "treat_outcome",
#                     "nontreat_outcome",
#                 ]

#                 df = pd.concat([df, tco_df])

#     return df


def ple_aggregation(
    inpath,
    report_path="./reports",
    title="PLE Aggregation",
    add_analysis=False,
    dpi=100,
    km_method="adjusted",
    t_id=0,
    c_id=0,
    o_id=0,
):
    sources = [
        i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")
    ]  # name of hospitals(data sources)
    inpath, temp_path, report_path = Path(inpath), Path("./results"), Path(report_path)
    (
        negative_ids,
        results,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
        strat_dict,
        sources,  # after remove error sources
    ) = get_data_from_sources(inpath, sources)
    cohort_name_dict = get_cohort_name(inpath, sources[0])

    # get study population
    results = results[
        [
            "t_id",
            "c_id",
            "o_id",
            "a_id",
            "t_pats",
            "c_pats",
            "t_o",
            "c_o",
            "rr",
            "ci_95_ub",
            "ci_95_lb",
            "p",
            "source",
        ]
    ].drop_duplicates(
        subset=[
            "t_id",
            "c_id",
            "o_id",
            "a_id",
        ]
    )
    # if target, comparator, outcome are not specified, use the first one
    for num, row in results.iterrows():
        t_id, c_id, o_id, a_id, _, _, _, _, _, _, _, _, _ = row
        logger.info(f"t_id: {t_id}, c_id: {c_id}, o_id: {o_id}")

        # if row in results have abnormal values(n<25), exclude them
        results_filter = results.query(aggConstants.tcoa_query).dropna(subset=["rr"])
        results_filter = check_smaller_than_5(results_filter)
        sources = results_filter.source.unique().tolist()
        if len(results_filter) == 0:
            continue

        # get raw population for each tcoa.
        if km_method == "raw":
            get_km_pop_dict(inpath, temp_path, sources, t_id, c_id, o_id, a_id)
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

        # get attrition dataframe
        attrition_cated = pd.concat(attrition_dict.values())
        attrition_cated = attrition_cated.query(aggConstants.tcoa_query)
        attritions = attrition_cated.pivot(
            index=["source", "cohort"], columns="description", values="subjects"
        )

        # temporary sav start_pop for using R metafor packages
        strat_df = pd.concat(strat_dict.values())
        # if additional analysis(from other paper) is added, add it to results
        if add_analysis:
            strat_df = add_analysis_func(strat_df, add_analysis)
        strat_df = strat_df.query(aggConstants.tcoa_query).copy()
        strat_df.loc[:, "t_wo_o"] = strat_df.loc[:, "t_pats"] - strat_df.loc[:, "t_o"]
        strat_df.loc[:, "c_wo_o"] = strat_df.loc[:, "c_pats"] - strat_df.loc[:, "c_o"]
        strat_df.sort_values("source").to_csv(
            "./results/temp_results.csv"
        )  # for forest plot

        # make plots for html
        os.makedirs("./results", exist_ok=True)
        ps_fig = draw_ps(ps_dict, sources, t_id, c_id, o_id, a_id)
        ps_fig.savefig("./results/ps_density.png", dpi=dpi)
        cov_bal_fig = draw_cov_bal(covariate_dict, sources, t_id, c_id, o_id, a_id)
        cov_bal_fig.savefig("./results/cov_bal.png", dpi=dpi)
        km_fig = draw_km_plot(km_dict, sources, t_id, c_id, o_id, a_id)
        km_fig.savefig("./results/km_plot.png", dpi=dpi)
        if km_method == "raw":
            km_raw_fig = draw_raw_km_plot(km_pop_dict, sources)
            km_raw_fig.savefig("./results/km_raw_plot.png", dpi=dpi)
        os.system("Rscript metafor_script.R")
        forest_fig = draw_forest_plot()  # R metafor packages to get meta-analysis
        forest_fig.savefig("./results/forest_plot.png", dpi=dpi)

        # concated plots to html
        text = f"""
                target: {cohort_name_dict[t_id]}, \n
                Comparator : {cohort_name_dict[c_id]}, \n
                Outcome : {cohort_name_dict[o_id]}, \n
                Analysis : {cohort_name_dict['analysis'][a_id]}, \n
                """
        outpath = f"report_t{t_id}_c{c_id}_o{o_id}_a{a_id}.html"
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
