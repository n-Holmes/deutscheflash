import pandas as pd

DEFAULT_GENDERS = ('der', 'die', 'das')

def new_word_list(genders=DEFAULT_GENDERS, default_guess_count=5):
    """Create a new wordlist"""
    columns = ('word', 'gender',) + genders
    datatypes = dict(zip(columns, (str, str) + (int,) * len(genders)))

    word_list = pd.DataFrame(columns=columns)
    word_list = word_list.astype(datatypes)
    word_list.set_index('word', inplace=True)

    word_list.loc['default'] = default_guess_count
    word_list.loc['default', 'gender'] = None

    return word_list, genders

def load_word_list(path):
    """Load a word list object.

    Args:
        path: path object or string location of word list csv

    Returns:
        pandas dataframe of the wordlist

    Raises:
        FileNotFoundError: If the path is invalid and the user chooses not to
            make a new wordlist.
    """
    try:
        word_list = pd.read_csv(path)
        word_list.set_index('word', inplace=True)
        return word_list
    except FileNotFoundError:
        print(f"No file found at path '{path}'.")
        newfile = input('Would you like to create a new word list there? Y/N')
        if newfile == 'Y':
            word_list, genders = new_word_list()
            save_word_list(word_list, path)
            return word_list, genders
        raise FileNotFoundError

def save_word_list(word_list, path):
    word_list.to_csv(path)
