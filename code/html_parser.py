'''

    This file contains all the function usefull to parse the just downloaded html pages into tsv files
    Containing all the relevant information that are:
        * Anime Name
        * Anime Type
        * Number of episode
        * Release and End Dates of anime
        * Number of members
        * Score
        * Users
        * Rank
        * Popularity
        * Synopsis
        * Related Anime
        * Characters
        * Voices
        * Staff


'''


from bs4 import BeautifulSoup
import bs4
import os
from datetime import datetime

# ---------------------------------------------------------------------------- #
#                                  HTML PARSER                                 #
# ---------------------------------------------------------------------------- #

# ----------------------------- Support functions ---------------------------- #

def get_soup(fname):
    '''
        Given the path of a html file this function returns a BeautifulSoup object paserd with the html.parser
        with the content of the file
    ''' 

    f = open(fname, 'r')
    soup = BeautifulSoup(f.read(), 'html.parser')
    f.close()
    return soup


def get_date(str_date):
    '''
        Given a string in the format:
            -Mon dd, year or 
            -Mon year
            -year
        It returns the corresponding datetime object
    '''
    if str_date == 'Not available': # Posssible dirty data...
        return None
    try:
        end = datetime.strptime(str_date, '%b %d, %Y')
    except ValueError:
        try:
            end = datetime.strptime(str_date, '%b %Y')
        except ValueError:
            end = datetime.strptime(str_date, '%Y')
    return end

# -------------------------- Web scraping functions -------------------------- #

def get_title(soup, ret):
    '''
        Given a BeautifulSoup object and a dictionary it adds to the dictionary the title of the page
    '''
    title = soup.find('title').contents[0].strip()
    if(title.endswith(" - MyAnimeList.net")):
        title = title[:-18]
    ret['title'] = title


def get_left_attributes(soup, ret):
    ''' 
        Given an html page parsed with BeautifulSoup and a dictionary, the function retrieved and add to it the folluwing fields:
            -episodes: Number of episodes of the anime
            -start_date: date of start airing
            -end_date: date of end airing if exists
            -score: score given by the users
            -users: users that scores it
            -rank: ranking of the anime
            -members: number of members
            -popularity: popularity of the anime
            -type: type of the anime
    '''
    divs = soup.find_all('div', {"class": "spaceit_pad"})
    
    # Taking the interesting tag
    from_interest = ['Episodes:','Aired:','Members:','Ranked:','Popularity:']
    for div in divs:
        content = div.contents
        tag = content[1].contents[0]

        if tag=='Score:': # The score tag has a special threatment given its structure
            
            # Retrieving the score
            attr= {'itemprop':'ratingValue'}
            score = div.find('span', attr)
            ret['score'] = float(score.contents[0]) if score is not None else None
            
            # Retrieving the users
            attr = {'itemprop':'ratingCount'}
            users = div.find('span', attr)
            ret['users'] = int(users.contents[0]) if users is not None else None
        
        # Same for score, with type we've more check
        elif tag == 'Type:':
            content[1:] = [el for el in content[1:] if el!='\n']

            # The type can be a wrapped string
            if type(content[-1])==bs4.element.NavigableString:
                ret['type'] = content[-1].strip()
            else: # or a link
                ret['type'] = content[-1].contents[0]
        
        # For the other tags...
        elif tag in from_interest:
            val = content[2].strip()
            if val.startswith('#'): # number as ranking or popularity starts with #
                val=val[1:]
                ret[tag[:-1].lower()] = int(val)
            elif tag == 'Aired:': # here we need to play with the dates
                if 'to' in val:
                    start, end = val.split('to')
                    start = start.strip()
                    start = get_date(start)
                    
                    if end is not None:    
                        if '?' not in end:
                            end = get_date(end.strip())
                        else:
                            end=None
                    val = f'start: {start}, end: {end}'
                    ret['start_date'] = start
                    ret['end_date'] = end
                else:
                    start=val.strip()
                    start = get_date(start)
                    ret['start_date'] = start
                    ret['end_date'] = None
            else:
                val = val.replace(',','') # the long numbers are comma separated
                
                ret[tag[:-1].lower()] = int(val) if val.isnumeric() else None #Sometimes val can be 'unknown' (i.e. see OnePiece)


def get_synopsis(soup, ret):
    ''' 
        This function adds the synopsis of the BeautifulSoup page to the ret dict
    '''
    synopsis = soup.find('p', {'itemprop':'description'}).contents[0]
    ret['synopsis'] = synopsis


def get_related_animes(soup, ret):
    ''' 
        This function adds a list of unique names on which the anime is related
    '''
    # For the related anime there's an html table dedicated
    related_animes_table = soup.find('table', {'class': 'anime_detail_related_anime'})
    if related_animes_table is None:
        ret['related_anime'] = None
        return
    animes = set()
    for a in related_animes_table.find_all('a'):
        a_cont = a.contents
        if len(a_cont) > 0:
            animes.add(a_cont[0])

    ret['related_anime'] = list(animes)


