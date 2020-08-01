
import requests
from bs4 import BeautifulSoup
import pyspark as ps
import numpy as np
import time

import os

assert os.sys.argv[1] == '--directory' and len(os.sys.argv) == 3, 'requires a specified output folder with --directory parameter'
directory = os.sys.argv[2]

response_cache = {}

def http_get(url):
    if response := response_cache.get(url):
        return response
    else:
        response = requests.request(url=url, method="GET")
        counties_list_html = response.content
        response_cache[url] = counties_list_html
        
        return response_cache[url]

def wikipedia_export_get(title):
    xml = http_get("https://en.wikipedia.org/wiki/Special:Export/" + title)
    
    if b'<redirect title' in xml:
        return wikipedia_export_get(title=BeautifulSoup(xml).select('redirect')[0]['title'])
    else:
        return xml

def wikipedia_standard_url(title):
    return "https://en.wikipedia.org/wiki/" + title

def wikitable_extractor(column, table_index=0):
    return lambda soup: [a['href'][len('/wiki/'):] for a in soup.select(f'table.wikitable.sortable')[table_index].select(f'td:nth-child({column}) a[href^="/wiki/"]')]

def wikilist_extractor(table_index=0):
    return lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('ul')[table_index].select('li a[href^="/wiki/"]')]

