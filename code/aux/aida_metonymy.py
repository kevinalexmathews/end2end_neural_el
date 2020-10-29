import argparse
import random
random.seed(42)
import os

import re
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

'''
DBpedia endpoints:
   http://dbpedia-live.openlinksw.com/sparql
   http://live.dbpedia.org/sparql
   http://dbpedia.org/sparql
   http://dbpedia.org/snorql
'''
sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
sparql.setReturnFormat(JSON)

def get_resource_url(mention):
    resource_url = """http://dbpedia.org/resource/""" + mention
    check_for_redirect = """
                SELECT ?page
                WHERE {
                         {<""" + resource_url + """> <http://dbpedia.org/ontology/wikiPageRedirects> ?page}
                      }
             """
    sparql.setQuery(check_for_redirect)

    try:
        resource_url = sparql.query().convert()["results"]["bindings"][0]['page']['value']
    except Exception:
        pass

    return resource_url

def get_dbpedia_categories(mention):
    '''
        To get all categories under which a page belongs
    '''
    mention = mention.replace(' ', '_')
    resource_url = get_resource_url(mention)
    query = """
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?label
                WHERE {
                         <""" + resource_url + """> rdf:type ?label
                      }
             """
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()["results"]["bindings"]
    except Exception:
        results = []

    categories = [category["label"]["value"].split('/')[-1] for category in results]
    return categories

def check_aida_mentions(in_filepath, out_filepath):
    '''
    We consider only mentions with links to Wikipedia.
    Some entity mentions in AIDA do not have any link to Wikipedia.
    These mentions are ignored.

    We compare the mention with the entity link.
    If the types are different,
        then the mention is METONYMIC, otherwise, LITERAL.
    '''
    LOCATION_TYPE = 'Location100027167'
    COUNTRY_TYPE = 'Country108544813'
    CITY_TYPE = 'City108524735'
    with open(in_filepath) as fin, open(out_filepath, 'w') as fout:
        in_metonymy = False
        cur_metonymy = []
        num_mentions = 0
        num_locations = 0
        num_countries = 0
        num_cities = 0
        num_country_metonymics = 0
        num_city_metonymics = 0

        for line in fin:
            l = line.split('\t')

            if len(l) == 7 and l[1] == 'B':
                # mention with entity links; NIL mentions are ignored
                num_mentions += 1
                fout.write('Mentions: {}; Locations: {}; Countries: {}; Country-Metonymics: {};'
                                    ' Cities: {}; City-Metonymics: {}\n'.format(
                    num_mentions, num_locations, num_countries, num_country_metonymics,
                                    num_cities, num_city_metonymics))

            if len(l) == 7 and l[1] == 'B' \
                and LOCATION_TYPE in get_dbpedia_categories(l[2]):
                fout.write('LOCATION: \t{}\n'.format(line.strip()))
                num_locations += 1

            if len(l) == 7 and l[1] == 'B' \
                and COUNTRY_TYPE in get_dbpedia_categories(l[2]):
                num_countries += 1

            if len(l) == 7 and l[1] == 'B' \
                and CITY_TYPE in get_dbpedia_categories(l[2]):
                num_cities += 1

            if len(l) == 7 and (l[1] == 'B' or l[1] == 'I') \
                and COUNTRY_TYPE in get_dbpedia_categories(l[2])  \
                and COUNTRY_TYPE not in \
                    get_dbpedia_categories(l[4][len("http://en.wikipedia.org/wiki/"):].replace('_', ' ')):
                    # country name used metonymically
                    num_country_metonymics += 1
                    in_metonymy = True
                    cur_metonymy.append(line.strip())
            elif len(l) == 7 and (l[1] == 'B' or l[1] == 'I') \
                and CITY_TYPE in get_dbpedia_categories(l[2])  \
                and CITY_TYPE not in \
                    get_dbpedia_categories(l[4][len("http://en.wikipedia.org/wiki/"):].replace('_', ' ')):
                    # city name used metonymically
                    num_city_metonymics += 1
                    in_metonymy = True
                    cur_metonymy.append(line.strip())
            elif in_metonymy and len(l) != 7: # mention over
                    fout.write('METONYMIC: {}\n'.format(cur_metonymy[0]))
                    cur_metonymy = []
                    in_metonymy = False

def split_dev_test(in_filepath, out_dir):
    with open(in_filepath) as fin, open(out_dir+"temp_aida_dev", "w") as fdev,\
            open(out_dir+"temp_aida_test", "w") as ftest:
        fout = fdev
        for line in fin:
            if line.startswith("-DOCSTART-") and line.find("testb") != -1:
                fout = ftest
            fout.write(line)

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aida_folder", default="/home/mathewkn/dalab/data/basic_data/test_datasets/AIDA/")
    parser.add_argument("--output_folder", default="/home/mathewkn/dalab/data/audit/aida_metonymy/")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()

    split_dev_test(args.aida_folder+"testa_testb_aggregate_original", args.output_folder)

    check_aida_mentions(args.aida_folder+"aida_train.txt", args.output_folder+'log-train')
    check_aida_mentions(args.output_folder+"temp_aida_dev", args.output_folder+'log-dev')
    check_aida_mentions(args.output_folder+"temp_aida_test", args.output_folder+'log-test')

    os.remove(args.output_folder + "temp_aida_dev")
    os.remove(args.output_folder + "temp_aida_test")
