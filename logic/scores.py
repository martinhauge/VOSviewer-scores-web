import os
import re
import logging
import pandas as pd
from logic.reftypes import db
from logic.ris import ris_df, ris_detect
from flask import flash, Markup

ALLOWED_EXTENSIONS = ['csv', 'txt', 'xls']
TEMP_DIR = 'temp'
OUTPUT_PATH = os.path.join('data', 'output')
SUMMARY_LEN = 10

log_level = logging.DEBUG

logging.basicConfig(level=log_level, format='[%(asctime)s] %(levelname)s (%(module)s): %(message)s')

# Filter db dictionary to only include scores values for front-end validation.
scores_dict = {base: [key for key in db[base]['values']] for base in db}

class ScoresHandler:

    # Generate output folder on first use.
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
        logging.debug('Output path created.')
    else:
        logging.debug('Output path identified.')

    # Generate folder for temporary files on first use.
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logging.debug('Temp folder created.')
    else:
        logging.debug('Temp folder identified.')
        
    def __init__(self, params, files):
        self.files = files
        self.checked_files = [f for f in self.files if allowed_file(f.filename)]
        if self.checked_files:
            self.success = True
            self.save_input_files()
        else:
            logging.debug('No valid files submitted.')
            flash('No valid files submitted.', 'danger')
            self.success = False

        if 'value' in params:
            self.value = params['value']
        else:
            self.value = None
        
        if params['corpus'] == 'yes':
            self.skip_corpus = True
        else:
            self.skip_corpus = False

        if self.success:
            if params['db'] == 'auto':
                if self.checked_files:
                    # Save temp file
                    test_file = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
                    logging.debug('Attempting auto-detection...')
                    detection = detect_base(test_file)
                    if detection:
                        self.base = detection
                        flash(f'{db[self.base]["name"]} format detected.', 'primary')
                        
                    else:
                        logging.critical('Auto-detection unsuccessful')
                        flash('Auto-detection failed. Please check input or specify database.', 'danger')
                        self.success = False
            else:
                self.base = params['db']

        if self.success:
            if params['buckets'] == 'yes':
                self.buckets = True
                self.interval = int(params['interval-range'])
            else:
                self.buckets = False

            if self.value in db[self.base]['values'].keys():
                # Setup database parameters
                self.sep = db[self.base]['sep']
                self.enc = db[self.base]['enc']
                self.title = db[self.base]['ti']
                self.abstract = db[self.base]['ab']
                self.quote = db[self.base]['quote']
                self.db_value = db[self.base]['values'][self.value]

                # Generate output file names
                if params['output-name']:
                    self.out_name = os.path.join(OUTPUT_PATH, params['output-name']) # generate_filename()
                else:
                    self.out_name = os.path.join(OUTPUT_PATH, 'text_data') # generate_filename()

                self.scores_name = generate_filename(self.out_name, suffix=f'_scores_{self.value}')

                if not self.skip_corpus:
                    self.corpus_name = generate_filename(self.out_name, '_corpus')
            else:
                self.success = False
                flash(f'This value is not supported for {db[self.base]["name"]} files. Please try another value.', 'warning')


    def __repr__(self):
        return f'ScoresHandler({self.params}, {self.files})'

    def save_input_files(self):
        if self.files[0].filename == '':
            logging.warning('No files submitted.')
            # Return error
        else:
            logging.debug(f'{len(self.files)} file(s) submitted.')
            logging.debug(f'{len(self.checked_files)} file(s) allowed.')
            self.file_paths = []
            for f in self.checked_files:
                file_path = os.path.join(TEMP_DIR, f.filename)
                f.save(file_path)
                logging.debug(f'{f.filename} saved to temporary directory.')
                self.file_paths.append(file_path)

    def clean_up(self):
        for f in os.listdir(TEMP_DIR):
            logging.debug(f'Deleting temporary file: {os.path.join(TEMP_DIR, f)}')
            os.unlink(os.path.join(TEMP_DIR, f))

    def create_df(self):

        file_error = 'Could not add {} to DataFrame.'
        self.df = pd.DataFrame()
        
        for f in self.file_paths:
            try:
                logging.debug(f'Adding {self.base} file to DataFrame:')
                logging.debug(f)
                if self.base == 'proquest':
                    # Special case for Proquest XLS format.
                    add_file = pd.read_excel(f, index_col=False, usecols=[self.title, self.abstract, self.db_value])
                    self.df = self.df.append(add_file)
                elif self.base == 'ris':
                    # Special case for RIS/Endnote format.
                    self.df = self.df.append(ris_df(f))
                else:
                    add_file = pd.read_csv(f, sep=self.sep, encoding=self.enc, index_col=False, usecols=[self.title, self.abstract, self.db_value], quoting=self.quote)
                    self.df = self.df.append(add_file)
            except Exception as error:
                logging.critical(file_error.format(f))
                logging.critical(error)
                self.success = False

    def generate_scores(self):
        # Check for intervals.
        if self.buckets:
            if self.value in ['py', 'nc']:
                self.df[self.db_value] = self.generate_buckets()
            else:
                logging.warning(f'Intervals unavailable for {self.value}. Creating standard scores file.')
                flash('Intervals can only be applied to publication year and number of citations. Original scores value used.', 'warning')
        
        # Count N/A values for summary.
        self.values_na = self.df[self.db_value].isna().sum()

        # Count N/A abstracts for summary
        self.abstracts_na = self.df[db[self.base]['ab']].isna().sum()

        # Create list of unique values.
        values_list = self.df[self.db_value].fillna('N/A')
        values_list.reset_index(drop=True, inplace=True)
        unique_values = set(sorted([str(i).lower() for i in values_list.unique()]))

        # Create default DataFrame of zeroes for scores based on unique values.
        self.scores_df = pd.DataFrame(columns=unique_values, index=values_list.index).fillna(0)

        # Populate the DataFrame with ones corresponding to values.
        for index, value in enumerate(values_list):
            self.scores_df[str(value).lower()][index] = 1

        self.format_scores()

    def format_scores(self):
        # Remove illegal characters and sort columns.
        self.scores_df.columns = [re.sub('[\[\]<>_]', '', col) for col in self.scores_df.columns]
        self.scores_df.sort_index(axis=1, inplace=True)

        # Convert to VOSviewer scores header format.
        self.scores_df.columns = [f'score<{col}>' for col in self.scores_df.columns]

    def save_output_files(self):
        if os.path.exists(self.scores_name):
            logging.warning(f'Scores file not created. {self.scores_name} already exists.')
            flash('Scores file already exists. Please change the output name.', 'warning')
        else:
            self.scores_df.to_csv(path_or_buf=self.scores_name, sep='\t', index=False)
            logging.debug(f'Scores file saved as {self.scores_name}.')
            flash(f'Scores file saved as {self.scores_name}.', 'success')

        if not self.skip_corpus:

            # Save titles and abstracts to new DataFrame
            titles = self.df[db[self.base]['ti']]
            abstracts = self.df[db[self.base]['ab']].fillna('-')
            self.corpus_df = pd.DataFrame(titles + ' ' + abstracts)

            if os.path.exists(self.corpus_name):
                logging.warning(f'Corpus file not created. {self.corpus_name} already exists.')
                flash('Corpus file already exists. Please change the output name or use existing corpus.', 'warning')
            else:
                self.corpus_df.to_csv(path_or_buf=self.corpus_name, sep='\t', index=False, header=False)
                logging.debug(f'Corpus file saved as {self.corpus_name}.')
                flash(f'Corpus file saved as {self.corpus_name}.', 'success')
        else:
            logging.debug('Skipping corpus file.')

    def generate_buckets(self):
        # Genereate range of intervals from scores values
        numbers = self.df[self.db_value].fillna(0).astype(int)
        num_list = [n for n in range(numbers.min() - self.interval, numbers.max() + self.interval + 1) if n % self.interval == 0]

        # Generate left-inclusive list of intervals.
        intervals = pd.cut(numbers, num_list, right=False)

        # Clean up labels.
        intervals = intervals.astype(str).str.strip('[)').str.replace(', ', '-')

        # Relabel N/A values.
        intervals = intervals.str.replace('^0-.*', 'N/A')
        
        return intervals

    def multi_scores(self):
        # Fetch scores value from multi-score cells
        # C1 Author Adress (WOS)
        # First value:
        # [i.split()[-1] for i in s.split('; [')][0]
        # Different values:
        # [i.split()[-1] for i in s.split('; [')][0]  
        pass

    def generate_summary(self):
        # Open tags for summary.
        summary_str = '<ul uk-accordion><li><a class="uk-accordion-title" href="#">Summary</a><div class="uk-accordion-content"><ul>'
        
        summary_str += f'<li>Number of scores: {len(self.scores_df.columns)}</li>'
        summary_str += f'<li>Number of references: {len(self.scores_df)}</li>'
        values_pct = '{:.2%}'.format(self.values_na / len(self.scores_df))
        summary_str += f'<li>Scores value not available: {self.values_na} ({values_pct})</li>'
        if not self.skip_corpus:
            abstract_pct = '{:.2%}'.format(self.abstracts_na / len(self.scores_df))
            summary_str += f'<li>Abstract not available: {self.abstracts_na} ({abstract_pct})</li>'
        
        # Open tags for list of values.
        summary_str += '<li><div>Top scores values:</div><ol>'
        
        values_distribution = self.scores_df.sum().sort_values(ascending=False).head(SUMMARY_LEN)
        for index, count in values_distribution.items():
            scores_pct = '{:.2%}'.format(count / len(self.scores_df))
            summary_str += f'<li>{clean_name(index)}: {count} ({scores_pct})'

        # Closing tags for list of values.
        summary_str += '</ol></li>'

        if len(self.scores_df.sum()) > SUMMARY_LEN:
            summary_str += f'<div><i>... and {len(self.scores_df.sum()) - SUMMARY_LEN} more.</i></div>'
        
        # Closing tags summary.
        summary_str += '</ul></div></li></ul>'

        flash(Markup(summary_str))