def get_staff(div, ret):
    '''
        Same as for anime, adds a list of strings containg the staff names.
        This time it's not required the entire BeautifulSoup object but only the div element
        containing the staff info 
    '''
    i = 1
    staff = []
    for td in div.find_all('td', {'class':'borderClass'}):
        if (i)==0:
            #print(td)
            a, small = td.find_all(['small', 'a'])
            staff.append([a.contents[0], small.contents[0].split(',')])

        i = (i+1)%2
    ret['staff'] = staff


def get_characters_voices(div, ret):
    ''' 
        As for staff here is required the div containing the tables of the characters and related voices.
        The function will add to the given dictionary the two lists
    '''
    ret['characters'] = []
    ret['voices'] = []
    
    # The date of interest are wrapped into table rows (tr)
    for tr in div.find_all('tr'):
        tds = tr.find_all('td', {'class':'borderClass'})
        if len(tds) != 3: # the rows of interest have three columns
            continue
        
        # we need only the second and the last
        ch = tds[1]
        vc = tds[2]
        ch_a = ch.find('a')
        vc_a = vc.find('a')
        if ch_a is not None:
            ret['characters'].append(ch_a.contents[0])
        if vc_a is not None:
            ret['voices'].append(vc_a.contents[0])

# --------------------------- Putting all togheter --------------------------- #

def get_total_info(fname):
    ''' 
        Putting all togheter here we take a fname containing an html.
        So this function returns a dictionary containing all the info of interest with the functions above
    '''
    ret = dict()
    soup = get_soup(fname)
    get_title(soup, ret)
    get_left_attributes(soup, ret)
    get_synopsis(soup, ret)
    get_related_animes(soup, ret)
    
    # Retrieving the divs for the staff and the actor and characters
    divs = soup.find_all('div', {'class':"detail-characters-list clearfix"})
    if len(divs) == 0:
        ret['characters'] = []
        ret['voices'] = []
        ret['staff'] = []
    elif len(divs) != 2:
        if divs[0].find('h3', {'class':"h3_characters_voice_actors"}) is not None:
            #print('only ch_voices')
            get_characters_voices(divs[0], ret)
            ret['staff'] = []
        else:
            #print('only staff')
            get_staff(divs[0], ret)
            ret['characters'] = []
            ret['voices'] = []
    else:
        get_characters_voices(divs[0], ret)
        get_staff(divs[1], ret)
    return ret

# -------------------------- Employing the functions ------------------------- #

def get_total_info_from_idx(idx, base_dir=os.path.join('..', 'data', 'html_pages')):
    ''' 
        Given the index of an anime this function returns the dictionary with the information about that
    '''

    fname = f"article_{str(idx).zfill(5)}.html"
    return get_total_info(os.path.join(base_dir, fname))


def get_tsv_from_idx(idx, base_dir=os.path.join('..', 'data', 'html_pages')):
    ''' 
        Given an index and a base_dir this function retrieves the info of the i-th anime in tsv format
        using its file in the base_dir directory
    '''
    # Fields of the tsv
    fields = ['title', 'type', 'episodes', 'start_date', 'end_date', 'score', 'users', 'ranked', 'popularity', 'members', 'synopsis', 'related_anime', 'characters', 'voices', 'staff']
    head = '\t'.join(fields)
    ret = '' 
    
    # Getting the dictionary info
    info_dict = get_total_info_from_idx(idx, base_dir)
    for f in fields:
        val = str(info_dict[f])
        if val is None:
            val = ''
        elif type(val)==list and len(val)==0:
            val= ''
        ret+= val+'\t'
    return head, ret[:-1]


def save_tsv_info(start, end, src_dir='../data/html_pages', dst_dir='../data/tsv_files'):
    '''
        This function retrieves the info from the files in the src_dir directory and saves the relative tsv in the dst_dir.
        You can pass a start, end indexes from which start and stop (remember that last is not included).

        These info in tsv format will be stored in a total_pages.tsv too containing the info for all the pages.
    '''
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)
    
    fields = ['title', 'type', 'episodes', 'start_date', 'end_date', 'score', 'users', 'ranked', 'popularity', 'members', 'synopsis', 'related_anime', 'characters', 'voices', 'staff']
    
    # Creating the total tsv 
    total_tsv = os.path.join(dst_dir, 'total_pages.tsv')
    if not os.path.exists(total_tsv):
        with open(total_tsv, 'x') as out:
            out.write('\t'.join(fields)+'\n')

    # Iterating over the desired indices
    for idx in range(start, end):
        # Getting the tsv data
        tsv_h, tsv_c = get_tsv_from_idx(idx, src_dir)
        out_name = f"article_{str(idx).zfill(5)}.tsv"
        
        # Creating the output file
        with open(os.path.join(dst_dir, out_name), 'w') as f:
            f.write(tsv_h + '\n' + tsv_c)
        
        # adding a line to the total
        with open(os.path.join(total_tsv), 'a') as f:
            f.write('\n'+tsv_c)     
        print(f"idx: {idx} DONE!")   