from __future__ import print_function
from rdkit import Chem
from rdkit.Chem import AllChem
import random
import numpy as np
import re
import graphtools as gt
import sys
import time

# PyNeuroChem
sys.path.append('/home/jujuman/Gits/NeuroChem/pyase_interface')
from neurochemToASE_iface import NeuroChem2ASE
import pyNeuroChem as pync

# ASE
from ase.io import read, write
from ase import Atoms
from ase.optimize import BFGS, LBFGS

def formatsmilesfile(file):
    ifile = open(file, 'r')
    contents = ifile.read()
    ifile.close()    

    p = re.compile('([^\s]*).*\n')
    smiles = p.findall(contents)
    
    ofile = open(file, 'w')
    for mol in smiles:    
        ofile.write(mol + '\n')
    ofile.close()

#-------- Parameters -----------

gdb = '08'

R = 0.3
#wdir = '/home/jujuman/Research/GDB-11-wB97X-6-31gd/dnntsgdb11_10/' #working directory
smfile = '/home/jujuman/Research/RawGDB11Database/gdb11_size' + gdb + '.smi' # Smiles file
At = ['C', 'O', 'N'] # Hydrogens added after check
P = 1.0

# Set required files for pyNeuroChem
anipath  = '/home/jujuman/Research/wB97X-631gd-train-highgarden/train_08-a3.1A_r4.6_AEV384_1'
cnstfile = anipath + '/rHCNO-4.6A_16-3.1A_a4-8.params'
saefile  = anipath + '/../sae_6-31gd.dat'
nnfdir   = anipath + '/networks/'

dir = '/home/jujuman/Research/LHL-DATA-ANI-c08e/'
gdbname = 'gdb' + gdb + '_opt'

#------- End Parameters ---------

# Construct pyNeuroChem class
nc = pync.pyNeuroChem(cnstfile, saefile, nnfdir, 0)

#fix the file
formatsmilesfile(smfile)

#molecules = Chem.SmilesMolSupplier('/home/jujuman/Research/ANN-Test-Data/GDB-11/gdb11_size02.smi', nameColumn=0)
molecules = Chem.SmilesMolSupplier(smfile, nameColumn=0)
Nmol = 0

NH = 0
NC = 0
NN = 0
NO = 0

NHt = 24 * len(molecules)
NCt = 10 * len(molecules)
NNt = 10 * len(molecules)
NOt = 10 * len(molecules)

AV_H = [np.empty((NHt,256),dtype=np.float32),
        np.empty((NHt,128),dtype=np.float32),
        np.empty((NHt,64) ,dtype=np.float32),
        np.empty((NHt,1)  ,dtype=np.float32)]

AV_C = [np.empty((NCt,256),dtype=np.float32),
        np.empty((NCt,128),dtype=np.float32),
        np.empty((NCt,64) ,dtype=np.float32),
        np.empty((NCt,1)  ,dtype=np.float32)]

AV_N = [np.empty((NNt,256),dtype=np.float32),
        np.empty((NNt,128),dtype=np.float32),
        np.empty((NNt,64) ,dtype=np.float32),
        np.empty((NNt,1)  ,dtype=np.float32)]

AV_O = [np.empty((NOt,256),dtype=np.float32),
        np.empty((NOt,128),dtype=np.float32),
        np.empty((NOt,64) ,dtype=np.float32),
        np.empty((NOt,1)  ,dtype=np.float32)]

idir = dir + 'indices/'
adir = dir + 'activations/'

fH = open(idir + 'H-atomic-' + gdbname + '.idx', 'w')
fC = open(idir + 'C-atomic-' + gdbname + '.idx', 'w')
fN = open(idir + 'N-atomic-' + gdbname + '.idx', 'w')
fO = open(idir + 'O-atomic-' + gdbname + '.idx', 'w')

fE = open(dir + 'tenergy/E-total-' + gdbname + '.dat', 'w')
fS = open(dir + 'smiles/smiles-' + gdbname + '.dat', 'w')

