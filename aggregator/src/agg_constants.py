from dataclasses import dataclass


@dataclass
class aggConstants:
    required_cols = [
        "source",
        "target_id",
        "comparator_id",
        "outcome_id",
        'analysis_id',
        "rr",
        "ci_95_lb",
        "ci_95_ub",
        "p",
        "target_subjects",
        "comparator_subjects",
        "target_outcomes",
        "comparator_outcomes",
    ]
    report_cols = [
        "source",
        "rr",
        "ci_95_ub",
        "ci_95_lb",
        "p",
        "target(outcome)",
        "comparator(outcome)",
        "target_id",
        "comparator_id",
        "outcome_id",
    ]

    metafor_script = """
    library(metafor)
    tt= read.csv('./results/temp_results.csv')
    data1= escalc(measure='RR',ai=target_outcomes, bi=target_no_outcomes, ci=comparator_outcomes, di=comparator_no_outcomes, data=tt, append=TRUE)
    res1 <- rma(yi, vi, data = data1, digits = 3, method="REML")
    res2 <- rma(yi, vi, data=data1, digits=3, method="FE")

    pdf(file='./results/forest_random.pdf')
    forest(res1, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
        ilab=cbind(target_outcomes, target_no_outcomes, comparator_outcomes, comparator_no_outcomes), ilab.xpos=c(-9.5,-8,-6,-4.5), 
        cex=.75, header="Hospital", mlab="",slab=(source))
    text(-16, -1, pos=4, cex=0.75, bquote(paste("Random Model (Q = ",
                                                .(formatC(res1$QE, digits=2, format="f")), ", df = ", .(res1$k - res1$p),
                                                ", p = ", .(formatC(res1$QEp, digits=2, format="f")), "; ", I^2, " = ",
                                                .(formatC(res1$I2, digits=1, format="f")), "%)")))
    dev.off()

    pdf(file='./results/forest_fixed.pdf')
    forest(res2, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
        ilab=cbind(target_outcomes, target_no_outcomes, comparator_outcomes, comparator_no_outcomes), ilab.xpos=c(-9.5,-8,-6,-4.5), 
        cex=.75, header="Hospital", mlab="",slab=(source))
    text(-16, -1, pos=4, cex=0.75, bquote(paste("Fixed Model (Q = ",
                                                .(formatC(res2$QE, digits=2, format="f")), ", df = ", .(res2$k - res2$p),
                                                ", p = ", .(formatC(res2$QEp, digits=2, format="f")), "; ", I^2, " = ",
                                                .(formatC(res2$I2, digits=1, format="f")), "%)")))
    dev.off()
    """
