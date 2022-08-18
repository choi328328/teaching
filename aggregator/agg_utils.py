import matplotlib.pyplot as plt
import pandas as pd
import zipfile
import os
from rpy2.robjects import r
from pretty_html_table import build_table
from pdf2image import convert_from_path
import base64
from PIL import Image
from agg_constants import aggConstants
from lifelines import KaplanMeierFitter
from loguru import logger
import pyreadr
from pathlib import Path
import shutil
import re
import traceback
def get_stratpop(inpath, source):
    
    inpath =Path(inpath)
    shutil.rmtree(inpath / 'script', ignore_errors=True)
    my_zip = zipfile.ZipFile(inpath/f"{source}.zip")
    my_zip.extractall(inpath)
    refer_path = [i for i in my_zip.namelist() if i.endswith("outcomeModelReference.rds")][0]
    refer = pyreadr.read_r(str(inpath / refer_path))[None].query('strataFile != "" ')
    refer_values=refer[['analysisId','targetId','comparatorId','outcomeId','strataFile']].values
    src, t, c, o, a = [], [], [], [], []
    t_counts, c_counts, t_o_counts, c_o_counts = [], [], [], []
    for a_id, t_id, c_id,o_id, pop_name in refer_values:
        src.append(source)
        t.append(t_id)
        c.append(c_id)
        o.append(o_id)
        a.append(a_id)
        pop = pyreadr.read_r(str(inpath /'script/extras/result/cmOutput'/ pop_name))[None]
        t_counts.append(len(pop.query('treatment == 1')))
        c_counts.append(len(pop.query('treatment == 0')))
        t_o_counts.append(len(pop.query('treatment == 1 & outcomeCount == 1')))
        c_o_counts.append(len(pop.query('treatment == 0 & outcomeCount == 1')))
    shutil.rmtree(inpath / 'script')
    return pd.DataFrame({'source':src,
                        'target_id': t,
                         'comparator_id': c, 
                         'outcome_id': o, 
                         'analysis_id':a,
                         'target_subjects': t_counts, 
                         'comparator_subjects': c_counts, 
                         'target_outcomes': t_o_counts, 
                         'comparator_outcomes': c_o_counts})
    
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
        for csv_name in csv_names if len([i for i in my_zip.namelist() if i.endswith(csv_name)]) != 0
    ]

    negative_outcome, covariate_balance, km_dist, cohort_results, attrition, ps_dist = (
        pd.read_csv(my_zip.open(p)) for p in paths
    )
    cohort_results["source"] = source
    attrition["source"] = source
    attrition["cohort"] = attrition.apply(
        lambda x: "target" if x["exposure_id"] == x["target_id"] else "comparator",
        axis=1,
    )
    strat_pop=get_stratpop(inpath, source)

    return (
        negative_outcome,
        cohort_results.round(3),
        covariate_balance,
        km_dist,
        attrition,
        ps_dist,
        strat_pop
    )


