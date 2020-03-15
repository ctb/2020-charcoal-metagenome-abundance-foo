"""
utility functions for charcoal.
"""
import math
import numpy as np
from numpy import genfromtxt

def load_and_normalize(filename, delete_empty=False):
    """
    Load metagenome x hash matrices, construct distance matrix.
    """
    mat = genfromtxt(filename, delimiter=',')
    n_hashes = mat.shape[1]
    n_orig_hashes = n_hashes

    # go through and normalize all the sample-presence vectors for each hash;
    # track those with all 0s for later removal.
    to_delete = []
    for i in range(n_hashes):
        if sum(mat[:, i]):
            mat[:, i] /= math.sqrt(np.dot(mat[:, i], mat[:, i]))
        else:
            to_delete.append(i)

    if delete_empty:
        # remove all columns with zeros
        print('removing {} null presence vectors'.format(len(to_delete)))
        for row_n in reversed(to_delete):
            mat = np.delete(mat, row_n, 1)

        assert mat.shape[1] == n_hashes - len(to_delete)

    n_hashes = mat.shape[1]

    # construct distance matrix using angular distance
    D = np.zeros((n_hashes, n_hashes))
    for i in range(n_hashes):
        for j in range(n_hashes):
            cos_sim = np.dot(mat[:, i], mat[:, j])
            cos_sim = min(cos_sim, 1.0)
            ang_sim = 1 - 2*math.acos(cos_sim) / math.pi
            D[i][j] = ang_sim

    # done!
    return D, n_orig_hashes
