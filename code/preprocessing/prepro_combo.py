import argparse
import os
import random
import preprocessing.util as util
from preprocessing.prepro_aida import process_aida
from preprocessing.prepro_aida import create_necessary_folders
from preprocessing.prepro_aida import split_dev_test
from preprocessing.prepro_aida import write_to_file
from preprocessing.prepro_wimcor import process_wimcor

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aida_folder",
                        default="../data/basic_data/test_datasets/AIDA/")
    parser.add_argument("--wimcor_folder",
                        default="../data/basic_data/test_datasets/WiMCor/")
    parser.add_argument("--output_folder",
                        default="../data/new_datasets/")
    parser.add_argument("--split_ratio",
                        type=float,
                        default=0.7,
                        help="ratio for split for train; rest is equally divided into dev and test")
    parser.add_argument("--add_noise",
                        dest='add_noise',
                        action='store_true',
                        help="add noise to dataset or not; for analysis")
    parser.add_argument("--no_add_noise",
                        dest='add_noise',
                        action='store_false',
                        help="add noise to dataset or not; for analysis")
    parser.add_argument("--noise_type",
                        type=str,
                        default="distort_meto_labels",
                        help="valid only if add_noise=True; \
                        distort_meto_labels OR distort_el_labels OR distort_context;")
    parser.add_argument("--reorder_samples",
                        dest='reorder_samples',
                        action='store_true',
                        help="create partitions so that dev and test have unseen entities")
    parser.add_argument("--no_reorder_samples",
                        dest='reorder_samples',
                        action='store_false',
                        help="create partitions so that dev and test have unseen entities")
    parser.set_defaults(reorder_samples=True)
    parser.set_defaults(add_noise=False)
    return parser.parse_args()

if __name__ == "__main__":
    '''
    This script creates a dataset that combines samples from AIDA and WiMCor
    to train and test a metonymy-aware entity linking system.
    '''
    args = _parse_args()
    print(args)
    create_necessary_folders(args.output_folder)

    # get AIDA samples
    split_dev_test(args.aida_folder+"testa_testb_aggregate_original", args.output_folder)
    aida_samples = process_aida(args.output_folder+"temp_aida_dev",
                                args.add_noise, args.noise_type,
                                metotype='LIT',
                                )
    os.remove(args.output_folder + "temp_aida_dev")
    os.remove(args.output_folder + "temp_aida_test")

    # get WiMCor samples
    wimcor_samples, ent_id_indices = process_wimcor(args.wimcor_folder+"wimcor_positive.xml",
                                                    args.add_noise, args.noise_type,
                                                    metotype='MET',)

    # reorder WiMCor samples according to entity ids
    if args.reorder_samples:
        reordered_wimcor_samples = []
        for ent_id in ent_id_indices.keys():
            for idx in ent_id_indices[ent_id]:
                reordered_wimcor_samples.append(wimcor_samples[idx])
        wimcor_samples = reordered_wimcor_samples

    # split the data into train, dev and test partitions
    combo_samples_train = aida_samples[:int(args.split_ratio*len(aida_samples))] + \
                            wimcor_samples[:int(args.split_ratio*len(wimcor_samples))]
    combo_samples_rest = aida_samples[int(args.split_ratio*len(aida_samples)):] + \
                            wimcor_samples[int(args.split_ratio*len(wimcor_samples)):]
    # shuffle the data; use seed to ensure reproducibility
    random.seed(42)
    random.shuffle(combo_samples_train)
    random.shuffle(combo_samples_rest)

    combo_samples_dev = combo_samples_rest[:len(combo_samples_rest)//2]
    combo_samples_test = combo_samples_rest[len(combo_samples_rest)//2:]

    print('Train: {}; Dev: {}; Test: {}'.format(len(combo_samples_train),
                                                len(combo_samples_dev),
                                                len(combo_samples_test)))

    # write the partitions to file
    is_reordered = '_reordered' if args.reorder_samples else ''
    if args.add_noise and args.noise_type=='distort_meto_labels':
        write_to_file(combo_samples_train,
                      args.output_folder+"combo"+is_reordered+"_metolabelsdistorted"+"_train.txt")
        write_to_file(combo_samples_dev,
                      args.output_folder+"combo"+is_reordered+"_metolabelsdistorted"+"_dev.txt")
        write_to_file(combo_samples_test,
                      args.output_folder+"combo"+is_reordered+"_metolabelsdistorted"+"_test.txt")
    elif args.add_noise and args.noise_type=='distort_el_labels':
        write_to_file(combo_samples_train,
                      args.output_folder+"combo"+is_reordered+"_ellabelsdistorted"+"_train.txt")
        write_to_file(combo_samples_dev,
                      args.output_folder+"combo"+is_reordered+"_ellabelsdistorted"+"_dev.txt")
        write_to_file(combo_samples_test,
                      args.output_folder+"combo"+is_reordered+"_ellabelsdistorted"+"_test.txt")
    elif args.add_noise and args.noise_type=='distort_context':
        write_to_file(combo_samples_train,
                      args.output_folder+"combo"+is_reordered+"_contextdistorted"+"_train.txt")
        write_to_file(combo_samples_dev,
                      args.output_folder+"combo"+is_reordered+"_contextdistorted"+"_dev.txt")
        write_to_file(combo_samples_test,
                      args.output_folder+"combo"+is_reordered+"_contextdistorted"+"_test.txt")
    elif not args.add_noise:
        # no perturbation; data as is;
        write_to_file(combo_samples_train,
                      args.output_folder+"combo"+is_reordered+"_train.txt")
        write_to_file(combo_samples_dev,
                      args.output_folder+"combo"+is_reordered+"_dev.txt")
        write_to_file(combo_samples_test,
                      args.output_folder+"combo"+is_reordered+"_test.txt")
