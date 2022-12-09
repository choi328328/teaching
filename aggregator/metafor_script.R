library(metafor)
tt= read.csv('./results/temp_results.csv')
data1= escalc(measure='RR',ai=t_o, bi=t_wo_o, ci=c_o, di=c_wo_o, data=tt, append=TRUE)
res1 <- rma(yi, vi, data = data1, digits = 3, method="REML")
res2 <- rma(yi, vi, data=data1, digits=3, method="FE")

pdf(file='./results/forest_random.pdf')
forest(res1, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
	ilab=cbind(t_o, t_wo_o, c_o, c_wo_o), ilab.xpos=c(-9.5,-8,-6,-4.5), 
	cex=.75, header="Hospital", mlab="",slab=(source))
text(-16, -1, pos=4, cex=0.75, bquote(paste("Random Model (Q = ",
											.(formatC(res1$QE, digits=2, format="f")), ", df = ", .(res1$k - res1$p),
											", p = ", .(formatC(res1$QEp, digits=2, format="f")), "; ", I^2, " = ",
											.(formatC(res1$I2, digits=1, format="f")), "%)")))
dev.off()

pdf(file='./results/forest_fixed.pdf')
forest(res2, atransf=exp, at=log(c(.05, .25, 1, 4)), xlim=c(-16,6),
	ilab=cbind(t_o, t_wo_o, c_o, c_wo_o), ilab.xpos=c(-9.5,-8,-6,-4.5), 
	cex=.75, header="Hospital", mlab="",slab=(source))
text(-16, -1, pos=4, cex=0.75, bquote(paste("Fixed Model (Q = ",
											.(formatC(res2$QE, digits=2, format="f")), ", df = ", .(res2$k - res2$p),
											", p = ", .(formatC(res2$QEp, digits=2, format="f")), "; ", I^2, " = ",
											.(formatC(res2$I2, digits=1, format="f")), "%)")))
dev.off()
