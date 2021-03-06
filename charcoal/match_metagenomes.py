#! /usr/bin/env python
"""
Take output of 'process_genome.py', match hashes against many metagenomes.
"""
import sys
import argparse
from pickle import load, dump
import numpy as np
import csv
import os

import sourmash

from . import utils                              # charcoal utils


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--load-hashes', required=True)
    p.add_argument('--metagenome-sigs-list', required=True)
    p.add_argument('--matrix-csv-out', required=True)
    p.add_argument('--matrix-pickle-out', required=True)
    p.add_argument('-d', '--metagenome-sigs-dir', default=None)
    p.add_argument('-k', '--ksize', type=int, default=31)
    args = p.parse_args()

    with open(args.load_hashes, 'rb') as fp:
        hash_to_lengths = load(fp)
        assert hash_to_lengths.ksize == args.ksize

    print('loaded {} hashes from {}'.format(len(hash_to_lengths), args.load_hashes))

    with open(args.metagenome_sigs_list, 'rt') as fp:
        metagenome_sigs = [ x.strip() for x in fp ]

    if args.metagenome_sigs_dir:
        metagenome_sigs = [ os.path.join(args.metagenome_sigs_dir, k) for k in metagenome_sigs ]

    matrix = np.zeros((len(metagenome_sigs), len(hash_to_lengths)))

    mm = utils.MetagenomesMatrix(hash_to_lengths.genome_file,
                                 list(hash_to_lengths),
                                 hash_to_lengths.fragment_size,
                                 args.ksize)

    for i, sigfile in enumerate(metagenome_sigs):
        print('loading metagenome sig from', sigfile)
        ss = sourmash.load_one_signature(sigfile, ksize=args.ksize)

        metag_scaled = ss.minhash.scaled
        query_scaled = hash_to_lengths.scaled

        if metag_scaled != query_scaled:
            print("** warning: metagenome scaled {} != query scaled {}".format(metag_scaled, query_scaled))

        mins = ss.minhash.get_mins(with_abundance=True)

        m = 0
        for j, query in enumerate(sorted(hash_to_lengths)):
            count = mins.get(query, 0)
            if count:
                m += 1

                matrix[i][j] = count

        print('...', i, len(metagenome_sigs), sigfile, len(hash_to_lengths), m)

    print('writing {} x {} matrix'.format(len(metagenome_sigs), len(hash_to_lengths)))
    with open(args.matrix_csv_out, 'wt') as outfp:
        w = csv.writer(outfp)
        for i in range(len(metagenome_sigs)):
            y = []
            for j in range(len(hash_to_lengths)):
                y.append('{}'.format(matrix[i][j]))
            w.writerow(y)

    mm.mat = matrix
    with open(args.matrix_pickle_out, 'wb') as outfp:
        dump(mm, outfp)

    return 0


if __name__ == '__main__':
    sys.exit(main())
