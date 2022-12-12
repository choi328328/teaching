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
    tcoa_list = results[["t_id", "c_id", "o_id", "a_id"]].drop_duplicates()
    # if target, comparator, outcome are not specified, use the first one
    for num, row in tcoa_list.iterrows():
        t_id, c_id, o_id, a_id = row
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
        if len(sources) != 0:
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
