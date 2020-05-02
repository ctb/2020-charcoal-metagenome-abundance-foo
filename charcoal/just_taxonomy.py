#! /usr/bin/env python
"""
Remove bad contigs based solely on taxonomy.

CTB TODO:
* optionally eliminate contigs with no taxonomy
"""
import argparse
import gzip
from collections import Counter

import screed

import sourmash
from sourmash.lca.command_index import load_taxonomy_assignments
from sourmash.lca import LCA_Database

from . import utils


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--genome', help='genome file', required=True)
    p.add_argument('--lineages_csv', help='lineage spreadsheet', required=True)
    p.add_argument('--matches_sig', help='all relevant matches', required=True)
    p.add_argument('--clean', help='cleaned contigs', required=True)
    p.add_argument('--dirty', help='dirty contigs', required=True)
    args = p.parse_args()

    tax_assign, _ = load_taxonomy_assignments(args.lineages_csv,
                                              start_column=3)
    print(f'loaded {len(tax_assign)} tax assignments.')

    with open(args.matches_sig, 'rt') as fp:
        siglist = list(sourmash.load_signatures(fp))

    if not siglist:
        print('no matches for this genome, exiting.')
        sys.exit(-1)

    empty_mh = siglist[0].minhash.copy_and_clear()
    ksize = empty_mh.ksize
    scaled = empty_mh.scaled

    lca_db = LCA_Database(ksize=ksize, scaled=scaled)

    for ss in siglist:
        ident = ss.name()
        ident = ident.split()[0]
        ident = ident.split('.')[0]
        lineage = tax_assign[ident]

        lca_db.insert(ss, ident=ident, lineage=lineage)

    print(f'loaded {len(siglist)} signatures & created LCA Database')

    print(f'pass 1: reading contigs from {args.genome}')
    entire_mh = empty_mh.copy_and_clear()
    for n, record in enumerate(screed.open(args.genome)):
        entire_mh.add_sequence(record.sequence, force=True)

    # get all of the hash taxonomy assignments for this contig
    hash_assign = sourmash.lca.gather_assignments(entire_mh.get_mins(),
                                                  [lca_db])

    # count them and find major
    counts = Counter()
    for hashval, lineages in hash_assign.items():
        for lineage in lineages:
            counts[lineage] += 1

    # make sure it's strain or species level
    assign, count = next(iter(counts.most_common()))
    f_major = count / len(hash_assign)
    print(f'{f_major*100:.1f}% of hashes identify as {assign}')
    if assign[-1].rank not in ('species', 'strain'):
        print(f'rank of major assignment is f{assign[-1].rank}; quitting')
        sys.exit(-1)

    clean_fp = gzip.open(args.clean, 'wt')
    dirty_fp = gzip.open(args.dirty, 'wt')

    # now, find disagreeing contigs.
    print(f'pass 2: reading contigs from {args.genome}')
    for n, record in enumerate(screed.open(args.genome)):
        clean = True               # default to clean

        mh = empty_mh.copy_and_clear()
        mh.add_sequence(record.sequence, force=True)

        if mh:
            # get all of the hash taxonomy assignments for this contig
            ctg_assign = sourmash.lca.gather_assignments(mh.get_mins(),
                                                         [lca_db])

            ctg_tax_assign = sourmash.lca.count_lca_for_assignments(ctg_assign)
            if ctg_tax_assign:
                ctg_lin, lin_count = next(iter(ctg_tax_assign.most_common()))

                # assignment outside of genus? dirty!
                if ctg_lin[-1].rank not in ('species', 'strain', 'genus'):
                    clean = False
                    print(f'dirty! {ctg_lin[-1].rank}')
                elif not utils.is_lineage_match(assign, ctg_lin, 'genus'):
                    clean = False
                    print(f'dirty! {ctg_lin}')
                
        # if long contig / many hashes, ...
        
        # if short contig / few hashes, ...

        if clean:
            clean_fp.write(f'>{record.name}\n{record.sequence}\n')
        else:
            dirty_fp.write(f'>{record.name}\n{record.sequence}\n')


if __name__ == '__main__':
    main()