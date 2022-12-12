import matplotlib.pyplot as plt
from pdf2image import convert_from_path
from PIL import Image
from lifelines import KaplanMeierFitter
from .agg_constants import aggConstants


def draw_ps(ps_dict, sources, t_id, c_id, o_id, a_id):
    sources = [source for source in sources if len(ps_dict[source]) > 0]
    if not sources:
        return plt.subplots(1, 1, figsize=(16, 1.5))[0]
    fig, axes = plt.subplots(
        len(sources) // 3 + 1,
        3,
        figsize=(16, 1.5 * len(sources)),
        facecolor="white",
    )
    for num, source in enumerate(sources):
        ps_score = ps_dict[source].query(aggConstants.tca_query).copy()
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
    if len(sources) != 1:
        fig.tight_layout()
    return fig


def draw_cov_bal(covariate_dict, sources, t_id, c_id, o_id, a_id):
    sources = [source for source in sources if len(covariate_dict[source]) > 0]
    if not sources:
        return plt.subplots(1, 1, figsize=(16, 1.5))[0]
    fig, axes = plt.subplots(
        len(sources) // 3 + 1,
        3,
        figsize=(16, 1.5 * len(sources)),
        facecolor="white",
    )

    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        cov_bal = covariate_dict[source].query(aggConstants.tcoa_query).copy()
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
    if len(sources) != 1:
        fig.tight_layout()
    return fig


def draw_raw_km_plot(km_pop_dict, sources):
    sources = [source for source in sources if source in km_pop_dict]
    sources = [source for source in sources if len(km_pop_dict[source]) > 0]
    if not sources:
        return plt.subplots(1, 1, figsize=(16, 1.5))[0]
    fig, axes = plt.subplots(
        len(sources) // 3 + 1,
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
        axes[coord].set_xlabel("Time in days")
        axes[coord].set_ylabel("Survival probability")
        # axes[coord].set_title(source, size=20)
    if len(sources) != 1:
        fig.tight_layout()
    return fig


def draw_km_plot(km_dict, sources, t_id, c_id, o_id, a_id):
    sources = [source for source in sources if len(km_dict[source]) > 0]
    if not sources:
        return plt.subplots(1, 1, figsize=(16, 1.5))[0]
    fig, axes = plt.subplots(
        len(sources) // 3 + 1,
        3,
        figsize=(24, 1.5 * len(sources)),
        facecolor="white",
    )

    for num, source in enumerate(sources):
        coord = (num // 3, num % 3) if len(sources) // 3 >= 1 else num % 3
        km_dist = km_dict[source].query(aggConstants.tcoa_query).copy()
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
    if len(sources) != 1:
        fig.tight_layout()
    return fig


def draw_forest_plot():
    fig, axes = plt.subplots(1, 2, figsize=(30, 15), facecolor="white")

    for num, forest in enumerate(["forest_fixed", "forest_random"]):
        convert_from_path(f"./results/{forest}.pdf")[0].save(
            f"./results/{forest}.png", "PNG"
        )
        img = Image.open(f"./results/{forest}.png")
        axes[num].imshow(img)
        axes[num].axis("off")
    # convert_from_path("./results/forest_fixed.pdf")[0].save(
    #     "./results/forest_fixed.png", "PNG"
    # )
    # img1 = Image.open("./results/forest_fixed.png")
    # axes[0].imshow(img1)
    # axes[0].axis("off")

    # convert_from_path("./results/forest_random.pdf")[0].save(
    #     "./results/forest_random.png", "PNG"
    # )
    # img2 = Image.open("./results/forest_random.png")
    # axes[1].imshow(img2)
    # axes[1].axis("off")

    fig.tight_layout()
    return fig
