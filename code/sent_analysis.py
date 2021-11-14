import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize


def filter_by_length(lst, length):
    """
    This function removes from a list of strings
    all those elements which are shorter than or
    as long as the specified length
    
    Arguments
        lst    : a list of strings
        length : (int) min length of the strings to keep
        
    Returns
        filtered list
    """
    
    return list(filter(lambda x: len(str(x)) > length, lst))


def norm_col(lst, new_min = 0, new_max = 1):
    """
    This function normalizes a list of numbers 
    so its min value is 0 and its max value is 1
    
    Arguments:
        lst     : column of a pandas dataframe or list-like
        new_min : (float)
        new_max : (float)
    Returns:
        (numpy array) normalized lst
    """
    
    lst_min = np.min(lst)
    lst_max = np.max(lst)
    
    return new_min + (new_max - new_min) * (np.array(lst) - lst_min) / (lst_max - lst_min)


def compound_score(text, sia):
    """
    This function computes VADER's compound score
    of some text
    
    Arguments:
        text : (string)
        sia: nltk.SentimentIntensityAnalyzer() object
    Returns:
        float between -1 and 1
    """
        
    return sia.polarity_scores(text)['compound']


def score_of_review(review, sia):
    """
    This function computes the mean compound score
    for a review, by averaging the scores for each sentence
    
    Arguments:
        review : (string)
        sia    : nltk.SentimentIntensityAnalyzer() object
    Returns:
        float between -1 and 1
    """
    
    return np.mean([compound_score(sentence, sia) 
                    for sentence in sent_tokenize(review) if sentence])


def score_of_anime(reviews, sia):
    """
    This function computes the mean compound score
    for an anime, by averaging the scores for each review
    
    Arguments:
        reviews : list of strings
        sia     : nltk.SentimentIntensityAnalyzer() object
    Returns:
        float between -1 and 1
    """
    
    return np.mean([score_of_review(review, sia) 
                    for review in reviews])


def sent_of_anime(score):
    """
    This function sets the thresholds to classify
    some text as being "positive", "negative", or
    "neutral"
    
    Arguments:
        score : (float)
    Returns:
        (string)
    """
        
    if score >= 0.2:
        return "Positive"
    elif score <= -0.2:
        return "Negative"
    else:
        return "Neutral"
    

def sent_pie_chart(plt, sent, text_fontsize = 15):
    """
    This function creates a matplotlib pie chart
    
    Arguments
        plt  : matplotlib.pyplot plot
        sent : pandas dataframe column with
               "Positive", "Negative" or "Neutral"
    
    Returns
        updated plt object
    """
    
    # Code to set custom colors inspired by this
    # https://stackoverflow.com/questions/35206282/assign-specific-colours-to-data-in-matplotlib-pie-chart
    
    labels = [s for s in sent.value_counts().index]
    
    colors = {"Positive": "greenyellow",
              "Neutral": "skyblue",
              "Negative": "crimson"}
    
    plt.pie(sent.value_counts(), 
            labels = labels,
            autopct = '%.0f%%',
            pctdistance = 0.7,
            startangle = 90,
            textprops = {'fontsize': text_fontsize},
            colors = [colors[sent] for sent in labels])
      
    return plt


def sent_multiple_pie_charts(df, plt, axes, title_size = 20):
    """
    This function creates a matplotlib plot
    with multiple pie charts of the sentiment, 
    one for each of the anime types
    
    Arguments
        df   : pandas dataframe
        plt  : matplotlib.pyplot plot
        axes : plt subplots
        title_size : (int) size of the title of each subplot
    
    Returns
        updated plt object
    """
    
    anime_types = df_sent.groupby('type').size().keys()
    
    for ax, anime_type in zip(axes.flatten(), anime_types):
        
        ax.title.set_text(anime_type)
        ax.title.set_size(title_size)
        
        sent_pie_chart(ax, df[df['type'] == anime_type]['sentiment'])
        
    return plt