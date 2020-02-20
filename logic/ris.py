import pandas as pd
import logging

def ris_detect(raw):
    """ Detect RIS format style. """
    if raw.startswith('TY  -'):
        logging.debug('RIS file format detected.')
        return 'ris'
    elif raw.startswith('%0'):
        logging.debug('Endnote file format detected.')
        return 'endnote'
    else:
        logging.debug('RIS format not identified.')
        raise Exception(f'Data scheme not recognised. Please check file format.\nBeginning of file: "{raw[:20]}"')


def ris_parse(ris_file):
    """ Read RIS file an parse rows and values to list of lists. """

    with open(ris_file, 'r', encoding='utf-8-sig') as f:
        raw = f.read()

    data_scheme = ris_detect(raw)

    data = raw.strip()

    entry_sep = '\n\n' # Use 'ER  - ' or '\n\n' as entry separator.
    line_sep = '\n'

    # Split data and remove empty rows (Endnote format)
    documents = [item for item in data.split(entry_sep) if item]
    table = [[item for item in doc.split(line_sep)] for doc in documents]

    return table, data_scheme

def ris_df(ris_file):
    """ Extract and return data as DataFrame. """
    
    table, data_scheme = ris_parse(ris_file)

    # Empty template DataFrame.
    df = pd.DataFrame(columns=['title', 'abstract', 'source', 'year', 'publisher', 'type'], index = range(len(table)))

    # Extract relevant data from RIS file table.
    if data_scheme == 'ris':
        for n, j in enumerate(table): 
            for i in j:
                if i.startswith('TI'): 
                    df.loc[n]['title'] = i[6:] 
                if i.startswith('AB'): 
                    df.loc[n]['abstract'] = i[6:] 
                if i.startswith('T2'): 
                    df.loc[n]['source'] = i[6:] 
                if i.startswith('PY'):
                    df.loc[n]['year'] = i[6:]
                if i.startswith('M3'):
                    df.loc[n]['type'] = i[6:]
    else:
        for n, j in enumerate(table):
            for i in j:
                if i.startswith('%T'):
                    df.loc[n]['title'] = i[3:]
                if i.startswith('%X'):
                    df.loc[n]['abstract'] = i[3:]
                if i.startswith('%B'):
                    df.loc[n]['source'] = i[3:]
                if i.startswith('%D'):
                    df.loc[n]['year'] = i[3:]
                if i.startswith('%0'):
                    df.loc[n]['type'] = i[3:]

    return df