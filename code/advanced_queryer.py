import pandas as pd
from nltk.stem import SnowballStemmer
import os
from question_two import *
import warnings
pd.options.mode.chained_assignment = None
# ---------------------------------------------------------------------------- #
#                          Couple of usefull functions                         #
# ---------------------------------------------------------------------------- #

stemmer = SnowballStemmer("english")

def actual_indexes(path='../shared_stuff/indexes'):
    ''' 
        Given the path containing the stored indexes the function returns the dictionary that maps
        each index name with the path of the directory containing the relative json files.
    '''
    ret = dict()
    for idx_dir in os.listdir(path):
        if idx_dir.startswith('.'): continue
        idx_path = os.path.join(path,idx_dir)
        ret[idx_dir] = idx_path
    return ret


def get_url_from_idx(idx, path='../shared_stuff/url_list.txt'):
    '''
    function to get the urls given the index
    
    INPUT: indexes, path of txt file of url
    OUTPUT: urls 
    '''
    
    with open(path, 'r') as f:
        urls = f.readlines()
    return urls[idx]

# ---------------------------------------------------------------------------- #
#                                 Let's Parse!                                 #
# ---------------------------------------------------------------------------- #

def parse_advanced_query(query):
    '''
    function to parse a query splitting word and fields where we are searching the word.
    Return the fields with inverted indexes of the words

    INPUT:query
    OUTPUT:parsed query 
    '''
    cum = []
    ret = dict()
    act_ind = actual_indexes()
    print(query.split(' '))
    for word in query.split(' '):
        if word.startswith('['):
            k = word[1:-1]
            if k not in act_ind:
                raise ValueError(f"You cannot query the field {k}, you can only choose between: {list(act_ind.keys())}")
            ret[k] = cum
            cum = []
        else:
            cum.append(word)
    return {k: parse_query(v, read_dict_from_file(filename=os.path.join(act_ind[k], 'vocabulary.json'))) for k,v in ret.items()}


def get_advanced_results(query_dict):
    '''
    function that uses the parsed query to find all the documents that match the request of the user

    INPUT: parsed query
    OUTPUT: indexes of the documents that match the query
    '''
    ret = dict()
    act_ind = actual_indexes()
    for k in query_dict:
        inv_idx = read_dict_from_file(os.path.join(act_ind[k], 'inv_idx.json'))
        if len(query_dict[k]) != 0:
            ret[k] = get_results(query_dict[k], inv_idx)
    
    if len(ret)==0:
        return set()
    return set.intersection(*ret.values())


WEIGHT = {'title': 0.7, 'staff': 0.05, 'voices': 0.08, 'synopsis': 0.05, 'characters': 0.12}

def score(df, query_len):
    '''
    function to calcolate the score of a query given the datafrmae

    INPUT: dataframe, query len in the format query_len={k: len(v) for k, v in parsed_query.items()}
    OUTPUT:score 
    '''
    'title: len_queryper_title, staff: len_queryper_staff,  ...'
    global WEIGHT
    cum = 0
    for i, q_i in query_len.items():
        p_i = WEIGHT[i]   
        d_i = len(df[i].split(' '))
        cum += (q_i/d_i)*p_i
    return cum

def get_printable_doc(df,idx, score):
    '''
    funtion to print the result in dataframe format with columns title,synopsis,url and score'
    
    INPUT: dataframe,indexes,score
    OUTPUT: dataframe
    '''
    ret = df.iloc[idx]
    url = get_url_from_idx(idx)
    ret['url'] = url
    ret['score'] = score
    return ret[['title', 'synopsis', 'url', 'score']].to_frame().transpose()

def query_anime(df, query, k=None):
    '''
    function to execute the query on the dataframe given the int number k  of elements we want as output

    INPUT:dataframe,query, k
    -NOTE- the query has the following shape: ```word1 word2 [where_to_search] word3 word4 [where_t_s2] ...```"<br
    
    OUTPUT: the result in dataframe format 
    '''
    
    parsed_query = parse_advanced_query(query)
    results = list(get_advanced_results(parsed_query))

    if len(results)==0:
        warnings.warn(f"Cannot find any anime for the query: '{query}'")
        return pd.DataFrame(columns=['doc_id', 'title', 'description', 'url', 'score'])
    query_len = {k: len(v) for k, v in parsed_query.items()}

    scores = [(idx, score(df.iloc[idx], query_len)) for idx in results]

    scores = sorted(scores, key=lambda coppia: -coppia[1])

    # Selecting the first k elements
    if k is None or k>len(scores):
        k = len(scores)
    scores = scores[:k]

    return pd.concat(list(map(lambda tupla: get_printable_doc(df, *tupla), scores))).reset_index().rename(columns={"index": "doc_id", "synopsis": "description"})

    