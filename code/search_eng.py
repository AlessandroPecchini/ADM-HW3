import pandas as pd
import numpy as np
import math
import string
import json
from operator import itemgetter

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer

def has_digits(s):
    """
    This function checks whether a string
    contains any digits
    
    Arguments
        s : string
        
    Returns
        (bool) True / False
    """
    
    return len([char for char in s if char.isdigit()]) != 0


def bad_words():
    """
    This function creates a list with words
    that should be excluded from the vocabulary
    during preprocessing, including punctuation,
    stopwords et similia
    
    Arguments
        none
        
    Returns
        (list)
    """
    
    punct = list(string.punctuation)
    punct += ["...", "''", "``", '""']
    
    stops = stopwords.words("english")
    
    other_suffixes = ["'s", "n't"]
    
    return punct + stops + other_suffixes


def preprocess(text, stemmer):
    """
    This function preprocesses some text (a document)
    by isolating each word, excluding stopwords et similia,
    and finally stemming them
    
    Arguments
        text : (string)
        stemmer : stemmer object, e.g. SnowBallStemmer()
    
    Returns
        (list) preprocessed input text
    """
    
    # between some words there is /, let's replace it with space
    text = str(text).replace("/"," ") 
    
    tokens = word_tokenize(text)
        
    return [stemmer.stem(w) for w in tokens 
            if w not in bad_words() and not has_digits(w) and len(w) == len(w.encode())]


def create_vocab(corpus):
    """
    This function creates a set of unique
    and preprocessed words from a corpus
    
    Arguments
        corpus : pandas df column or list-like
    
    Returns
        vocab  : dictionary with the words as keys
                 and a unique integer for each as values
    """
    
    vocab = set()
    
    for doc in corpus:
        vocab.update(set(doc))

    return {word:idx for idx, word in enumerate(vocab)}
    

def save_dict_to_file(dct, filename):
    """
    This function saves a dictionary 
    to an external JSON file
    
    Arguments
        dct       : dictionary
        filename  : name of the file
        
    Returns
        void
    """
        
    with open(filename, "w") as file:
        json.dump(dct, file)
        

def read_dict_from_file(filename):
    """
    This function reads a dictionary
    from an external JSON file
        
    Arguments
        filename : name of the file
    
    Returns
        dct : dictionary with the contents of 'filename'
    """

    with open(filename, "r") as file:
        dct = json.loads(file.read())

    return dct


def create_inv_idx(corpus, vocab): 
    """
    This functions creates an inverted index list
    given a corpus of documents and a vocabulary
    
    Arguments
        corpus  : pandas df column or list-like
        vocab   : dictionary of all the words in the corpus
    
    Returns
        inv_idx : dictionary with the words as referenced in 'vocab' as keys 
                  and the lists of the documents each word is in as values       
    """
    
    inv_idx = {}
    
    for idx, word in zip(vocab.values(), vocab.keys()):
        inv_idx[idx] = [str(doc_id) for doc_id, doc in enumerate(corpus) if word in doc]
    
    return inv_idx


def parse_query(query, vocab, stemmer):
    """
    This functions converts the list of words
    input by the user into the list of the IDs
    the words are saved as in the vocabulary
    
    Arguments
        query : list of words
        vocab : vocabulary of words with the words as keys
                and their IDs as values
    Returns
        list of the IDs of the words in the query
    """
    
    parsed_query = []
    
    for word in query:
        try:
            parsed_query.append(vocab[stemmer.stem(word)])
        except KeyError:
            print(f"The term '{word}' wasn't found anywhere!")
    
    return parsed_query


def get_results(query, inv_idx):
    """
    This functions finds the documents all the words
    in the query are in.
    
    It finds them in four steps:
    1. retrieves the list of docs each word is in from the inverted index
    2. converts that list into a set
    3. creates a list of all these sets (one for each word)
    4. intersects all those sets into a single set
       
    Arguments
        query : list of words as parsed by 'parse_query'
        
    Returns
        set with the documents that contain all the words in the query
    """
    
    return set.intersection(*[set(inv_idx[str(q)]) for q in query])


