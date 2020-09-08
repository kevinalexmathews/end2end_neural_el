import argparse
from bs4 import BeautifulSoup
from spacy.lang.en import English
import preprocessing.util as util

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

def process_wimcor(in_filepath, out_filepath):
    with open(in_filepath) as fin:
        content = fin.read()
    soup = BeautifulSoup(content, 'lxml')

    spacy_tokenizer = English(parser=False)

    entityNameIdMap = util.EntityNameIdMap()
    entityNameIdMap.init_compatible_ent_id()
    unknown_gt_ids = 0   # counter of ground truth entity ids that are not in the wiki_name_id.txt

    with open(out_filepath, "w") as fout:
        for idx, item in enumerate(soup.find_all('sample')):
            fout.write('DOCSTART_{}\n'.format(idx))

            lcontext = str(item.find('pmw').previous_sibling) if item.find('pmw').previous_sibling else ""
            pmw = item.find('pmw').text
            loc_pmw = len(spacy_tokenizer(lcontext))
            len_pmw = len(spacy_tokenizer(pmw))
            sample = '{} {} {}'.format(lcontext, pmw, str(item.find('pmw').next_sibling) if item.find('pmw').next_sibling else "")

            ctr = 0
            in_pmw = False
            for idx, token in enumerate(spacy_tokenizer(sample)):
                if idx == loc_pmw:
                    wiki_title = item.find('pmw')['fine']
                    ent_id = entityNameIdMap.compatible_ent_id(wiki_title)
                    if ent_id is not None:
                        fout.write('MMSTART_{}\n'.format(ent_id))

                        in_pmw = True
                        ctr = len_pmw
                    else:
                        unknown_gt_ids += 1
                    fout.write('{}\n'.format(token))
                elif in_pmw and ctr == 0:
                    in_pmw = False

                    fout.write('MMEND\n')
                    fout.write('{}\n'.format(token))
                else:
                    fout.write('{}\n'.format(token))

                ctr -= 1

            fout.write('DOCEND\n')
    print("process_wimcor    unknown_gt_ids: ", unknown_gt_ids)

if __name__ == "__main__":
    '''
    This code is modeled after prepro_aida.py
    '''

    parser = argparse.ArgumentParser('Preprocess WiMCor')
    parser.add_argument("--wimcor_folder", default="../data/basic_data/test_datasets/WiMCor/")
    parser.add_argument("--output_folder", default="../data/new_datasets/")
    args = parser.parse_args()

    process_wimcor(args.wimcor_folder+"wimcor_positive.xml", args.output_folder+"wimcor_positive.txt")