def allowed_file(filename):
    return '.' in filename and filename.split('.')[1].lower() in ALLOWED_EXTENSIONS

def clean_name(name):
    return name.replace('score<', '').replace('>', '')

def generate_filename(file_name, suffix='', digits=2, extension='txt'):
    """Generate unique file name by incrementing number suffix."""

    # Build template file name
    master_name = '{0}{{:0{1}}}{2}.{3}'.format(file_name, digits, suffix, extension)
    file_num = 1
    output_name = master_name.format(file_num)

    # Iterate over files in folder until a vacant file name is found
    while os.path.isfile(output_name):
        file_num += 1
        output_name = master_name.format(file_num)

    logging.debug('File named "{}".'.format(output_name))
    return output_name

def detect_base(test_file):
    # Check filename for clues.
    if test_file.endswith('.xls'):
        print('This looks like the format of ProQuest.')
        return 'proquest'
    elif test_file.endswith('.csv'):
        print('This looks like the format of Scopus.')
        return 'scopus'
    elif test_file.endswith('.txt') or test_file.endswith('.ris'):
        try:
            logging.debug('Trying UTF-16-LE...')
            with open(test_file, 'r', encoding='utf-16-le') as f:
                head = next(f)
            logging.debug(f'Beginning of file: {head[:20]}')
            logging.debug('File read with UTF-16-LE encoding...')
            if head.startswith('\ufeffPT'):
                print('This looks like the format of Web of Science.')
                return 'wos'
            else:
                logging.debug('Header not matched.')
                try:
                    logging.debug('Trying UTF-8...')
                    with open(test_file, 'r', encoding='utf-8-sig') as f:
                        head = next(f)
                    logging.debug(f'Beginning of file: {head[:20]}')
                    logging.debug('File read with UTF-8 encoding...')
                    try:
                        ris_detect(head)
                        print('This looks like the format of RIS or Endnote.')
                        return 'ris'
                    except:
                        pass
                except Exception as err:
                    logging.debug(err)
        except Exception as err:
            logging.debug(err)
            try:
                logging.debug('Trying UTF-8...')
                with open(test_file, 'r', encoding='utf-8-sig') as f:
                    head = next(f)
                logging.debug(f'Beginning of file: {head[:20]}')
                logging.debug('File read with UTF-8 encoding...')
                try:
                    ris_detect(head)
                    print('This looks like the format of RIS or Endnote.')
                    return 'ris'
                except:
                    pass
            except:
                pass
    logging.debug('Failed to auto-detect format. Please specify in user variables.')
    return None