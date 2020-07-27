
import requests
from bs4 import BeautifulSoup
import pyspark as ps
import numpy as np
import time

import os

assert os.sys.argv[1] == '--output' and len(os.sys.argv) == 3, 'requires a specified output folder with --output parameter'

# this shared variable is not taken advantage of by the distributed
# Spark nodes, but is useful for Python-level scripts
response_cache = {}

def http_get(url):
    if response := response_cache.get(url):
        return response
    else:
        response = requests.request(url=url, method="GET")
        counties_list_html = response.content
        response_cache[url] = counties_list_html
        
        return response_cache[url]


## -- WIKIPEDIA UTILITIES --

def wikipedia_export_get(title):
    xml = http_get("https://en.wikipedia.org/wiki/Special:Export/" + title)
    
    if b'<redirect title' in xml:
        return wikipedia_export_get(title=BeautifulSoup(xml).select('redirect')[0]['title'])
    else:
        return xml

def wikipedia_standard_url(title):
    return "https://en.wikipedia.org/wiki/" + title

# def wikipedia_standard_url_encode(title):
#     import urllib.parse
#     return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title)

def wikipedia_counties_titles():
    soup = BeautifulSoup(http_get(counties_list_url))
    
    rows = soup.select('.wikitable.sortable tbody tr')
    anchors = sum([row.select('td a')[:1] for row in rows], [])

    urls = [a['href'][len('/wiki/'):] for a in anchors]
    
    return urls
    
def wikipedia_communities_subheadings(text):
    import re

    regex = r"(^==\s?Communities\s?==)(.+?)(^==[^=].+?[^=]==)"
    post_communities = re.findall(regex, text, re.MULTILINE + re.DOTALL)
    
    if len(post_communities) == 0:
        return []

    post_communities = post_communities[0]
    
    regex = r"===(.+)==="
    res = [result.strip() for result in re.findall(regex, post_communities[1])]

    return res

def wikipedia_communities_extract(text):
    import re

    regex = r"(^==\s?Communities\s?==)(.+?)(^==[^=].+?[^=]==)"
    post_communities = re.findall(regex, text, re.MULTILINE + re.DOTALL)
    
    regex = r"(^==\s?Municipalities\s?==)(.+?)(^==[^=].+?[^=]==)"
    municipalities = re.findall(regex, text, re.MULTILINE + re.DOTALL)
    
    regex = r"(^==\s?Cities and communities\s?==)(.+?)(^==[^=].+?[^=]==)"
    cities_and_communities = re.findall(regex, text, re.MULTILINE + re.DOTALL)
    
    regex = r"(^==\s?Community\s?==)(.+?)(^==[^=].+?[^=]==)"
    community = re.findall(regex, text, re.MULTILINE + re.DOTALL)
    
    types = []
    if len(post_communities) > 0:
        types.append("Communities")
        
    if len(municipalities) > 0:
        types.append("Municipalities")
        if len(municipalities) > len(post_communities):
            post_communities = municipalities

    if len(cities_and_communities) > 0:
        types.append("Cities and communities")
        if len(cities_and_communities) > len(post_communities):
            post_communities = cities_and_communities

    if len(community) > 0:
        types.append("Community")
        if len(community) > len(post_communities):
            post_communities = community
    
    if len(post_communities) == 0:
        return []

    post_communities = post_communities[0]
    
    regex = r"===(.+)==="
    communities_subheadings = [result.strip() for result in re.findall(regex, post_communities[1])]
    
    ## --
    
    regex = r"\*\s*\[\[(.+?),(.+?)\|(.+?)\]\]"
    communities = re.findall(regex, post_communities[1])
    
    regex = r"\*\s*\[\[(.+?)\|(.+?)\]\]"
    communities_all = re.findall(regex, post_communities[1])
    
    regex = r"\*\s*\[\[([^|]+?)\]\]"
    communities_untitled = re.findall(regex, post_communities[1])
        
    a = set([c[2] for c in communities])
    b = set([c[1] for c in communities_all])
    difference = b.difference(a).union(a.difference(b))
    
    return communities_subheadings, [c[0] for c in communities_all], difference, communities_untitled, types


# ---
# Spark setup
spark = (ps.sql.SparkSession
         .builder
         .master('local[8]')
         .appName('lecture')
         .getOrCreate())

sc = spark.sparkContext

counties_list_url = "https://en.wikipedia.org/wiki/List_of_United_States_counties_and_county_equivalents"


if not os.path.exists(os.sys.argv[2]):
    os.makedirs(os.sys.argv[2])

## -- parse the communities from each county --

if not os.path.exists(f'{os.sys.argv[2]}/counties_communities_all.txt'):
    titles_all = wikipedia_counties_titles()

    counties_export_text = (sc.parallelize(titles_all)
                            .map(wikipedia_export_get)
                            .map(lambda export: BeautifulSoup(export, 'html.parser').select('text')[0].getText())
                            .cache())

    communities_all = (counties_export_text.map(wikipedia_communities_extract)
                                        .filter(lambda x: x != [])
                                        .map(lambda x: x[1]))

    communities_all = list(communities_all.map(set).reduce(set.union))

    with open(f'{os.sys.argv[2]}/counties_communities_all.txt', 'w') as file:
        file.write("\n".join(communities_all))

print("Done.")