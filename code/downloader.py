import requests
import os
import argparse
from time import *
from random import *

def download_pages(f_path, out_path='', base=0, to=-1):
    '''
        This funtion dowloads the html pages going from 'base' to 'to'-1 that corresponds to the url of the file located in fpath.
        
        The structure of the url file has to be the following:
            URL1\n
            URL2\n
            ...
        
        All these pages will be stored in files named article_i.html where 'i' means that it's the i-th url.
        You can choose to save these pages in specific location using the argument out_path

        The programm will download each page in the file, but you can choose the range playing with 'base' and 'to'

        Arguments
        _________

            f_path: str
                The path corresponding to the file containing the urls.
            out_path='.' : str
                The directory where the output files will be stored
            base=0: int
                The index of the url from which start the download
            end=len(url file): int
                The index of the file on which stop
    '''

    number=base
    # to make requests in a safer way
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    
    # Getting all the urls
    with open(f_path) as file:
        lines = file.readlines()

    to = min(to, len(lines)) if to >=0 else len(lines)

    idx = base
    while idx<to:

        url = lines[idx]
        response=requests.get(url, headers=headers)

        # Ops.. We've done too much requests, let's sleep for a while hoping to be free to ask again
        if response.status_code==403:
            sleep_time =  randint(5,25)
            print(f"An error occoured, I'll sleep for {sleep_time} seconds")
            sleep(sleep_time)
            continue
        
        error_btn = "<button type=\"submit\" class=\"g-recaptcha\" data-sitekey=\"6Ld_1aIZAAAAAF6bNdR67ICKIaeXLKlbhE7t2Qz4\" data-callback='onSubmit' data-action='submit'>Submit</button>"
        
        # Some output log, just to be up to date
        print(f"request: {number} response code: {response.status_code} error button in text?: {error_btn in response.text}")
        
        
        # Everithing is going well, let's save
        name=('article_%d.html' % (number))
        html_file = open(os.path.join(out_path,name),"w")
        html_file.write(response.text)
        html_file.close()
        number+=1
        idx+=1


def parse_args():
    '''
        This methods parses the arguments from the command line
    '''


    # Instantiating the parser 

    parser = argparse.ArgumentParser(description="This script will download the html pages in the url of the f_path given in input",
                                    usage="\n -fp F_PATH [-h] [--out OUT_PATH] [--base FROM] [--to TO]")
    
    # Setting up the arguments

    parser.add_argument('-fp', type=str, required=True,
                        help=\
                            f"The path where txt file containing the urls is located")

    parser.add_argument('--out', type=str,
                        help="The directory where the output files will be stored")

    parser.add_argument('--base', type=int,
                        help="The index of the url from wich to start")

    parser.add_argument('--to', type=int,
                        help='the index of the url on wich to stop (excluded)')

    args = parser.parse_args()

    if args.fp is None:
        raise ValueError("You must pass a path to the document to retrieve the urls")
    return args
    

def main():
    
    # Retrieving the arguments from the comman line
    args = parse_args()

    # Giving some sense to the 'base' and 'to' indices
    base = args.base if args.base is not None else 0
    to = args.to if args.to is not None else -1
    
    if to>0 and base>to:
        raise ValueError('The base and to index must be in crescent order, your base: {args.base}, your to: {args.to}')

    # Fixing potential directory issues
    if args.out is not None:
        if not os.path.exists(args.out):
            os.mkdir(args.out)
    out = args.out if args.out is not None else ''

    if args.fp is not None:
        if not os.path.exists(args.fp):
            raise ValueError(f"the file {args.fp} doesn't exist")
    else:
        raise ValueError("You need to provide a valid path in order to use this tool")
    
    # Actually start the program
    download_pages(args.fp, out_path=out, base=base, to=to)

main()