def get_df_entries(df, results,
                   url_file = "../shared_stuff/url_list.txt", 
                   simil = None):
    """
    This function filters the dataset so it only shows
    the rows which match the results, and adds a new column
    with the URL for the anime of each row.
    
    Arguments
        df       : pandas dataframe
        results  : set with the row indices to be filtered out
        url_file : external file with the URLs for each of the rows in df
        simil    : dictionary with the similarity scores
    
    Returns
        df : filtered pandas dataframe
    """
    
    if not results:
        print("No results!")
        return pd.DataFrame()
    
    with open(url_file, 'r') as file:
        url_list = file.read().split("\n")

    df = df.iloc[[*results]]
    df = df[["title", "synopsis"]]
    df = df.rename(columns = {"title": "animeTitle", 
                              "synopsis": "animeDescription"})
    
    df['animeUrl'] = itemgetter(*results)(url_list)
    
    #in case we need a colum for Similarity
    if simil is not None: 
        df["Similarity"] = itemgetter(*results)(simil)
        df = df.sort_values(by = ['Similarity'], ascending = False)

    return df


def create_inv_idx2(corpus, vocab):
    
    tf = {}  
    
    #creating nested dictionary tf[word_idx][doc_num] = tf = freq of the word in this document/ quantity of all words in the doc 
    for word in vocab:      
        tf[vocab[word]]={}  
        
    for doc_num, doc in enumerate(corpus):
        l = len(doc)
        
        for word in doc:           
            if doc_num in tf[vocab[word]]:
                tf[vocab[word]][doc_num] += 1/l #dividing by l - to obtain tf score              
            else:
                tf[vocab[word]][doc_num] = 1/l   
                
    idf = {i: np.log(len(corpus)/len(tf[i])) for i in tf}    #idf
    
    #from nested dictionary to dict of tuples and tfidf = tf*idf
    tfidf = {k:list((d, (t*(idf[k]))) for d, t in v.items()) for (k, v) in tf.items()}
    
    return tfidf, idf 


def tfidf_query(corpus, query, inv_idx, idf):
    """
    This functions receives query and outputs tfidfs for words in this query
    
    Arguments
        corpus
        query : list of words
        inv_idx 
        idf
    Returns 
        tfidf_q, tfidf_docs - tfidf for query and for documents,
        tfidf_q - array, ith elemnt tfidf for ith word in query in query
        tfidf_docs["doc_number"] - array, ith elemnt tfidf for ith ford in query in doc_number
        
    """
    #tfidf indexes of words in query for all documents, in format of nested dict
    tfidf_d = {q: dict((i, v) for (i, v) in inv_idx[str(q)]) for q in query} 
    docs = set.intersection(*[set(i for (i, v) in inv_idx[str(q)]) for q in query]) #list of docs that have all words from query
    idf = {q: idf[str(q)] for q in query} #idf for words from query
    #let's count tfidf for query
    l = len(query)
    tf_q ={}
    for word in query:
        if word in tf_q:
            tf_q[word] += 1/l #dividing by l - to obtain tf score
        else:
            tf_q[word] = 1/l   
    tfidf_q = [tf_q[i]*idf[i] for i in tf_q]  #tfidf for query, array
    
    #creating tfidf for words in query for each doc that has all words from query
    
    tfidf_docs = {d : [0 for i in tf_q] for d in docs} #empty dict of arrays 
    for d in docs:
        for i, w in enumerate(tf_q):
            tfidf_docs[d][i] = tfidf_d[w][d]
            
    return tfidf_q, tfidf_docs

def cosine_similiarity(q, d):
    '''
    This function counts cosine similiarity between two vectors q and d
    '''
    return (sum([q[i]*d[i] for i in range(len(q))]) / math.sqrt(sum(qi * qi for qi in q) * sum(di * di for di in d)))
