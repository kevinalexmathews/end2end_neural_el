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

def get_aida_countries(in_filepath):
    '''
    We consider only mentions that are country names (Country108544813).

    We consider only mentions having links to Wikipedia.
    Some entity mentions in AIDA do not have any link to Wikipedia.

    We compare the mention with the entity link. 
    If the two are different, then the mention is METONYMIC, otherwise, LITERAL.
    '''
    COUNTRY_TYPE = 'Country108544813'
    with open(in_filepath) as fin:
        in_metonymy = False
        cur_metonymy = []
        num_mentions = 0
        num_metonymic = 0
        num_countries = 0

        for line in fin:
            l = line.split('\t')

            if len(l) == 7 and l[1] == 'B':
                num_mentions += 1
                print('Mentions: {}; Countries: {}; Metonymy: {}'.format(
                    num_mentions, num_countries, num_metonymic))

            if len(l) == 7 and l[1] == 'B' \
                and COUNTRY_TYPE in get_dbpedia_categories(l[2]):
                num_countries += 1

            if len(l) == 7 and (l[1] == 'B' or l[1] == 'I') \
                and COUNTRY_TYPE in get_dbpedia_categories(l[2])  \
                and COUNTRY_TYPE not in \
                    get_dbpedia_categories(l[4][len("http://en.wikipedia.org/wiki/"):].replace('_', ' ')):
                    in_metonymy = True
                    cur_metonymy.append(line.strip())
            elif in_metonymy and len(l) != 7 and len(cur_metonymy) > 0:
                    num_metonymic += 1
                    for item in cur_metonymy:
                        print(item)

                    cur_metonymy = []
                    in_metonymy = False

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aida_folder", default="/home/mathewkn/dalab/data/basic_data/test_datasets/AIDA/")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    get_aida_countries(args.aida_folder+"aida_train.txt")

