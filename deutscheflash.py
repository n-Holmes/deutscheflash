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

    def new(self, options=DEFAULT_GENDERS, default_guess_count: int = 2):
        """Create a new wordlist."""
        self.structure = {
            "options": options,
            "default guesses": default_guess_count,
            "index": "Word",
            "column count": 3,
        }

        columns = ["Word", "Gender", "Correct", "Wrong", "Weight"]
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
            (n_options - 1) / n_options,
        ]
        self.words.loc[word] = row

    def get_words(self, n, distribution="weighted"):
        """Selects and returns a sample of words and their genders.

        Args:
            n (int): The number of results wanted.
            distribution (str): The sampling method to use. Either `uniform` or
                `weighted`.

        Yields:
            A tuple of strings in the format (word, gender).
        """
        if distribution == "uniform":
            sample = self.words.sample(n=n)

        elif distribution == "weighted":
            sample = self.words.sample(n=n, weights="Weight")

        else:
            raise ValueError(f"Unknown value for distribution: {distribution}")

        for row in sample.iterrows():
            yield row[0], row[1].Gender

    def update_weight(self, word, guess):
        """Update the weighting on a word based on the most recent guess.
        
        Args:
            word (str): The word to update. Should be in the index of self.words.
            guess (bool): Whether the guess was correct or not.
        """

        row = self.words.loc[word]
        if guess:
            row.Correct += 1
        else:
            row.Wrong += 1

        n_options = len(self.structure["options"])
        total = row.Correct + row.Wrong
        if not total % n_options:
            # Throw away some data as evenly as possible to allow for change over time
            if row.Correct:
                wrongs_to_throw = min(row.Wrong, n_options - 1)
                row.Wrong -= wrongs_to_throw
                row.Correct -= n_options - wrongs_to_throw
            else:
                row.wrong -= n_options

        row.Weight = row.Wrong / (row.Correct + row.Wrong)

        self.words.loc[word] = row


def main():
    """Main body of the program."""
    args = _parse_args()
    path = pathlib.Path(args.words)

    words = WordList()
    words.load(path)
    print(f"WordList {args.words} successfully loaded.")

    if args.quiz_length:
        print(f"Starting quiz with length {args.quiz_length}...\n")
        correct, answered = _quiz(words, args.quiz_length)
        print(f"You successfully answered {correct} out of {answered} questions!")

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
    """Runs a command line quiz of the specified length."""
    pd.options.mode.chained_assignment = None  # Suppresses SettingWithCopyWarning

    answered = 0
    correct = 0
    for word, gender in words.get_words(quiz_length):
        guess = input(f"What is the gender of {word}? ").lower()
        if guess == "quit":
            break

        accurate = gender == guess
        words.update_weight(word, accurate)
        answered += 1

        if accurate:
            print("Correct!\n")
            correct += 1
        else:
            print(f"Incorrect! The correct gender is {gender} {word}.")

    return correct, answered


def _add_words(wordlist):
    """CLI for adding words individually to the wordlist."""
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


def _load_words(word_list, import_path):
    """Loads words from a csv file at import_path into `word_list`."""
    new_words = pd.read_csv(import_path)
    words_added = 0
    repetitions = 0
    for _, row in new_words.iterrows():
        try:
            word_list.add(row.Gender, row.Word)
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
