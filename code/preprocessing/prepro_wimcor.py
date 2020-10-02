import argparse
import random
random.seed(42)
from bs4 import BeautifulSoup
import spacy
from spacy.lang.en import English
import preprocessing.util as util
from preprocessing.prepro_aida import write_to_file
from preprocessing.prepro_aida import create_necessary_folders

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

def process_wimcor(in_filepath, add_noise=None, noise_type=None, metotype='MET'):
    with open(in_filepath) as fin:
        content = fin.read()
    soup = BeautifulSoup(content, 'lxml')

    spacy_tokenizer = English(parser=False)
    vocabulary = list(spacy.load('en_core_web_sm').vocab.strings)

    entityNameIdMap = util.EntityNameIdMap()
    entityNameIdMap.init_compatible_ent_id()
    name_id_map_items = list(entityNameIdMap.wiki_name_id_map.items())
    unknown_gt_ids = 0   # counter of ground truth entity ids that are not in the wiki_name_id.txt

    samples = []
    ent_id_indices = {}
    for sample_idx, item in enumerate(soup.find_all('sample')):
        inserted_already = False
        cur_sample = []
        cur_sample.append('DOCSTART_{}\n'.format(sample_idx))

        lcontext = str(item.find('pmw').previous_sibling) if item.find('pmw').previous_sibling else ""
        pmw = item.find('pmw').text
        loc_pmw = len(spacy_tokenizer(lcontext))
        len_pmw = len(spacy_tokenizer(pmw))
        sample = '{} {} {}'.format(lcontext, pmw, str(item.find('pmw').next_sibling) if item.find('pmw').next_sibling else "")

        ctr = 0
        in_pmw = False
        for token_idx, token in enumerate(spacy_tokenizer(sample)):
            if token_idx == loc_pmw:
                wiki_title = item.find('pmw')['fine']
                ent_id = entityNameIdMap.compatible_ent_id(wiki_title)
                if ent_id is not None:
                    if add_noise and noise_type=='distort_meto_labels':
                        metotype = random.choice(['LIT', 'MET'])
                    elif add_noise and noise_type=='distort_el_labels':
                        ent_id = random.choice(name_id_map_items)[1]

                    if ent_id not in ent_id_indices.keys():
                        ent_id_indices[ent_id] = [sample_idx]
                    else:
                        ent_id_indices[ent_id].append(sample_idx)

                    cur_sample.append('MMSTART_{}_{}\n'.format(ent_id, metotype))

                    in_pmw = True
                    ctr = len_pmw
                else:
                    unknown_gt_ids += 1
                cur_sample.append('{}\n'.format(token))
            elif in_pmw and ctr == 0:
                in_pmw = False

                cur_sample.append('MMEND\n')
                if add_noise and noise_type=='distort_context':
                    cur_sample.append('{}\n'.format(random.choice(vocabulary)))
                else:
                    cur_sample.append('{}\n'.format(token))
            elif in_pmw and ctr != 0:
                cur_sample.append('{}\n'.format(token))
            else:
                if add_noise and noise_type=='distort_context':
                    cur_sample.append('{}\n'.format(random.choice(vocabulary)))
                else:
                    cur_sample.append('{}\n'.format(token))

            ctr -= 1

        cur_sample.append('DOCEND\n')

        samples.append(cur_sample)
    print("process_wimcor    unknown_gt_ids: ", unknown_gt_ids)

    return samples, ent_id_indices

if __name__ == "__main__":
    '''
    This code is modeled after prepro_aida.py
    '''

    parser = argparse.ArgumentParser('Preprocess WiMCor')
    parser.add_argument("--wimcor_folder", default="../data/basic_data/test_datasets/WiMCor/")
    parser.add_argument("--output_folder", default="../data/new_datasets/")
    args = parser.parse_args()
    create_necessary_folders(args.output_folder)

    samples = process_wimcor(args.wimcor_folder+"wimcor_positive.xml")
    write_to_file(samples, args.output_folder+"wimcor_positive.txt")

