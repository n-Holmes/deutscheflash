"""A simple CLI app to practice grammatical genders of German nouns."""

import argparse
import json
import pathlib
import pandas as pd

DEFAULT_GENDERS = ("der", "die", "das")


class WordList:
    """Data structure to store a pandas dataframe and some structural details."""

    def __init__(self):
        self.words = None
        self.structure = {}

    def load(self, path: pathlib.Path):
        """Load a the WordList with stored data."""
        try:
            self.words = pd.read_csv(path.with_suffix(".csv"))
            with path.with_suffix(".json").open() as f:
                self.structure = json.loads(f.read())
            self.words.set_index(self.structure["index"], inplace=True)

        except FileNotFoundError:
            self.new()

    def new(self, options=DEFAULT_GENDERS, default_guess_count: int = 5):
        """Create a new wordlist."""
        self.structure = {
            "options": options,
            "default guesses": default_guess_count,
            "index": "Word",
            "column count": 3,
        }

        columns = ["Word", "Gender", "Correct", "Wrong"]
        datatypes = dict(zip(columns, (str,) + (int,) * self.structure["column count"]))

        self.words = pd.DataFrame(columns=columns).astype(datatypes)
        self.words.set_index(self.structure["index"], inplace=True)

    def save(self, path: pathlib.Path):
        """Saves words to a .csv file and structure to a .json."""
        self.words.to_csv(path.with_suffix(".csv"))
        with path.with_suffix(".json").open(mode="w") as f:
            f.write(json.dumps(self.structure))

    def add(self, gender, word):
        gender = gender.lower()
        word = word.capitalize()

        if gender not in self.structure["options"]:
            raise ValueError(
                f"{gender} is not a valid gender for the current wordlist."
            )
        if word in self.words.index:
            raise ValueError(f"{word} is already included.")

        n_options = len(self.structure["options"])
        row = [
            gender,
            self.structure["default guesses"],
            self.structure["default guesses"] * (n_options - 1),
            (n_options - 1) / n_options
        ]
        self.words.loc[word] = row


def main():
    """Main body of the program."""
    args = _parse_args()
    path = pathlib.Path(args.words)

    words = WordList()
    words.load(path)
    print(f"WordList {args.words} successfully loaded.")

    if args.quiz_length:
        print(f"Starting quiz with length {args.quiz_length}...")
        _quiz(words, args.quiz_length)

    elif args.add_words:
        print("Entering word addition mode...")
        _add_words(words)

    elif args.load_words:
        print(f"Importing word file {args.load_words}...")
        added, reps = _load_words(words, args.load_words)
        print(f"{added} words successfully imported. {reps} duplicates skipped.")

    _save_and_exit(words, path)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Flashcard app for German grammatical genders."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-q", "--quiz", type=int, help="Start the app in quiz mode.", dest="quiz_length"
    )
    mode.add_argument(
        "-a",
        "--add-words",
        action="store_true",
        help="Start the app in manual word addition mode.",
    )
    mode.add_argument(
        "-l",
        "--load-words",
        help="Concatenates a prewritten list of words into the saved WordList.",
    )
    parser.add_argument(
        "-w", "--words", default="main_list", help="The name of the WordList to use."
    )
    return parser.parse_args()


def _quiz(words, quiz_length):
    # TODO: implement quiz
    pass


def _add_words(wordlist):
    print("Type a word with gender eg `der Mann` or `quit` when finished.")
    while True:
        input_str = input()
        if input_str == "quit":
            print("Exiting word addition mode...")
            break

        try:
            gender, word = input_str.split()
            wordlist.add(gender, word)
        except ValueError as e:
            print(e)


def _load_words(words, import_path):
    new_words = pd.read_csv(import_path)
    words_added = 0
    repetitions = 0
    for _, row in new_words.iterrows():
        try:
            words.add(row.Gender, row.Word)
            words_added += 1
        except ValueError:
            repetitions += 1
    
    return words_added, repetitions


def _save_and_exit(wordlist, path):
    while True:
        try:
            wordlist.save(path=path)
            # TODO: Can WordList be made into a context manager?
            print("WordList successfully saved, goodbye!")
            break
        except PermissionError:
            print("PermissionError! File may be open in another window.")
            retry = input("Try again? Y/N: ")
            if retry in "Yy":
                continue
            elif retry in "Nn":
                print("Exiting without saving changes.")
                break
            else:
                print("Input not recognised.")


if __name__ == "__main__":
    main()
