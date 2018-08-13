# -*- coding: utf-8 -*-
"""
    Python wrapper for LazyMole

    Jeremy Bennett, University of Tübingen 2018 (jeremypaulbennett@gmail.com)

    Uses LazyMole by Gerry Rizzo, University of Southern California (gerry.rizzo89@gmail.com)

"""

import os
from os.path import join
import numpy as np
import yaml
import subprocess
import errno


class model():
    def __init__(self,
                 basepath,
                 in_field,
                 in_source,
                 in_target,
                 dx, dy, dz,                                            # model grid cell dimensions
                 nx, ny, nz,                                            # number of grid cells in model
                 rx=1, ry=1, rz=1,                                      # graph theory refinement
                 in_skip=0,
                 in_log=True,                                           # Is K field logarithmic?
                 out_config='config.yaml',                              # Name of configuration file output
                 foldername='lazymole',                                 # Name of folder where output is saved
                 exe_path=r'src\lazymole.exe'):                         # Location of executable.
        """
        Run LazyMole connectivity metric

        Parameters
        ----------
        basepath : str
            basepath for simulations
        in_field : numpy array
            K values (same dimensions as connectivity grid)
        in_source : numpy array
            Source cells
        in_target : numpy array
            Target cells

            Filepath to .npz file

        """
        self.basepath = basepath
        self.in_field = in_field
        self.in_source = in_source
        self.in_target = in_target
        self.in_skip = in_skip
        self.in_log = in_log
        self.out_config = out_config
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.exe_path = exe_path
        self.foldername = foldername

        self.fname_field = 'field.dat'
        self.fname_source = 'source.dat'
        self.fname_target = 'target.dat'
        self.fname_res = 'hres.dat'
        self.fname_path = 'path.dat'

        """ Preliminaries """
        # Load K data
        # data = np.loadtxt(self.in_field)

        # Create folder for the connectivity run
        self.lm_path = join(os.path.abspath(basepath), self.foldername)
        try_makefolder(self.lm_path)

        """ Convert dataset """
        # if not os.path.isfile(join(self.lm_path, self.fname_field)):
        xvec, yvec, zvec = np.meshgrid(np.arange(0, nx), np.arange(0, ny), np.arange(0, nz))

        idxh = np.empty((np.size(xvec), 4), dtype=int)                     # Table matching ijk coordinates to linear coordinates
        for iv, xyzv in enumerate([xvec, yvec, zvec]):
            idxh[:, iv] = xyzv.flatten()

        idxh[:, 3] = idxh[:, 2]*nx*ny + idxh[:, 1]*nx + idxh[:, 0]                                              # Get indices for all nodes
        self.field_vec = [in_field[idxh[i, 0], idxh[i, 1], idxh[i, 2]] for i in range(0, np.size(xvec))]        # Apply to K
        np.savetxt(join(self.lm_path, self.fname_field), self.field_vec, fmt='%.5e')                                          # Save to text file

        """ Generate source and target files """
        # if not os.path.isfile(join(self.lm_path, self.fname_source)):
        sx, sy, sz = np.where(in_source == 1)
        idx_sour = [sz[i]*nx*ny + sy[i]*nx + sx[i] for i in range(len(sx))]
        np.savetxt(join(self.lm_path, self.fname_source), idx_sour, fmt='%u')

        # if not os.path.isfile(join(self.lm_path, self.fname_target)):
        tx, ty, tz = np.where(in_target == 1)
        idx_targ = [tz[i]*nx*ny + ty[i]*nx + tx[i] for i in range(len(tx))]
        np.savetxt(join(self.lm_path, self.fname_target), idx_targ, fmt='%u')

        """ Generate YAML configuration file"""
        # if not os.path.isfile(join(self.lm_path, self.out_config)):
        yout = {'grid':
                    {'cell size':
                         {'dx': self.dx, 'dy': self.dy, 'dz': self.dz},
                     'refinement':
                         {'refx': self.rx, 'refy': self.ry, 'refz': self.rz},
                     'dimensions':
                         {'nx': self.nx, 'nz': self.nz, 'ny': self.ny}},
                'input':
                    {'source':
                         {'file': self.fname_source},
                     'target':
                         {'file': self.fname_target},
                     'field':
                         {'log': self.in_log, 'skip': self.in_skip, 'file': self.fname_field}},
                'output':
                    {'path':
                         {'file': self.fname_path},
                     'resistance':
                         {'file': self.fname_res}}}

        with open(join(self.lm_path, self.out_config), 'w') as yy:
            yaml.dump(yout, yy, default_flow_style=False)

    def run(self):
        """ run process

         :return mhr (float) Minimum Hydraulic Resistance Output from console application
         :return target_id (inr) Target ID outpt from console application
         """

        import time

        run_args = [self.exe_path, self.lm_path]
        print('Running analysis with {}'.format(self.exe_path))
        # subprocess.call(run_args)
        p = subprocess.Popen(run_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # Hack to get around "press enter to continue..."
        time.sleep(20)
        out = p.communicate(input=b'\n')

        # Get values
        mhr = float(out[0].split(b'Minimum Hydraulic Resistance = ')[1].split(b'\r\n')[0])
        target_id = int(out[0].split(b'Target ID = ')[1].split(b'\r\n')[0])

        with open(join(self.lm_path, 'summary.txt'), 'w') as txtfile:
            txtfile.write('Minimum hydraulic resistance: {} \n'.format(mhr))
            txtfile.write('Target ID: {}'.format(target_id))

        return mhr, target_id

    def plot(self):
        """ Plot lazy mole"""
        pass

    def delete(self):
        """ Save summary of model run and delete folder """
        pass

    def get_mhr(self):
        """ Get minimum hydraulic resistance from calculated values """
        # Open hres.dat
        # hres = np.loadtxt(join(self.lm_path, self.fname_res))

        # Get hres values that are within target zone

        # Get smallest value


        # return mhr
        pass

def try_makefolder(makedir):
    """
    Create modflow output folder

    """
    # Create modflow output folder

    try:
        os.makedirs(makedir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


if __name__ == '__main__':
    """ Run channel example """
    import h5py

    chan_dir = join('..', 'testcases', 'channel', 'chan')
    dx = 1
    dy = 1
    dz = 0.5
    lx = 40
    ly = 20
    lz = 5
    nx = int(lx/dx)
    ny = int(ly/dy)
    nz = int(lz/dz)


    with h5py.File(join(chan_dir, 'chan.h5'), 'r') as hf:
        kfield = np.array(hf['/k_iso'])

    kfield = np.log(kfield)

    # Apply source and target values at inlet and outlet planes
    sour = np.zeros((nx, ny, nz), dtype=bool)       # Source - model inlet plane
    targ = np.zeros((nx, ny, nz), dtype=bool)       # Target - model outlet plane
    sour[0, :, :] = 1
    targ[-1, :, :] = 1

    """ LazyMole """
    lm = model(chan_dir,
               kfield,
               sour,
               targ,
               dx, dy, dz,
               nx, ny, nz)
    lm.run()
