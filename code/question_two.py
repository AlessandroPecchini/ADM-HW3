import string
import json
from operator import itemgetter

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer

stemmer = SnowballStemmer('english')

def str_to_list(s):
    """
    This functions returns a list
    with each of the characters of the input string
    
    Arguments
        s : string
        
    Returns
        (list)
    """
    
    return [char for char in s]

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
    
    punct = str_to_list(string.punctuation)
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
    
    text = str(text)
    
    tokens = word_tokenize(text)
        
    return [stemmer.stem(w) for w in tokens 
            if w not in bad_words() and not has_digits(w)]


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
        inv_idx[idx] = [doc_id for doc_id, doc in enumerate(corpus) if word in doc]
    
    return inv_idx

def parse_query(query, vocab):
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
    
    It finds them in three steps:
    1. creates a list of docs each word is in from the inverted index
    2. converts that list into a set
    3. intersects all those sets into a single set
       
    Arguments
        query : list of words as parsed by 'parse_query'
        
    Returns
        set with the documents that contain all the words in the query
    """
    
    return set.intersection(*[set(inv_idx[str(q)]) for q in query])


def get_df_entries(df, results,
                   url_file = "../shared_stuff/url_list.txt"):
    """
    This function filters the dataset so it only shows
    the rows which match the results, and adds a new column
    with the URL for the anime of each row.
    
    Arguments
        df       : pandas dataframe
        results  : set with the row indices to be filtered out
        url_file : external file with the URLs for each of the rows in df
    
    Returns
        df : filtered pandas dataframe
    """
    
    if not results:
        print("No results!")
        return
    
    with open(url_file, 'r') as file:
        url_list = file.read().split("\n")

    df = df.iloc[[*results]]
    df = df[["title", "synopsis"]]
    df = df.rename(columns = {"title": "animeTitle", 
                              "synopsis": "animeDescription"})
    
    df['animeUrl'] = itemgetter(*results)(url_list)
    
    return df