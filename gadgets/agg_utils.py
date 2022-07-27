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
from lifelines import KaplanMeierFitter


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

    return (
        negative_outcome,
        cohort_results.round(3),
        covariate_balance,
        km_dist,
        attrition,
        ps_dist,
    )


def get_data_from_sources(inpath, sources):
    negative_dict, results_dict, covariate_dict, km_dict, attrition_dict, ps_dict = (
        {} for _ in range(6)
    )

    # get data from zipfiles
    for source in sources:
        (
            negative_outcome,
            cohort_results,
            covariate_balance,
            km_dist,
            attrition,
            ps_dist,
        ) = get_data(inpath, source)

        negative_dict[source] = negative_outcome
        results_dict[source] = cohort_results
        covariate_dict[source] = covariate_balance
        km_dict[source] = km_dist
        attrition_dict[source] = attrition
        ps_dict[source] = ps_dist
    return (
        negative_dict,
        results_dict,
        covariate_dict,
        km_dict,
        attrition_dict,
        ps_dict,
    )


def draw_ps(ps_dict, sources):
    fig, axes = plt.subplots(
        (len(sources) // 3) + 1, 3, figsize=(16, 1.5 * len(sources)), facecolor="white"
    )
    for num, source in enumerate(sources):
        ps_score = ps_dict[source]
        coord = (num // 3, num % 3) if len(sources) // 3 > 1 else num % 3
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


def draw_cov_bal(covariate_dict, sources):
    fig, axes = plt.subplots(
        (len(sources) // 3) + 1, 3, figsize=(16, 1.5 * len(sources)), facecolor="white",
    )
    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 > 1 else num % 3
        cov_bal = covariate_dict[source]
        cov_bal["std_diff_after_abs"] = cov_bal["std_diff_after"].map(lambda x: abs(x))
        cov_bal["std_diff_before_abs"] = cov_bal["std_diff_before"].map(
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

    fig, axes = plt.subplots(
        (len(sources) // 3) + 1, 3, figsize=(16, 1.5 * len(sources)), facecolor="white"
    )

    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 > 1 else num % 3
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


def draw_km_plot(km_dict, sources):
    fig, axes = plt.subplots(
        (len(sources) // 3) + 1, 3, figsize=(24, 1.5 * len(sources)), facecolor="white"
    )
    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 > 1 else num % 3
        km_dist = km_dict[source]
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
