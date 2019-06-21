"""A simple CLI app to practice grammatical genders of German nouns."""

import argparse
import json
import pathlib
import pandas as pd

DEFAULT_GENDERS = ["der", "die", "das"]

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
            "index": "word",
            "column count": len(options) + 1,
        }

        columns = ["word", "gender"] + options
        datatypes = dict(zip(columns, (str,) + (int,) * self.structure["column count"]))

        self.words = pd.DataFrame(columns=columns).astype(datatypes)
        self.words.set_index(self.structure["index"], inplace=True)

    def save(self, path: pathlib.Path):
        """Saves words to a .csv file and structure to a .json."""
        self.words.to_csv(path.with_suffix(".csv"))
        with path.with_suffix(".json").open(mode="w") as f:
            f.write(json.dumps(self.structure))

    def add(self, gender, word):
        if gender not in self.structure["options"]:
            raise ValueError(
                f"{gender} is not a valid gender for the current wordlist."
            )
        row = [self.structure["default guesses"]] * self.structure["column count"]
        row[0] = gender
        self.words.loc[word.capitalize()] = row


def main():
    """Main body of the program."""
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
    args = parser.parse_args()

    words = WordList()
    words.load(pathlib.Path(args.words))
    print(f"WordList {args.words} successfully loaded.")

    if args.quiz_length:
        print(f"Starting quiz with length {args.quiz_length}...")
    elif args.add_words:
        print("Entering word addition mode...")
    elif args.load_words:
        print(f"Importing word file {args.load_words}...")
        print("Words successfully imported.")


if __name__ == "__main__":
    main()
