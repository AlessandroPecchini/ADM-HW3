import requests
import os
from bs4 import BeautifulSoup
import argparse
from time import *
from random import *

def download_pages(f_path, out_path='', base=0, to=-1):
    number=base
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    with open(f_path) as file:
    #the line will be the url
        lines = file.readlines()
    to = to if to >=0 else len(lines)
    for idx in range(to-base):
        url = lines[idx+base]
        response=requests.get(url, headers=headers)
        if response.status_code==403:
            sleep_time =  randint(20,40)
            print(f"An error occoured, I'll sleep for {sleep_time} seconds")
            sleep(sleep_time)
            continue

        error_btn = "<button type=\"submit\" class=\"g-recaptcha\" data-sitekey=\"6Ld_1aIZAAAAAF6bNdR67ICKIaeXLKlbhE7t2Qz4\" data-callback='onSubmit' data-action='submit'>Submit</button>"
        print(f"request: {number} response code: {response.status_code} error button in text?: {error_btn in response.text}")
        #save file as htlm
        name=('article_%d.html' % (number))
        html_file = open(os.path.join(out_path,name),"w")
        html_file.write(response.text)
        html_file.close()
        number+=1


def parse_args():
    '''
        Questo metodo parsa gli argomenti della linea di comando.
    '''

    # Instantiate the parser
    parser = argparse.ArgumentParser(description="This script will download the html pages in the url of the f_path given in input",
                                    usage="\n -fp F_PATH [-h] [--out OUT_PATH] [--base FROM] [--to TO]")
        
    
    parser.add_argument('-fp', type=str, required=True,
                        help=\
                            f"The path where txt file containing the urls is located")

    # Switch
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
    args = parse_args()

    base = args.base if args.base is not None else 0
    to = args.to if args.to is not None else -1
    
    if to>0 and base>to:
        raise ValueError('The base and to index must be in crescent order, your base: {args.base}, your to: {args.to}')

    if args.out is not None:
        if not os.path.exists(args.out):
            os.mkdir(args.out)
    out = args.out if args.out is not None else ''

    if args.fp is not None:
        if not os.path.exists(args.fp):
            raise ValueError(f"the file {args.fp} doesn't exist")
    else:
        raise ValueError("You need to provide a valid path in order to use this tool")
    
    download_pages(args.fp, out_path=out, base=base, to=to)


# pippo pluto

main()