for m in molecules:
    if m is None: continue

    typecheck = False
    for a in m.GetAtoms():
        sym = str(a.GetSymbol())
        count = 0

        for i in At:
            if i is sym:
                count = 1

        if count is 0:
            typecheck = True

    if typecheck is False and random.random() < P and Nmol != 47008:

        m = Chem.AddHs(m) # Add Hydrogens
        print('Molecule ', str(Nmol) ,': ', Chem.MolToSmiles(m))
        AllChem.EmbedMolecule(m) # Embed in 3D Space
        AllChem.UFFOptimizeMolecule(m) # Classical Optimization

        #---------------------------------------------

        #print('Number of Atoms: ', m.GetNumAtoms())
        #print('Number of Bonds: ', m.GetNumBonds())
        #print('Number of Conformers: ', m.GetNumConformers())
        
        if m.GetNumConformers() > 1:
            print('MORE THAN ONE CONFORMER!')
            exit(1)

        xyz = np.ndarray(shape=(m.GetNumAtoms(),3), dtype=np.float32)
        typ = []
        tstr = ''
        hbr = []

        for i in range (0,m.GetNumAtoms()):
            pos = m.GetConformer().GetAtomPosition(i)
            sym = m.GetAtomWithIdx(i).GetSymbol()
            hyb = m.GetAtomWithIdx(i).GetHybridization()
            #print (' ' + str(sym) + ' ' + str(hyb) + ' ' + "{:.5f}".format(pos.x) + ' ' + "{:.5f}".format(pos.y) + ' ' + "{:.5f}".format(pos.z))
            xyz[i,0] = pos.x
            xyz[i,1] = pos.y
            xyz[i,2] = pos.z
            typ.append(sym)
            tstr += sym
            hbr.append(str(hyb))

        # Set molecule
        geometry = Atoms(tstr,xyz)

	# Setup ANI and calculate single point energy
        geometry.set_calculator(NeuroChem2ASE(nc))
	
	# Geometry optimization with BFGS
        start_time = time.time()
        dyn = LBFGS(geometry,logfile='logfile.out')
        dyn.run(fmax=0.0001,steps=500)
        Ns = dyn.get_number_of_steps()
        print('[ANI Total time:', time.time() - start_time, 'seconds. Steps: ', Ns,']')

	# Get potential
        E1 = geometry.get_potential_energy()

	# Get geometry
        xyz = geometry.get_positions()
        gt.writexyzfile(dir + 'xyz/mol-' + gdbname + '-' + str(Nmol) + '.xyz',xyz,typ)

        #print('Energy:  ' + str(E1))

        fE.write("{:.10f}".format(E1) + '\n')
        fS.write(Chem.MolToSmiles(m) + '\n')

        '''
        types = np.zeros(4,int)
        for i in range (0,m.GetNumAtoms()):
            if typ[i] == 'H':
                types[0] += 1
            elif typ[i] == 'C':
                types[1] += 1
            elif typ[i] == 'N':
                types[2] += 1
            elif typ[i] == 'O':
                types[3] += 1
            else:
                print ('!ERROR! Invalid type')
                exit()

        #print ('Types: ' + str(types))

        for a in range(0,len(AV_H)):
            AV_H[a] = np.vstack([AV_H[a], np.empty((types[0], AV_H[a].shape[1]), dtype=np.float32)])

        for a in range(0,len(AV_C)):
            AV_C[a] = np.vstack([AV_C[a], np.empty((types[1], AV_C[a].shape[1]), dtype=np.float32)])

        for a in range(0,len(AV_N)):
            AV_N[a] = np.vstack([AV_N[a], np.empty((types[2], AV_N[a].shape[1]), dtype=np.float32)])

        for a in range(0,len(AV_O)):
            AV_O[a] = np.vstack([AV_O[a], np.empty((types[3], AV_O[a].shape[1]), dtype=np.float32)])
        '''

        for i in range (0,m.GetNumAtoms()):

            if typ[i] == 'H':
                for a in range(0,len(AV_H)):
                    AV = nc.activations(atom_idx=i, layer_idx=a)
                    AV_H[a][NH] = AV

                fH.write(str(NH) + ',' +
                         str(i) + ',' +
                         str(Nmol) + '\n')
                NH += 1

            if typ[i] == 'C':
                for a in range(0,len(AV_H)):
                    AV = nc.activations(atom_idx=i, layer_idx=a)
                    AV_C[a][NC] = AV

                fC.write(str(NC) + ',' +
                         str(i) + ',' +
                         str(Nmol) + '\n')
                NC += 1

            if typ[i] == 'N':
                for a in range(0,len(AV_H)):
                    AV = nc.activations(atom_idx=i, layer_idx=a)
                    AV_N[a][NN] = AV

                fN.write(str(NN) + ',' +
                         str(i) + ',' +
                         str(Nmol) + '\n')
                NN += 1

            if typ[i] == 'O':
                for a in range(0,len(AV_H)):
                    AV = nc.activations(atom_idx=i, layer_idx=a)
                    AV_O[a][NO] = AV

                fO.write(str(NO) + ',' +
                         str(i) + ',' +
                         str(Nmol) + '\n')
                NO += 1

        Nmol += 1

print ("|---------Computations Complete----------|")

fH.close()
fC.close()
fN.close()
fO.close()
fE.close()
fS.close()

print('Nmol: ' + str(Nmol))

szs = np.array([AV_H[0].shape[1],
                AV_H[1].shape[1],
                AV_H[2].shape[1],
                AV_H[3].shape[1]],
                dtype=int)

np.savez(adir + 'H-LHL-data-' + gdbname,l0=AV_H[0][0:NH,:]
                                       ,l1=AV_H[1][0:NH,:]
                                       ,l2=AV_H[2][0:NH,:]
                                       ,l3=AV_H[3][0:NH,:]
                                       ,sz = szs)

np.savez(adir + 'C-LHL-data-' + gdbname,l0=AV_C[0][0:NC,:]
                                       ,l1=AV_C[1][0:NC,:]
                                       ,l2=AV_C[2][0:NC,:]
                                       ,l3=AV_C[3][0:NC,:]
                                       ,sz = szs)

np.savez(adir + 'N-LHL-data-' + gdbname,l0=AV_N[0][0:NN,:]
                                       ,l1=AV_N[1][0:NN,:]
                                       ,l2=AV_N[2][0:NN,:]
                                       ,l3=AV_N[3][0:NN,:]
                                       ,sz = szs)

np.savez(adir + 'O-LHL-data-' + gdbname,l0=AV_O[0][0:NO,:]
                                       ,l1=AV_O[1][0:NO,:]
                                       ,l2=AV_O[2][0:NO,:]
                                       ,l3=AV_O[3][0:NO,:]
                                       ,sz = szs)