def get_data_from_sources(inpath, sources):
    negative_dict, results_dict, covariate_dict, km_dict, attrition_dict, ps_dict, strat_dict = (
        {} for _ in range(7)
    )
    source_errors = []
    # get data from zipfiles
    for source in sources:
        try:
            (
                negative_outcome,
                cohort_results,
                covariate_balance,
                km_dist,
                attrition,
                ps_dist,
                strat_pop
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


def draw_ps(ps_dict, sources, target_id, comparator_id, outcome_id, analysis_id):
    sources = [source for source in sources if len(ps_dict[source]) > 0]
    fig, axes = plt.subplots(
        len(sources) // 3+1,
        3,
        figsize=(16, 1.5 * len(sources)),
        facecolor="white",
    )
    for num, source in enumerate(sources):
        ps_score = (
            ps_dict[source]
            .query("target_id == @target_id and comparator_id == @comparator_id  and analysis_id == @analysis_id")
            .copy()
        )
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        axes[coord].plot(
            ps_score["preference_score"],
            ps_score["target_density"],
            color=(0.8, 0, 0),
            alpha=0.2,
            label="target",
        )
        axes[coord].plot(
            ps_score["preference_score"],
            ps_score["comparator_density"],
            color=(0, 0, 0.8),
            alpha=0.2,
            label="comparator",
        )
        axes[coord].fill_between(
            ps_score["preference_score"],
            0,
            ps_score["target_density"],
            color=(0.8, 0, 0),
            alpha=0.5,
        )
        axes[coord].fill_between(
            ps_score["preference_score"],
            0,
            ps_score["comparator_density"],
            color=(0, 0, 0.8),
            alpha=0.5,
        )
        axes[coord].set_xlabel("Preference Score")
        axes[coord].set_ylabel("Density")
        axes[coord].legend(loc="upper center", frameon=False)
        axes[coord].set_title(source, size=20)
    fig.tight_layout()
    return fig


def draw_cov_bal(covariate_dict, sources, target_id, comparator_id, outcome_id, analysis_id):
    sources = [source for source in sources if len(covariate_dict[source]) > 0]
    fig, axes = plt.subplots(
        len(sources) // 3 +1,
        3,
        figsize=(16, 1.5 * len(sources)),
        facecolor="white",
    )
    
    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        cov_bal = (
            covariate_dict[source]
            .query(
                "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id  and analysis_id == @analysis_id"
            )
            .copy()
        )
        cov_bal.loc[:, "std_diff_after_abs"] = cov_bal.loc[:, "std_diff_after"].map(
            lambda x: abs(x)
        )
        cov_bal.loc[:, "std_diff_before_abs"] = cov_bal.loc[:, "std_diff_before"].map(
            lambda x: abs(x)
        )
        axes[coord].set_xlabel("Before propensity score adjustment")
        axes[coord].set_ylabel("After propensity score adjustment")
        axes[coord].scatter(
            cov_bal["std_diff_before_abs"],
            cov_bal["std_diff_after_abs"],
            color=(0, 0, 0.8),
            alpha=0.3,
            s=10,
        )
        axes[coord].set_xlim(0, 0.5)
        axes[coord].set_ylim(0, 0.5)
        axes[coord].plot([0, 1], linestyle="--", color=(0.3, 0.3, 0.3))
        axes[coord].set_title(source, size=20)
    fig.tight_layout()
    return fig


def draw_raw_km_plot(km_pop_dict, sources):
    sources = [source for source in sources if len(km_pop_dict[source]) > 0]
    fig, axes = plt.subplots(
        len(sources) // 3 +1,
        3,
        figsize=(16, 1.5 * len(sources)),
        facecolor="white",
    )
    
    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        km_pop = km_pop_dict[source]
        df_treat, df_nontreat = (
            km_pop.query("treatment==1"),
            km_pop.query("treatment==0"),
        )
        kmf = KaplanMeierFitter()

        kmf.fit(
            df_treat["survivalTime"],
            event_observed=df_treat["outcomeCount"],
            label="target",
        )
        axes[coord] = kmf.plot_survival_function(ax=axes[coord], title=source)

        kmf.fit(
            df_nontreat["survivalTime"],
            event_observed=df_nontreat["outcomeCount"],
            label="comparator",
        )
        axes[coord] = kmf.plot_survival_function(ax=axes[coord])
        # axes[coord].set_title(source, size=20)
    fig.tight_layout()
    return fig


def draw_km_plot(km_dict, sources, target_id, comparator_id, outcome_id, analysis_id):
    sources = [source for source in sources if len(km_dict[source]) > 0]
    fig, axes = plt.subplots(
        len(sources) // 3 +1,
        3,
        figsize=(24, 1.5 * len(sources)),
        facecolor="white",
    )
    
    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        km_dist = (
            km_dict[source]
            .query(
                "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id  and analysis_id == @analysis_id"
            )
            .copy()
        )
        km_dist = km_dist.query("(target_survival>0) & (comparator_survival>0)")
        axes[coord].step(
            km_dist["time"],
            km_dist["target_survival"],
            color=(0.8, 0, 0),
            label="target",
        )
        axes[coord].fill_between(
            km_dist["time"],
            km_dist["target_survival_lb"],
            km_dist["target_survival_ub"],
            color=(0.8, 0, 0),
            alpha=0.5,
        )
        axes[coord].step(
            km_dist["time"],
            km_dist["comparator_survival"],
            color=(0, 0, 0.8),
            label="comparator",
        )
        axes[coord].fill_between(
            km_dist["time"],
            km_dist["comparator_survival_ub"],
            km_dist["comparator_survival_lb"],
            color=(0, 0, 0.8),
            alpha=0.5,
        )
        axes[coord].set_xlabel("Time in days")
        axes[coord].set_ylabel("Survival probability")
        axes[coord].legend(frameon=False)
        axes[coord].set_title(source, size=20)
    fig.tight_layout()
    return fig


def draw_forest_plot():
    fig, axes = plt.subplots(1, 2, figsize=(30, 15), facecolor="white")
    convert_from_path("./results/forest_fixed.pdf")[0].save(
        "./results/forest_fixed.png", "PNG"
    )
    convert_from_path("./results/forest_random.pdf")[0].save(
        "./results/forest_random.png", "PNG"
    )
    img1 = Image.open("./results/forest_fixed.png")
    axes[0].imshow(img1)
    axes[0].axis("off")

    img2 = Image.open("./results/forest_random.png")
    axes[1].imshow(img2)
    axes[1].axis("off")
    fig.tight_layout()
    return fig


def make_html(
    title, text, attritions, results, outpath="html_report.html", km_method="adjusted"
):

    target_outcome_text = ""
    results_text = "Estimation summary"
    negative_text = "Negative outcomes"
    attrition_text = "Attritions"

    attrition2 = attritions.reset_index()
    attrition2.columns = list(attrition2.columns)
    if "Original cohorts" in attrition2.columns:
        attrition2.drop(columns=["Original cohorts"], inplace=True)

    forest_plot_uri = base64.b64encode(
        open("./results/forest_plot.png", "rb").read()
    ).decode("utf-8")
    ps_density_uri = base64.b64encode(
        open("./results/ps_density.png", "rb").read()
    ).decode("utf-8")
    cov_bal_uri = base64.b64encode(open("./results/cov_bal.png", "rb").read()).decode(
        "utf-8"
    )
    km_plot_uri = base64.b64encode(open("./results/km_plot.png", "rb").read()).decode(
        "utf-8"
    )
    if km_method == "raw":
        km_plot_uri = base64.b64encode(
            open("./results/km_raw_plot.png", "rb").read()
        ).decode("utf-8")

    results["target(outcome)"] = results.apply(
        lambda x: f'{x["target_subjects"]} ({x["target_outcomes"]})', axis=1
    )
    results["comparator(outcome)"] = results.apply(
        lambda x: f'{x["comparator_subjects"]} ({x["comparator_outcomes"]})', axis=1,
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
                <img src="data:image/png;base64,{forest_plot_uri}" width="900"> 
                
                <h3>Kaplan-Meier curve</h3>
                <img src="data:image/png;base64,{km_plot_uri}" width="1100">
                
                <h3>{attrition_text}</h3>
                {build_table(attrition2, 'green_light')}
                
                <h3>PS distribution</h3>
                <img src="data:image/png;base64,{ps_density_uri}" width="1100">
                
                <h3>Covariate balance</h3>
                <img src="data:image/png;base64,{cov_bal_uri}" width="1100">

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
    anal_summary = pd.read_csv(my_zip.open(analysis_summ_path))[['analysisId','analysisDescription']].drop_duplicates()
    final_dict = {**dict(zip(cohort_df.cohortDefinitionId, cohort_df.cohortName)),
                  'analysis':dict(zip(anal_summary.analysisId, anal_summary.analysisDescription))}
    
    return final_dict


def ple_aggregation(
    inpath,
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
        results[["target_id", "comparator_id", "outcome_id",'analysis_id']].drop_duplicates().values
    )
    # if target, comparator, outcome are not specified, use the first one
    for target_id, comparator_id, outcome_id, analysis_id in tcoa_id:
        logger.info(
            f"target_id: {target_id}, comparator_id: {comparator_id}, outcome_id: {outcome_id}"
        )
        # if additional analysis(from other paper) is added, add it to results
        if add_analysis:
            for anal in add_analysis:
                if int(anal[5]) * int(anal[6]) * int(anal[7]) == 0:
                    add_t, add_c, add_o = target_id, comparator_id, outcome_id
                else:
                    add_t, add_c, add_o = int(anal[5]), int(anal[6]), int(anal[7])
                results = results.append(
                    pd.DataFrame(
                        {
                            "source": anal[0],
                            "target_id": add_t,
                            "comparator_id": add_c,
                            "outcome_id": add_o,
                            "analysis_id" :1,
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

        results_filter = results.query(
            "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id and analysis_id == @analysis_id"
        ).copy()

        if km_method == "raw":
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
        results_cated = results_cated.query(
            " target_id == @target_id & comparator_id == @comparator_id and analysis_id == @analysis_id "
        )
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
        attrition_cated = attrition_cated.query(
            "target_id == @target_id & comparator_id == @comparator_id & outcome_id == @outcome_id and analysis_id == @analysis_id"
        )
        attritions = attrition_cated.pivot(
            index=["source", "cohort"], columns="description", values="subjects"
        )

        results_filter = results_filter.dropna(subset=["rr"])

        # if row in results have abnormal values...warn about source
        
        results_filter.loc[:, "target_no_outcomes"] = (
            results_filter.loc[:, "target_subjects"]
            - results_filter.loc[:, "target_outcomes"]
        )
        results_filter.loc[:, "comparator_no_outcomes"] = (
            results_filter.loc[:, "comparator_subjects"]
            - results_filter.loc[:, "comparator_outcomes"]
        )
        check_cols = [
            "target_subjects",
            "comparator_subjects",
            "target_outcomes",
            "comparator_outcomes",
            "target_no_outcomes",
            "comparator_no_outcomes",
        ]
        error_source = []
        for num, row in results_filter.iterrows():
            for col in check_cols:
                if row[col] <= 0:
                    logger.warning(f"{row['source']} has non-positive value in {col} ")
                    error_source.append(row["source"])
        results_filter = results_filter[~results_filter["source"].isin(error_source)]
        sources = results_filter.source.unique().tolist()

        if len(results_filter) == 0:
            continue

        # temporary sav start_pop for using R metafor packages
        strat_df=pd.concat(strat_dict.values())
        strat_df=strat_df.query(
            "target_id == @target_id and comparator_id == @comparator_id and outcome_id == @outcome_id and analysis_id == @analysis_id"
        ).copy()
        
        strat_df.loc[:, "target_no_outcomes"] = (
            strat_df.loc[:, "target_subjects"]
            - strat_df.loc[:, "target_outcomes"]
        )
        strat_df.loc[:, "comparator_no_outcomes"] = (
            strat_df.loc[:, "comparator_subjects"]
            - strat_df.loc[:, "comparator_outcomes"]
        )
        
        strat_df.to_csv("./results/temp_results.csv")
        # use R metafor packages to get meta-analysis
        # metafor is selected of crenditality of results and aesthetics of plots
        r(aggConstants.metafor_script)

        # Illustrate PS distribution
        ps_fig = draw_ps(ps_dict, sources, target_id, comparator_id, outcome_id, analysis_id)
        ps_fig.savefig("./results/ps_density.png", dpi=dpi)

        # Illustrate covariate balance
        cov_bal_fig = draw_cov_bal(
            covariate_dict, sources, target_id, comparator_id, outcome_id, analysis_id
        )
        cov_bal_fig.savefig("./results/cov_bal.png", dpi=dpi)

        # Illustrate KM distribution
        km_fig = draw_km_plot(km_dict, sources, target_id, comparator_id, outcome_id, analysis_id)
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
        outpath = f"report_t{target_id}_c{comparator_id}_o{outcome_id}_a{analysis_id}.html"
        logger.info(f"{text}to {outpath}")
        os.makedirs(inpath.split("/")[-1], exist_ok=True)
        outpath = inpath.split("/")[-1] + "/" + outpath
        make_html(
            title=title,
            text=text,
            attritions=attritions,
            results=results_filter,
            outpath=outpath,
            km_method=km_method,
        )
