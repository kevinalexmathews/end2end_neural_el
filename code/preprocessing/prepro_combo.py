import argparse
import os
import random
import preprocessing.util as util
from preprocessing.prepro_aida import process_aida
from preprocessing.prepro_aida import create_necessary_folders
from preprocessing.prepro_aida import split_dev_test
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
    return parser.parse_args()

def write_to_file(samples, fpath):
    with open(fpath, 'w') as fout:
        for sample in samples:
            for item in sample:
                fout.write(item)

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
                                args.output_folder+"aida_dev_out_temp.txt")
    os.remove(args.output_folder + "temp_aida_dev")
    os.remove(args.output_folder + "temp_aida_test")
    os.remove(args.output_folder + "aida_dev_out_temp.txt")

    # get WiMCor samples
    wimcor_samples = process_wimcor(args.wimcor_folder+"wimcor_positive.xml",
                                    args.output_folder+"wimcor_positive_out_temp.txt",
                                    metotype='MET')
    os.remove(args.output_folder + "wimcor_positive_out_temp.txt")

    # merge and randomly shuffle
    combo_samples = aida_samples + wimcor_samples
    random.shuffle(combo_samples)

    # split the combo in train, dev and test partition
    combo_samples_train = combo_samples[:int(args.split_ratio*len(combo_samples))]
    combo_samples_rest = combo_samples[int(args.split_ratio*len(combo_samples)):]

    combo_samples_dev = combo_samples_rest[:len(combo_samples_rest)//2]
    combo_samples_test = combo_samples_rest[len(combo_samples_rest)//2:]

    print('Train: {}; Dev: {}; Test: {}'.format(len(combo_samples_train),
                                                len(combo_samples_dev),
                                                len(combo_samples_test)))

    # write the partitions to file
    write_to_file(combo_samples_train, args.output_folder+"combo_train.txt")
    write_to_file(combo_samples_dev, args.output_folder+"combo_dev.txt")
    write_to_file(combo_samples_test, args.output_folder+"combo_test.txt")

