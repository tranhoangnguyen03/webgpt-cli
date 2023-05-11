# webgpt is a command line interface tool that uses the GPT-3 API to generate summaries from the web and provides a link to the source

import re
import sys
import argparse
import openai
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import warnings
import os
import logging

logger = logging.getLogger(__name__)

with open('blacklist') as f:
    black_list = f.read().splitlines()

# supress warnings
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description='Use GPT-3 with multi-shot prompting to generate summaries from the web.')
parser.add_argument('query', type=str, help='the query to generate text from')
parser.add_argument('-m', '--model', type=str, default='text-davinci-003', help='the GPT-3 model to use')
parser.add_argument('-t', '--temperature', type=float, default=0.3, help='the sampling temperature')
parser.add_argument('-max', '--max-tokens', type=int, default=2000, help='the maximum number of tokens to generate')
parser.add_argument('-n', '--num-results', type=int, default=3, help='the number of results to return')

# Parse the arguments
args = parser.parse_args()

query = args.query

# Using this class to supress the output of the search function
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

# This function searches google for the query and returns the top 3 links
def search(query):

  hl =  "en"
  gl = "us"
  key = "ccec77fdc3ce624ad18a680eb61ff4d62f5cada1246e3f03eba613c76bc63944"

  params = {
    "q": query,
    "hl": hl,
    "gl": gl,
    "api_key": key
  }

  search = GoogleSearch(params)
  results = search.get_dict()

  links = []
  logger.info(results)
  for i in results["organic_results"]:
      links.append(i['link'])
  
  return links

# This function scrapes the text from the link
def scrape(url):

    # url = "https://en.wikipedia.org/wiki/Coffee"

    r1 = requests.get(url)
    r1.status_code
    coverpage = r1.content
    soup = BeautifulSoup(coverpage, "lxml")
    content = soup.find("body").find_all('p')

    x = ''
    for i in content:
        x = x + i.getText().replace('\n', '')

    x = re.sub(r'==.*?==+', '', x)
    
    return x

def get_topic(query):
    prompt = ''.join([
        "Which artist painted the Mona Lisa?	Art",
        "Who wrote the novel To Kill a Mockingbird?	Literature",
        "What is the formula for calculating the area of a circle?	Mathematics",
        "Who invented the telephone?	History/Inventions",
        "What is the capital of Spain?	Geography",
        "What is the atomic number of oxygen?	Chemistry",
        "Who directed the film Titanic?	Film",
        "Who composed the famous opera The Barber of Seville?	Music",
        "What is the process of photosynthesis?	Biology",
        "What is the name of the first man to walk on the moon?	History/Space Exploration",
        "Only output the direct answer in as few words as possible:" 
        f"The topic for this question {query} is"
        ])

    string = gpt(prompt)
    # pattern = r"^Topic:\s(.*)$"
    # match = re.search(pattern, string, re.MULTILINE)
    # if match:
    #     topic = match.group(1)
    #     return topic
    # else:
    #     logger.error(f'No topic found {string}')
    #     return None
    logger.info(string)
    return string
     

def get_gpt_answer(query:str):
    topic = get_topic(query) or 'general'
    context = ' '.join([
        f"You are a distinguished professor in `{topic}` with well over ten years teaching.",
        "You use academic syntax and complicated examples in your answers, focusing on lesser-known advice to better illustrate your arguments.",
        "Your language should be sophisticated but not overly complex.",
        "If you do not know the answer to a question, do not make information up",
        "Your answers should be in the form of a conversational series of paragraphs.",
        "Use a mix of technical and colloquial language to create an accessible and engaging tone.",
        "Please answer the question below:"
    ])

    prompt = '\n\n'.join([
        context,
        query,
    ])
    return {'summary':gpt(prompt), 
            'link':'Chat GPT',
            'source':'Chat GPT'
        }


# This function uses the GPT-3 API to generate a summary
def gpt(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    r = openai.Completion.create(model=args.model, prompt=prompt, temperature=args.temperature, max_tokens=args.max_tokens)
    response = r.choices[0]['text']

    return response

with HiddenPrints():
    # This function combines the search, scrape and gpt functions
    def process(query):
    
        links = search(query)
        results = [get_gpt_answer(query)]

        for i in links[:args.num_results]:

            if i not in black_list:

                txt = scrape(i)[:2000]
                if len(txt) < 500:
                    continue

                prompt = """Given the following question:'"""+query+"""'

                Extract the text from the following content strictly relevant to the question and summarize in detail:

                '"""+txt+"""'

                Extracted summarized content:"""

                a = {
                    'query': query,
                    'link': i,
                    'text': txt,
                    'summary': gpt(prompt).strip()
                }
                
                results.append(a)
        return results

    data = process(args.query)

# This function prints the results in a nice format
def output(query, data):
    print('')
    print('\033[1m' + 'Query:' + '\033[0m', "\x1B[3m" + query + "\x1B[0m")
    print('\033[1m' + 'Results: ' + '\033[0m')

    for i in data:
        print('')
        print('')
        # print('\033[1m' + '' + '\033[0m',)
        print(" - '"+i['summary'].strip()+"'")
        print('['+ '\033[1m' + 'source:' + '\033[0m', '\033[34m' + "\x1B[3m" + i['link'] + "\x1B[0m" + '\033[00m' +']')
        print('')


output(args.query, data)