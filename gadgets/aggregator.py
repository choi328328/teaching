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

args = parser.parse_args()

os.chdir(
    "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/gadgets"
)
os.makedirs("./results", exist_ok=True)


def get_datas(inpath, source):
    my_zip = zipfile.ZipFile(os.path.join(inpath, f"{source}.zip"))
    negative_path = [
        i for i in my_zip.namelist() if i.endswith("negative_control_outcome.csv")
    ][0]
    covariate_path = [
        i for i in my_zip.namelist() if i.endswith("covariate_balance.csv")
    ][0]
    km_path = [i for i in my_zip.namelist() if i.endswith("kaplan_meier_dist.csv")][0]
    method_result_path = [
        i for i in my_zip.namelist() if i.endswith("cohort_method_result.csv")
    ][0]
    attrition_path = [i for i in my_zip.namelist() if i.endswith("attrition.csv")][0]
    ps_path = [i for i in my_zip.namelist() if i.endswith("preference_score_dist.csv")][
        0
    ]

    negative_outcome = pd.read_csv(my_zip.open(negative_path))
    cohort_results = pd.read_csv(my_zip.open(method_result_path))
    cohort_results["source"] = source
    covariate_balance = pd.read_csv(my_zip.open(covariate_path))
    km_dist = pd.read_csv(my_zip.open(km_path))
    attrition = pd.read_csv(my_zip.open(attrition_path))
    attrition["source"] = source
    attrition["cohort"] = attrition.apply(
        lambda x: "target" if x["exposure_id"] == x["target_id"] else "comparator",
        axis=1,
    )
    ps_dist = pd.read_csv(my_zip.open(ps_path))
    
    return negative_outcome, cohort_results, covariate_balance, km_dist, attrition, ps_dist
    



