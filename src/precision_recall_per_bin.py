#!/usr/bin/env python

import collections
import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import pandas as pd


def transform_confusion_matrix(query):
    gold_standard = query.gold_standard

    bin_id_to_genome_id_to_length = {}
    for bin in query.bins:
        bin_id_to_genome_id_to_length[bin.id] = bin.mapping_id_to_length
    df_confusion = pd.DataFrame(bin_id_to_genome_id_to_length).T

    query_sequence_ids = set(query.sequence_id_to_bin_id.keys())
    gs_sequence_ids = set(gold_standard.sequence_id_to_bin_id.keys())
    genome_id_to_unassigned_bps = collections.Counter()
    for unassigned_seq_id in gs_sequence_ids - query_sequence_ids:
        genome_id = gold_standard.sequence_id_to_bin_id[unassigned_seq_id]
        genome_id_to_unassigned_bps[genome_id] += gold_standard.sequence_id_to_length[unassigned_seq_id]

    df_unassigned = pd.DataFrame.from_dict(genome_id_to_unassigned_bps, orient='index').rename(columns={0: 'unassigned'}).T
    table = df_confusion.append(df_unassigned, sort=False)
    table.fillna(0, inplace=True)
    # use log scale
    # table = table.applymap(np.log).fillna(0)

    bin_id_to_mapped_genome = {}
    for bin in query.bins:
        bin_id_to_mapped_genome[bin.id] = bin.mapping_id

    # sort bins by the number of true positives (length of mapped genome within the bin)
    bin_id_to_mapped_genome_by_length = collections.OrderedDict(sorted(bin_id_to_mapped_genome.items(), key=lambda t: bin_id_to_genome_id_to_length[t[0]][t[1]], reverse=True))

    # sort genomes
    genome_order = []
    for bin_id in bin_id_to_mapped_genome_by_length:
        mapped_genome = bin_id_to_mapped_genome_by_length[bin_id]
        if mapped_genome not in genome_order:
            genome_order.append(mapped_genome)
    genome_order += list(set(table.columns.values.tolist()) - set(genome_order))
    for genome_id in genome_id_to_unassigned_bps.keys():
        if genome_id not in genome_order:
            genome_order.append(genome_id)

    table = table.loc[list(bin_id_to_mapped_genome_by_length.keys()) + ['unassigned'], genome_order]

    for genome_id in gold_standard.get_bin_ids():
        if genome_id not in table.columns.values.tolist():
            table[genome_id] = 0

    return table
