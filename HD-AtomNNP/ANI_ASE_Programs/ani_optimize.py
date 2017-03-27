import sys
import time

# Numpy
import numpy as np

# Neuro Chem
from ase_interface import ANI
import pyNeuroChem as pync

import  ase
#from ase.build import molecule
#from ase.neb import NEB
#from ase.calculators.mopac import MOPAC
from ase.md.langevin import Langevin
from ase.io.trajectory import Trajectory
from ase.io.trajectory import Trajectory
from ase import units

from ase.optimize.fire import FIRE as QuasiNewton

from ase.md.nvtberendsen import NVTBerendsen
from ase.md import MDLogger

#from ase.neb import NEBtools
from ase.io import read, write
from ase.optimize import BFGS, LBFGS

#import matplotlib
#import matplotlib as mpl

#import matplotlib.pyplot as plt

#import seaborn as sns
#%matplotlib inline

# Set required files for pyNeuroChem
anipath  = '/home/jujuman/Dropbox/ChemSciencePaper.AER/ANI-c08e-ccdissotest1-ntwk'
cnstfile = anipath + '/rHCNO-4.6A_16-3.1A_a4-8.params'
saefile  = anipath + '/sae_6-31gd.dat'
nnfdir   = anipath + '/networks/'

# Construct pyNeuroChem class
nc = pync.molecule(cnstfile, saefile, nnfdir, 0)

#bz = read('C_100.xyz')
bz = read('/home/jujuman/Research/ReactiondEtest/Numbering/prod.xyz')

#L = 75.0
#bz.set_cell(([[L,0,0],[0,L,0],[0,0,L]]))
#bz.set_pbc((True, True, True))

bz.set_calculator(ANI(False))
bz.calc.setnc(nc)

start_time = time.time()
dyn = LBFGS(bz)
dyn.run(fmax=0.001)
print('[ANI Total time:', time.time() - start_time, 'seconds]')

# Write visualization of molecule
f = open("optmol_begin.xyz",'w')
f.write('\n' + str(len(bz)) + '\n')
for i in bz:
    f.write(str(i.symbol) + ' ' + str(i.x) + ' ' + str(i.y) + ' ' + str(i.z) + '\n')
f.close()