parameters = [
    ( 'List_of_cities_and_towns_in_Alabama', wikitable_extractor(column=1)),
    (      'List_of_ghost_towns_in_Alabama', wikitable_extractor(column=1)),
    
    (            'List_of_cities_in_Alaska', wikitable_extractor(column=1)),
    
    ( 'List_of_cities_and_towns_in_Arizona', wikitable_extractor(column=1)),
    (      'List_of_ghost_towns_in_Arizona', wikitable_extractor(column=1)),
    
    ('List_of_cities_and_towns_in_Arkansas', wikitable_extractor(column=2)),
    (     'List_of_ghost_towns_in_Arkansas', wikitable_extractor(column=1)),
    
    ('List_of_cities_and_towns_in_California', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('table.wikitable.sortable th[scope="row"] a[href^="/wiki/"]')]),
    (     'List_of_ghost_towns_in_California', wikitable_extractor(column=1)),
    
        
    ('List_of_cities_and_towns_in_Colorado', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Colorado', wikitable_extractor(column=1)),
    
    (       'List_of_cities_in_Connecticut', wikitable_extractor(column=1)),
    (        'List_of_towns_in_Connecticut', wikitable_extractor(column=2)),
    (  'List_of_ghost_towns_in_Connecticut', wikilist_extractor()),
    
    (  'List_of_municipalities_in_Delaware', wikitable_extractor(column=2)),
    (     'List_of_ghost_towns_in_Delaware', wikilist_extractor()),

    (   'List_of_municipalities_in_Florida', wikitable_extractor(column=2)),
    (      'List_of_ghost_towns_in_Florida', wikitable_extractor(column=1)),
    
    ('List_of_municipalities_in_Georgia_(U.S._state)', wikitable_extractor(table_index=1, column=1)),
    ('List_of_ghost_towns_in_Georgia_(U.S._state)', wikilist_extractor()),
    
    (            'List_of_places_in_Hawaii', wikitable_extractor(column=2)),
    (       'List_of_ghost_towns_in_Hawaii', lambda soup: sum([wikilist_extractor(table_index=i)(soup) for i in range(1, 6)], [])),
    
    (             'List_of_cities_in_Idaho', wikitable_extractor(column=2)),
    (        'List_of_ghost_towns_in_Idaho', wikilist_extractor()),
    
    (  'List_of_municipalities_in_Illinois', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Illinois', wikilist_extractor()),
    
    (           'List_of_cities_in_Indiana', wikitable_extractor(column=2)),
    (            'List_of_towns_in_Indiana', wikitable_extractor(column=1)),
    (      'List_of_ghost_towns_in_Indiana', wikilist_extractor()),
    
    (              'List_of_cities_in_Iowa', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('table.wikitable.sortable th[scope="row"] a[href^="/wiki/"]')]),
    (         'List_of_ghost_towns_in_Iowa', wikilist_extractor()),
    
    (            'List_of_cities_in_Kansas', lambda soup: sum([wikilist_extractor(table_index=i)(soup) for i in range(5, 5+25)], [])), # alphabetical, missing 'X'
    (       'List_of_ghost_towns_in_Kansas', wikitable_extractor(column=1)),
    
    (          'List_of_cities_in_Kentucky', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Kentucky', wikilist_extractor()),
    
    ( 'List_of_municipalities_in_Louisiana', wikitable_extractor(column=1)),
    (    'List_of_ghost_towns_in_Louisiana', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('div')[2].select('ul li a[href^="/wiki/"]')[:-5] if '_Louisiana' in a['href']]),
    
    (             'List_of_cities_in_Maine', wikitable_extractor(column=2)),
    (              'List_of_towns_in_Maine', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select(f'table.Wikitable.sortable')[0].select(f'td:nth-child(1) a[href^="/wiki/"]')]),
    (        'List_of_ghost_towns_in_Maine', wikilist_extractor()),
    
    (  'List_of_municipalities_in_Maryland', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Maryland', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('ul a[href^="/wiki/"]') if 'ounty' not in a['href']][:12]),
    
    ('List_of_municipalities_in_Massachusetts', wikitable_extractor(column=1)),
    ('List_of_ghost_towns_in_Massachusetts', lambda soup: [title for title in wikilist_extractor()(soup) if 'Quabbin' not in title]),
    
    (  'List_of_municipalities_in_Michigan', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Michigan', wikilist_extractor(table_index=2)),
    
    (         'List_of_cities_in_Minnesota', wikitable_extractor(column=2)),
    (    'List_of_ghost_towns_in_Minnesota', wikilist_extractor()),
    
    ('List_of_municipalities_in_Mississippi', wikitable_extractor(column=1)),
    (   'List_of_ghost_towns_in_Mississippi', wikilist_extractor()),
    
    # (           'List_of_cities_in_Missouri', lambda soup: sum([wikilist_extractor(table_index=i)(soup) for i in range(2, 25)], []))
    (      'List_of_ghost_towns_in_Missouri', wikilist_extractor()),
    
    (  'List_of_cities_and_towns_in_Montana', wikitable_extractor(column=1)),
    (       'List_of_ghost_towns_in_Montana', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('ul a[href^="/wiki/"]:not([href*="County"])')[:73]]),
    
    (           'List_of_cities_in_Nebraska', lambda soup: sum([wikilist_extractor(table_index=i)(soup) for i in range(1, 1+23)], [])),
    (      'List_of_ghost_towns_in_Nebraska', wikilist_extractor()),
    
    (            'List_of_cities_in_Nevada', wikitable_extractor(column=1)),
    (       'List_of_ghost_towns_in_Nevada', wikitable_extractor(column=1)),
    
    ('List_of_cities_and_towns_in_New_Hampshire', wikitable_extractor(column=1)),
    ('List_of_ghost_towns_in_New_Hampshire', lambda soup: wikilist_extractor()(soup)[:5]),
    
    ('List_of_municipalities_in_New_Jersey', wikitable_extractor(column=2)),
    (  'Category:Ghost_towns_in_New_Jersey', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('li a')[:17]]),
    
    ('List_of_municipalities_in_New_Mexico', wikitable_extractor(column=1)),
    (   'List_of_ghost_towns_in_New_Mexico', wikitable_extractor(column=1)),
    
    (          'List_of_cities_in_New_York', wikitable_extractor(column=1)),
    ('Category:Ghost_towns_in_New_York_(state)', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('li a')[:10]]),
    
    ('List_of_municipalities_in_North_Carolina', lambda soup: [title for title in sum([wikilist_extractor(table_index=i)(soup) for i in range(2, 26)], []) if 'County' not in title]),
    ('List_of_ghost_towns_in_North_Carolina', wikilist_extractor()),
    
    # (       'List_of_cities_in_North_Dakota', wikitable_extractor(table_index=0, column=2)),
    (  'List_of_ghost_towns_in_North_Dakota', wikilist_extractor()),
    
    (               'List_of_cities_in_Ohio', wikitable_extractor(column=1)),
    (             'List_of_villages_in_Ohio', wikitable_extractor(column=1)),
    # (          'List_of_ghost_towns_in_Ohio', lambda soup: [title for title in wikilist_extractor()(soup) if '_County' not in title][1:]),
    
    ( 'List_of_cities_and_towns_in_Oklahoma', wikitable_extractor(table_index=1, column=2)),
    (      'List_of_ghost_towns_in_Oklahoma', wikitable_extractor(column=1)),
    
    (             'List_of_cities_in_Oregon', wikitable_extractor(column=2)),
    (        'List_of_ghost_towns_in_Oregon', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('table.wikitable.sortable th[scope="row"] a[href^="/wiki/"]')]),
    
    (       'List_of_cities_in_Pennsylvania', wikitable_extractor(column=1)),
    # (    'List_of_ghost_towns_in_Pennsylvania', '')

    ('List_of_municipalities_in_Rhode_Island', wikitable_extractor(column=1)),
    (  'Category:Ghost_towns_in_Rhode_Island', lambda soup: ['Hanton_City,_Rhode_Island']),
    
    ('List_of_cities_and_towns_in_South_Carolina', wikitable_extractor(column=1)),
    ( 'List_of_ghost_towns_in_South_Carolina', wikilist_extractor()),
    
    (        'List_of_cities_in_South_Dakota', wikitable_extractor(column=2)), # partial
    (         'List_of_towns_in_South_Dakota', wikitable_extractor(column=1)),
    (   'List_of_ghost_towns_in_South_Dakota', wikitable_extractor(column=1)),
    
    (   'List_of_municipalities_in_Tennessee', wikitable_extractor(column=2)),
    (      'List_of_ghost_towns_in_Tennessee', lambda soup: wikilist_extractor()(soup)[:-1]),
    
    (               'List_of_cities_in_Texas', lambda soup: [a['href'][len('/wiki/'):] for a in soup.select('table.wikitable.sortable th[scope="row"] a[href^="/wiki/"]')]),
    (                'List_of_towns_in_Texas', wikitable_extractor(column=1)), # partial
    (          'List_of_ghost_towns_in_Texas', lambda soup: [title for title in sum([wikilist_extractor(table_index=i)(soup) for i in range(1, 9)], [])]),
    
    (        'List_of_municipalities_in_Utah', wikitable_extractor(column=1)),
    (           'List_of_ghost_towns_in_Utah', lambda soup: [title for title in sum([wikilist_extractor(table_index=i)(soup) for i in range(2, 6)], [])]),
    
    (             'List_of_cities_in_Vermont', wikitable_extractor(column=1)),
    (              'List_of_towns_in_Vermont', wikitable_extractor(column=2)),
    (        'List_of_ghost_towns_in_Vermont', wikilist_extractor()),
    
    (             'List_of_towns_in_Virginia', wikitable_extractor(column=1)),
    (       'List_of_ghost_towns_in_Virginia', wikilist_extractor()),
    
    ('List_of_cities_and_towns_in_Washington', wikitable_extractor(column=1)),
    (     'List_of_ghost_towns_in_Washington', wikitable_extractor(column=1)),
    
    (       'List_of_cities_in_West_Virginia', wikitable_extractor(column=2)),
    (        'List_of_towns_in_West_Virginia', lambda soup: [title for title in sum([wikilist_extractor(table_index=i)(soup) for i in range(1, 24)], [])]),
    (  'List_of_ghost_towns_in_West_Virginia', wikilist_extractor()),
    
    (           'List_of_cities_in_Wisconsin', wikitable_extractor(column=1)),
    # ('List_of_municipalities_in_Wisconsin_by_population', ''),
    (            'List_of_towns_in_Wisconsin', wikitable_extractor(column=1)),
    (      'List_of_ghost_towns_in_Wisconsin', wikitable_extractor(column=1)),
    
    (     'List_of_municipalities_in_Wyoming', wikitable_extractor(column=1)),
    (        'List_of_ghost_towns_in_Wyoming', wikilist_extractor())
]


