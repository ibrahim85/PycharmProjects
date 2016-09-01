__author__ = 'jujuman'

import numpy as np
import statsmodels.api as sm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import os
import matplotlib as mpl
import random
import graphtools as gt
import scipy.interpolate


def getmaxmin(data):
    x, y, z, d = gt.calculateelementdiff2D(data)
    z = gt.convert * z
    return z.max(), z.min()


def graphEdiff2D(ax, data1, data2, title):
    x, y, z, d = gt.calculatecompareelementdiff2D(data1, data2)

    z = gt.convert * z

    # Set up a regular grid of interpolation points
    xi, yi = np.linspace(x.min(), x.max(), 100), np.linspace(y.min(), y.max(), 100)
    xi, yi = np.meshgrid(xi, yi)

    # Interpolate
    rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
    zi = rbf(xi, yi)

    im = ax.imshow(zi, vmin=z.min(), vmax=z.max(), origin='lower',
                   extent=[x.min(), x.max(), y.min(), y.max()])

    ax.set_title(title,fontsize=14)
    # plt.xlabel('Structure')
    # plt.ylabel('Structure')

    ax.scatter(x, y, c=z, vmin=z.min(), vmax=z.max())
    ax.plot([x.min(),x.max()],[y.min(),x.max()],'--',color='red',linewidth=4,alpha=0.8)

    ax.set_xlim([-0.02*x.max(),x.max()+0.02*x.max()])
    ax.set_ylim([-0.02*y.max(),y.max()+0.02*y.max()])

    ax.grid(True)

    return im


def graphEdiffDelta2D(ax, data1, data2, Na):
    data1 = gt.convert * data1
    data2 = gt.convert * data2

    x, y, z, d = gt.calculateelementdiff2D(data1)
    x2, y2, z2, d2 = gt.calculateelementdiff2D(data2)

    RMSE = gt.calculaterootmeansqrerror(d,d2) / float(Na)

    print ('dataz1:',z)
    print ('dataz2:',z2)

    z = np.abs(z - z2)

    print ('zdiff:',z)

    # Set up a regular grid of interpolation points
    xi, yi = np.linspace(x.min(), x.max(), 100), np.linspace(y.min(), y.max(), 100)
    xi, yi = np.meshgrid(xi, yi)

    # Interpolate
    rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
    zi = rbf(xi, yi)

    im = ax.imshow(zi, vmin=z.min(), vmax=z.max(), origin='lower',
                   extent=[x.min(), x.max(), y.min(), y.max()])

    ax.set_title('Difference Plot (symmetric)\nRMSE: ' + "{:.5f}".format(RMSE) + 'kcal/mol/atom Atoms: ' + str(natm),fontsize=14)
    # plt.xlabel('Structure')
    # plt.ylabel('Structure')

    ax.scatter(x, y, c=z, vmin=z.min(), vmax=z.max())

    ax.set_xlim([-0.02*x.max(),x.max()+0.02*x.max()])
    ax.set_ylim([-0.02*y.max(),y.max()+0.02*y.max()])

    #ax.plot([x.min(),x.max()],[y.min(),x.max()],color='red',linewidth=4)
    ax.grid(True)

    return im


# -----------------------
cmap = mpl.cm.brg
# ------------5412.mordor
# AM1 vs Act
# ------------
user = os.environ['USER']

#savefile = 'test.pdf'
networktag = 'c07b-64-64-64-32-r32-a-8x8-ac3.1-rc4.5'
dir = '/Research/trainingcases/wB97X-631gd-train-highgarden/nw-64-64-64-32/train_07-a3.1A_r4.5/'
#dir = '/Research/trainingcases/wB97X-631gd-train-highgarden/nw-64-32-32/train_07-a3.1A_r5.1/'

#file = 'pp_01_test.dat_graph'
#file = 'polypep_test.dat_graph'
#file = 'C8H16-isomers_test.dat_graph'
file = 'benzamide_conformers-0_test.dat_graph'
file2 = 'benzamide_conformersPM6-0_test.dat_graph'
#file = 'pentadecane_test.dat_graph'
#file2 = 'pentadecanePM6_test.dat_graph'
#file = 'retinolconformer_test.dat_graph'
#file2 = 'retinolconformerPM6_test.dat_graph'
#file = 'atazanavir_AM1_CLN_test.dat_graph'

natm = 16

prob = 1.0

data1, data2 = gt.getfltsfromfileprob('/home/' + user + dir + file, ' ', [1], [2], prob)
data2, data3 = gt.getfltsfromfileprob('/home/' + user + dir + file2, ' ', [1], [2], prob)

font = {'family': 'Bitstream Vera Sans',
        'weight': 'normal',
        'size': 10}

plt.rc('font', **font)

fig, axes = plt.subplots(nrows=1, ncols=2)

#im1 = graphEdiff2D(axes.flat[0], data1, data2, 'Top left: ANN - c07b\nBottom right: wB97x/6-31g*')
im1 = graphEdiff2D(axes.flat[0], data1, data2, 'Top left: PM6\nBottom right: wB97x/6-31g*')
im2 = graphEdiffDelta2D(axes.flat[1], data1, data2, natm)

th = fig.suptitle('300K norm. mode generated conformers of Benzamide\n(Rcr=4.5$\AA$)')
#th = fig.suptitle('300K norm. mode generated conformers of\nH-Gly-Pro-Hyp-Gly-Ala-Gly-OH')
#th = fig.suptitle('Linearly interpolated energy difference\nbetween conformers of Retinol')
th.set_fontsize(26)
th.set_position([0.5,0.98])

#fig.text(0.5, 0.03, 'Network tag: ' + networktag,fontsize=10,verticalalignment='center',horizontalalignment='center')

cbaxes = fig.add_axes([0.13, 0.09, 0.35, 0.02])
ch1 = fig.colorbar(im1, ax=axes.ravel().tolist(),cax=cbaxes, orientation='horizontal')
ch1.set_label('$\Delta$E kcal/mol',fontsize=12)

cbaxes = fig.add_axes([0.55, 0.09, 0.35, 0.02])
ch2 = fig.colorbar(im2, ax=axes.ravel().tolist(),cax=cbaxes, orientation='horizontal')
ch2.set_label('|$\Delta\Delta$E| kcal/mol',fontsize=12)

# -----
# PLOT
# -----
#plt.show()
#savedir = '/home/jujuman/Dropbox/Research/HD-AtomNNP-Results/FiguresForMeet/'

#plt.savefig(savedir+savefile,format='pdf')
plt.show()
