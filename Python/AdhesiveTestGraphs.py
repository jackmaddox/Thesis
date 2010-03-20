import AdhesiveTestDataProcessing as dp
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib import rcParams

FiguresDirectory = '/home/jack/Documents/School/Grad/Thesis/Figures'

boards=dp.ImportData()
os.chdir(FiguresDirectory)
rcParams['figure.figsize']=(3.5,3.5/1.61803)
rcParams['font.size']=12.0
rcParams['legend.fontsize']='x-small'
rcParams['ytick.labelsize']='small'
rcParams['xtick.labelsize']='small'
rcParams['lines.linewidth']=0.5
rcParams['axes.labelsize']='medium'
rcParams['text.usetex']='True'
rcParams['text.latex.preamble']='\usepackage{bm}'
rcParams['patch.linewidth']=0.1
rcParams['legend.shadow']='False'
rcParams['legend.columnspacing']=2.5

power=np.array([0,0.5,1,1.5,2])

SpreadPlot=plt.figure()
ax=plt.axes([0.125,0.135,1-0.21,1-0.2])

for board in boards.bytype('THER FR4'):
	if board.name=='THER19': continue
	for tr in [board.cycles[0].tr1,board.cycles[0].tr2]:
		leg1=ax.plot(power,power*tr,color='grey')
for board in boards.bytype('PSAK FR4'):
	for tr in [board.cycles[0].tr1,board.cycles[0].tr2]:
		leg2=ax.plot(power,power*tr,color='green')
leg1=ax.plot([1],linewidth=1,color='grey',)
leg2=ax.plot([1],linewidth=1,color='green')
lg=ax.legend((leg1,leg2),('THER FR4 (35 locations)','PSAK FR4 (18 locations)'),'lower right',shadow=False)
lg.legendPatch.set_alpha(0.5)



xaxisoffset=0.1
yaxisoffset=1
ax.axis([0-xaxisoffset,2+xaxisoffset,0-yaxisoffset,20+yaxisoffset])
ax.set_xticks([0,0.5,1,1.5,2])
ax.set_xlabel(r'$P$ (W)')
ax.set_ylabel(r'$\Delta T$ (${^\circ}$C)}')

SpreadPlot.savefig('spreadplot.pdf',transparent=True)