with open(f'{directory}/counties_communities_all.txt', 'r') as file:
    communities_data = file.read()
    
communities_current = set(communities_data.replace('_', ' ').split('\n'))

state_communities_all = []

print('|'.join([f'{"page":>30}', f'{"new":>4}', f'{"total":5}', f'{"first":>25}', f'{"last":>25}', f'{"sample":>55}', '']))
print('|'.join(['-'*30, '-'*4, '-'*5, '-'*25, '-'*25, '-'*100])[:149] + '|')
for title, extract_function in parameters:
    soup = BeautifulSoup(http_get(wikipedia_standard_url(title)), 'html.parser')
    titles = [title.replace('_', ' ') for title in extract_function(soup)]
    difference = len(set(titles).difference(communities_current))
    state_communities_all += titles

    assert difference <= len(titles)

    row = '|'.join([f'{title[-30:].replace("_", " "):>30}', f'{difference:>4}', f'{len(titles):5}', f'{titles[0][:25]:>25}', f'{titles[-1][:25]:>25}', f'{str(np.random.choice(titles, 2)):>55}'])
    print(row[:149] + '|')

print('-'.join(['-'*30, '-'*4, '-'*5, '-'*25, '-'*25, '-'*100])[:149] + '|')
print('total new:', len(set(state_communities_all).difference(communities_current)))
combined = list(communities_current.union(state_communities_all))
print('total:', len(combined))


## -- write list of titles in partitions for https://en.wikipedia.org/wiki/Special:Export

index = 0
partition_size = 30000
while partition := combined[index:index+partition_size]:
    actual_size = len(partition)
    with open(f'{directory}/partition--{index:06.0f}--{index+actual_size-1:06.0f}', 'w') as file:
        file.write('\n'.join(partition))

    index += partition_size