def ple_aggregation(inpath, add_analysis, dpi):
    sources = [i.split(".zip")[0] for i in os.listdir(inpath) if i.endswith(".zip")]
    negative_dict, results_dict, covariate_dict, km_dict, attrition_dict, ps_dict = (
        {},
        {},
        {},
        {},
        {},
        {},
    )

    for source in sources:
        my_zip = zipfile.ZipFile(os.path.join(inpath, f"{source}.zip"))
        negative_path = [
            i for i in my_zip.namelist() if i.endswith("negative_control_outcome.csv")
        ][0]
        covariate_path = [
            i for i in my_zip.namelist() if i.endswith("covariate_balance.csv")
        ][0]
        km_path = [i for i in my_zip.namelist() if i.endswith("kaplan_meier_dist.csv")][
            0
        ]
        method_result_path = [
            i for i in my_zip.namelist() if i.endswith("cohort_method_result.csv")
        ][0]
        attrition_path = [i for i in my_zip.namelist() if i.endswith("attrition.csv")][
            0
        ]
        ps_path = [
            i for i in my_zip.namelist() if i.endswith("preference_score_dist.csv")
        ][0]

        negative_outcome = pd.read_csv(my_zip.open(negative_path))
        cohort_results = pd.read_csv(my_zip.open(method_result_path))
        cohort_results["source"] = source
        covariate_balance = pd.read_csv(my_zip.open(covariate_path))
        km_dist = pd.read_csv(my_zip.open(km_path))
        attrition = pd.read_csv(my_zip.open(attrition_path))
        attrition["source"] = source
        attrition["cohort"] = attrition.apply(
            lambda x: "target" if x["exposure_id"] == x["target_id"] else "comparator",
            axis=1,
        )
        ps_dist = pd.read_csv(my_zip.open(ps_path))
        negative_outcome, cohort_results, covariate_balance, km_dist, attrition, ps_dist = get_datas(inpath, source)

        
        negative_dict[source] = negative_outcome
        results_dict[source] = cohort_results.round(3)
        covariate_dict[source] = covariate_balance
        km_dict[source] = km_dist
        attrition_dict[source] = attrition
        ps_dict[source] = ps_dist

    negative_ids = list(negative_dict.values())[0].outcome_id
    results_cated = pd.concat(results_dict.values())
    required_cols = [
        "source",
        "target_id",
        "comparator_id",
        "outcome_id",
        "rr",
        "ci_95_lb",
        "ci_95_ub",
        "p",
        "target_subjects",
        "comparator_subjects",
        "target_outcomes",
        "comparator_outcomes",
    ]
    results = results_cated[~results_cated["outcome_id"].isin(negative_ids)][
        required_cols
    ]

    negative_cated = results_cated[results_cated["outcome_id"].isin(negative_ids)]
    negatives = pd.DataFrame(
        negative_cated[required_cols]
        .dropna(subset=["rr"])
        .query("p>0.05")
        .groupby("source")
        .count()["rr"]
    )
    negatives.columns = ["Negative outcomes"]
    negatives["Non-signifcant percent"] = (
        negatives["Negative outcomes"] / len(negative_ids) * 100
    )

    attrition_cated = pd.concat(attrition_dict.values())
    attritions = attrition_cated.pivot(
        index=["source", "cohort",], columns="description", values="subjects"
    )
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
                        "target_subjects": int(anal[2]),
                        "comparator_subjects": int(anal[4]),
                        "target_outcomes": int(anal[1]),
                        "comparator_outcomes": int(anal[3]),
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
    results.to_csv("./results/temp_results.csv")
    negative_cated.to_csv("./results/temp_negatives.csv")

    r(
        """
    library(metafor)
    tt= read.csv('./results/temp_results.csv')
    data1= escalc(measure='RR',ai=target_outcomes, bi=target_no_outcomes, ci=comparator_outcomes, di=comparator_no_outcomes, data=tt, append=TRUE)
    res1 <- rma(yi, vi, data = data1, digits = 3)
    res2 <- rma(yi, vi, data=data1, digits=3, method="FE")

    pdf(file='./results/forest_random.pdf')
    forest(res1, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
        ilab=cbind(target_outcomes, target_subjects, comparator_outcomes, comparator_subjects), ilab.xpos=c(-9.5,-8,-6,-4.5), 
        cex=.75, header="Hospital", mlab="",slab=(source))
    text(-16, -1, pos=4, cex=0.75, bquote(paste("Random Model (Q = ",
                                                .(formatC(res1$QE, digits=2, format="f")), ", df = ", .(res1$k - res1$p),
                                                ", p = ", .(formatC(res1$QEp, digits=2, format="f")), "; ", I^2, " = ",
                                                .(formatC(res1$I2, digits=1, format="f")), "%)")))
    dev.off()

    pdf(file='./results/forest_fixed.pdf')
    forest(res2, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
        ilab=cbind(target_outcomes, target_subjects, comparator_outcomes, comparator_subjects), ilab.xpos=c(-9.5,-8,-6,-4.5), 
        cex=.75, header="Hospital", mlab="",slab=(source))
    text(-16, -1, pos=4, cex=0.75, bquote(paste("Fixed Model (Q = ",
                                                .(formatC(res2$QE, digits=2, format="f")), ", df = ", .(res2$k - res2$p),
                                                ", p = ", .(formatC(res2$QEp, digits=2, format="f")), "; ", I^2, " = ",
                                                .(formatC(res2$I2, digits=1, format="f")), "%)")))
    dev.off()
    """
    )
    fig1, axes = plt.subplots(
        max(len(sources) // 2, 1), 2, figsize=(12, 3 * len(sources)), facecolor="white"
    )
    for num, source in enumerate(sources):
        ps_score = ps_dict[source]
        coord = (num // 2, num % 2) if num // 2 > 1 else num % 2
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
    fig1.tight_layout()
    fig1.savefig("./results/ps_density.png", dpi=dpi)

    #####
    fig2, axes = plt.subplots(
        max(len(sources) // 2, 1), 2, figsize=(12, 3 * len(sources)), facecolor="white"
    )
    for num, source in enumerate(sources):
        coord = (num // 2, num % 2) if num // 2 > 1 else num % 2
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
    fig2.tight_layout()
    fig2.savefig("./results/cov_bal.png", dpi=dpi)

    ####
    fig3, axes = plt.subplots(
        max(len(sources) // 2, 1), 2, figsize=(12, 3 * len(sources)), facecolor="white"
    )
    for num, source in enumerate(sources):
        coord = (num // 2, num % 2) if num // 2 > 1 else num % 2
        cov_bal = km_dict[source]
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
    fig3.tight_layout()
    fig3.savefig("./results/km_plot.png", dpi=dpi)

    ###
    fig4, axes = plt.subplots(1, 2, figsize=(30, 15), facecolor="white")
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
    fig4.tight_layout()
    fig4.savefig("./results/forest_plot.png", dpi=dpi)

    page_title_text = "My report"
    title_text = "PLE"
    text = ",".join(sources) + " are included in the analysis."
    results_text = "Estimation summary"
    negative_text = "Negative outcomes"
    attrition_text = "Attritions"
    stats_text = "Historical prices summary statistics"

    aa = attritions.reset_index()
    aa.columns = list(aa.columns)

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

    # 2. Combine them together using a long f-string
    html = f"""
        <html>
            <head>
                <title>{page_title_text}</title>
            </head>
            <body>
                <h1>{title_text}</h1>
                <p>{text}</p>
                
                <h2>{results_text}</h2>
                {build_table(results.query('outcome_id != -999 '), 'blue_light')}
                <h2>Forest plot</h2>
                <img src="data:image/png;base64,{forest_plot_uri}" width="1100"> 
                
                <h2>{attrition_text}</h2>
                {build_table(aa, 'green_light')}
                
                <h2>PS distribution</h2>
                <img src="data:image/png;base64,{ps_density_uri}" width="1100">
                
                <h2>Covariate balance</h2>
                <img src="data:image/png;base64,{cov_bal_uri}" width="1100">
                
                <h2>Kaplan-Meier curve</h2>
                <img src="data:image/png;base64,{km_plot_uri}" width="1100">

            </body>
        </html>
        """

    # 3. Write the html string as an HTML file
    with open("html_report.html", "w") as f:
        f.write(html)


if __name__ == "__main__":
    # 외부 혹은 다른 논문에서 분석된 자료를 함께 meta-analysis하기 위해서...add_analysis 사용
    add_analysis = [("smc", 132, 10000, 500, 10000)]

    ple_aggregation(inpath=args.inpath, add_analysis=add_analysis, dpi=args.dpi)
    print("DONE!!!!!")

