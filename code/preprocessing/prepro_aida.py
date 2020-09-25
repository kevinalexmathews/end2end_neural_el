import argparse
import random
random.seed(42)
import os
import spacy
import preprocessing.util as util

def process_aida(in_filepath, add_noise=None, noise_type=None, metotype='LIT'):

    # _, wiki_id_name_map = util.load_wiki_name_id_map(lowercase=False)
    #_, wiki_id_name_map = util.entity_name_id_map_from_dump()
    entityNameIdMap = util.EntityNameIdMap()
    entityNameIdMap.init_compatible_ent_id()
    vocabulary = list(spacy.load('en_core_web_sm').vocab.strings)
    name_id_map_items = list(entityNameIdMap.wiki_name_id_map.items())
    unknown_gt_ids = 0   # counter of ground truth entity ids that are not in the wiki_name_id.txt
    ent_id_changes = 0

    samples = []
    with open(in_filepath) as fin:
        in_mention = False   # am i inside a mention span or not
        first_document = True
        inserted_already = False
        cur_sample = []
        for line in fin:
            l = line.split('\t')
            if in_mention and not (len(l) == 7 and l[1]=='I'):
                # if I am in mention but the current line does not continue the previous mention
                # then print MMEND and be in state in_mention=FALSE
                cur_sample.append("MMEND\n")
                in_mention = False

            if line.startswith("-DOCSTART-"):
                if not first_document:
                    cur_sample.append("DOCEND\n")
                    samples.append(cur_sample)
                    inserted_already = False
                    cur_sample = []
                # line = "-DOCSTART- (967testa ATHLETICS)\n"
                doc_title = line[len("-DOCSTART- ("): -2]
                cur_sample.append("DOCSTART_"+doc_title.replace(' ', '_')+"\n")
                first_document = False
            elif line == "\n":
                cur_sample.append("*NL*\n")
            elif len(l) == 7 and l[1] == 'B':  # this is a new mention
                wiki_title = l[4]
                wiki_title = wiki_title[len("http://en.wikipedia.org/wiki/"):].replace('_', ' ')
                new_ent_id = entityNameIdMap.compatible_ent_id(wiki_title, l[5])
                if new_ent_id is not None:
                    if new_ent_id != l[5]:
                        ent_id_changes += 1
                        #print(line, "old ent_id: " + l[5], " new_ent_id: ", new_ent_id)
                    if add_noise and noise_type=='distort_meto_labels':
                        metotype = random.choice(['LIT', 'MET'])
                    elif add_noise and noise_type=='distort_el_labels':
                        new_ent_id = random.choice(name_id_map_items)[1]
                    elif add_noise and noise_type=='insert_random_token_before_MMSTART' and not inserted_already:
                        random_word = random.choice(vocabulary)
                        print(random_word)
                        cur_sample.append('{}\n'.format(random_word))
                        inserted_already = True
                    cur_sample.append("MMSTART_"+new_ent_id+"_"+metotype+"\n")    # TODO check here if entity id is inside my wikidump
                                                   # if not then omit this mention
                    cur_sample.append(l[0]+"\n")  # write the word
                    in_mention = True
                else:
                    unknown_gt_ids += 1
                    cur_sample.append(l[0]+"\n") # write the word
                    print(line)
            else:
                # words that continue a mention len(l) == 7: and l[1]=='I'
                # or normal word outside of mention, or in mention without disambiguation (len(l) == 4)
                cur_sample.append(l[0].rstrip()+"\n")
        cur_sample.append("DOCEND\n")  # for the last document
        samples.append(cur_sample)
    print("process_aida     unknown_gt_ids: ", unknown_gt_ids)
    print("process_aida     ent_id_changes: ", ent_id_changes)

    return samples

def write_to_file(samples, fpath):
    print('writing to {}'.format(fpath))
    with open(fpath, 'w') as fout:
        for sample in samples:
            for item in sample:
                fout.write(item)

def split_dev_test(in_filepath, out_dir):
    with open(in_filepath) as fin, open(out_dir+"temp_aida_dev", "w") as fdev,\
            open(out_dir+"temp_aida_test", "w") as ftest:
        fout = fdev
        for line in fin:
            if line.startswith("-DOCSTART-") and line.find("testb") != -1:
                fout = ftest
            fout.write(line)


def create_necessary_folders(path):
    if not os.path.exists(path):
        os.makedirs(path)

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aida_folder", default="../data/basic_data/test_datasets/AIDA/")
    parser.add_argument("--output_folder", default="../data/new_datasets/")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    create_necessary_folders(args.output_folder)
    samples = process_aida(args.aida_folder+"aida_train.txt")
    write_to_file(samples, args.output_folder+"aida_train.txt")

    split_dev_test(args.aida_folder+"testa_testb_aggregate_original", args.output_folder)
    samples = process_aida(args.output_folder+"temp_aida_dev")
    write_to_file(samples, args.output_folder+"aida_dev.txt")
    samples = process_aida(args.output_folder+"temp_aida_test")
    write_to_file(samples, args.output_folder+"aida_test.txt")

    os.remove(args.output_folder + "temp_aida_dev")
    os.remove(args.output_folder + "temp_aida_test")