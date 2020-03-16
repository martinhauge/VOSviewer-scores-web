import csv

# Currently supported databases are Web of Science, Scopus and Proquest as well as RIS files.
# The 'db' dictionary allows for additional scores values as well as adjustment of file encodings etc.
db = {
    'wos': {
            'name': 'Web of Science',
            'sep': '\t',
            'enc': 'utf-16-le', # Change encoding to 'utf-8' for Win UTF-8 format
            'quote': csv.QUOTE_NONE,
            'ti': 'TI',
            'ab': 'AB',
            'so': 'SO',
            'py': 'PY',
            'pu': 'PU',
            'ty': 'DT'
            },
    'scopus': {
            'name': 'Scopus',
            'sep': ',',
            'enc': None,
            'quote': csv.QUOTE_ALL,
            'ti': 'Title',
            'ab': 'Abstract',
            'so': 'Source title',
            'py': 'Year',
            'pu': 'Publisher',
            'ty': 'Document Type',
            'at': 'Access Type'
            },
    'proquest': {
            'name': 'ProQuest',
            'sep': '\t',
            'enc': None,
            'quote': csv.QUOTE_ALL,
            'ti': 'Title',
            'ab': 'Abstract',
            'so': 'pubtitle',
            'py': 'year',
            'pu': 'publisher',
            'ty': 'ArticleType'
            },
    'ris': {
            'name': 'RIS/Endnote',
            'sep': None,
            'enc': 'utf-8-sig',
            'quote': csv.QUOTE_ALL,
            'ti': 'title',
            'ab': 'abstract',
            'so': 'source',
            'py': 'year',
            'pu': None,
            'ty': 'type'
            }
    }