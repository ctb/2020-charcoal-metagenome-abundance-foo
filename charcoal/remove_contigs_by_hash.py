#! /usr/bin/env python
"""
Separate genomes into have-hash and not-have-hash.

Only works for fragments right now.
"""
import sys
import argparse
import sourmash
import screed
from pickle import dump


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--genome', required=True)
    p.add_argument('--hashlist', required=True)
    p.add_argument('--clean-output', required=True)
    p.add_argument('--dirty-output', required=True)
    p.add_argument('-k', '--ksize', default=31, type=int)
    p.add_argument('--scaled', default=1000, type=int)
    p.add_argument('--fragment', default=0, type=int)
    args = p.parse_args()

    assert args.fragment, "must specify --fragment"

    mh_factory = sourmash.MinHash(n=0, ksize=args.ksize, scaled=args.scaled)

    rm_hashes = set()
    for line in open(args.hashlist, 'rt'):
        line = line.strip()
        if line:
            hashval = int(line)
            rm_hashes.add(hashval)

    n = 0
    o = 0
    p = 0

    clean_fp = open(args.clean_output, 'wt')
    dirty_fp = open(args.dirty_output, 'wt')
    
    #
    # iterate over all contigs in genome file
    #
    for record in screed.open(args.genome):
        # fragment longer contigs into smaller regions?
        if args.fragment:
            for start in range(0, len(record.sequence), args.fragment):
                # fragment contigs
                seq = record.sequence[start:start + args.fragment]
                n += 1

                # for each contig, calculate scaled hashes
                mh = mh_factory.copy_and_clear()
                mh.add_sequence(seq, force=True)

                minset = set(mh.get_mins())

                if minset.intersection(rm_hashes) or not mh:
                    # dirty! discard.
                    o += 1
                    dirty_fp.write('>{}:{}-{}\n{}\n'.format(record.name.split()[0], start, start+args.fragment, record.sequence))
                    rm_hashes -= minset
                else:
                    clean_fp.write('>{}:{}-{}\n{}\n'.format(record.name.split()[0], start, start+args.fragment, record.sequence))
                    p += 1

        # deal directly with contigs in the genome file
        else:
            assert 0
            n += 1

            mh = mh_factory.copy_and_clear()
            mh.add_sequence(record.sequence, force=True)
            if not mh:
                sum_missed_bp += len(record.sequence)
                continue

            m += 1
            min_value = min(mh.get_mins())
            hash_to_lengths[min_value] = len(record.sequence)

    print('total contigs:', n)
    print('dirty contigs:', o)
    print('clean contigs:', p)

    assert not rm_hashes, rm_hashes

    return 0


if __name__ == '__main__':
    sys.exit(main())
