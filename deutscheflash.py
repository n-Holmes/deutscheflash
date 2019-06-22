"""A simple CLI app to practice grammatical genders of German nouns."""

import argparse
import json
import pathlib
import pandas as pd

GERMAN_GENDERS = {
    "masculine": "der",
    "neuter": "das",
    "plural": "die",
    "femenine": "die",
}


class WordList:
    """Data structure to store a pandas dataframe and some structural details.
    
    Args:
        path (pathlib.Path or None): The path (without suffix) to a wordlist.
            If there is no current list at the path, will create a new list.
            If no path is provided the WordList will not be fully initialized and will
            require a subsequent call of `load` or `new`.
    """

    def __init__(self, path=None):
        self.words = None
        self.structure = {}

        if path is not None:
            self.load(path)

    def load(self, path: pathlib.Path):
        """Load stored data."""
        try:
            self.words = pd.read_csv(path.with_suffix(".csv"))
            with path.with_suffix(".json").open() as f:
                self.structure = json.loads(f.read())
            self.words.set_index(self.structure["index"], inplace=True)

        except FileNotFoundError:
            self.new()

    def new(self, genders: dict = GERMAN_GENDERS, score_inertia: int = 2):
        """Create a new wordlist.
        
        Args:
            genders (dict): A dictionary of genders and their standard forms.
            score_inertia (int): Determines how resistant scores are to change.
                Must be a positive integer.  Higher values will require more consecutive
                correct answers to reduce the frequency of a specific word.
        """
        self.structure = {
            "genders": genders,
            "aliases": self._get_aliases(genders),
            "default guesses": score_inertia,
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

    def format_gender(self, gender_string: str):
        """Attempts to find a matching gender for gender_string.
        
        Args:
            gender_string (str): A gender for the word list or an alias of a gender.
        
        Returns:
            The associated gender.
        
        Raises:
            ValueError: `gender_string` does not match any gender or alias.
        """
        gender_string = gender_string.lower()
        if gender_string in self.structure["genders"]:
            return gender_string
        if gender_string in self.structure["aliases"]:
            return self.structure["aliases"][gender_string]

        raise ValueError(f"Unknown gender: {gender_string}")

    def add(self, gender: str, word: str):
        """Add a new word to the list.
        
        Args:
            gender (str): The gender of the word being added.
            word (str): The word to add.
        
        Raises:
            ValueError: `gender` does not match the current wordlist or the word is
                already present in the list.
        """
        gender = self.format_gender(gender)
        word = word.capitalize()

        if gender not in self.structure["genders"]:
            raise ValueError(
                f"{gender} is not a valid gender for the current wordlist."
            )
        if word in self.words.index:
            raise ValueError(f"{word} is already included.")

        n_genders = len(self.structure["genders"])
        row = [
            gender,
            self.structure["default guesses"],
            self.structure["default guesses"] * (n_genders - 1),
            (n_genders - 1) / n_genders,
        ]
        self.words.loc[word] = row

    def get_words(self, n:int, distribution:str="weighted"):
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

        n_genders = len(self.structure["genders"])
        total = row.Correct + row.Wrong
        if not total % n_genders:
            # Throw away some data as evenly as possible to allow for change over time
            # Never throw away the last negative result to avoid question being lost.
            if row.Correct:
                wrongs_to_throw = min(row.Wrong - 1, n_genders - 1)
                row.Wrong -= wrongs_to_throw
                row.Correct -= n_genders - wrongs_to_throw
            else:
                row.wrong -= n_genders

        row.Weight = row.Wrong / (row.Correct + row.Wrong)

        self.words.loc[word] = row

    @staticmethod
    def _get_aliases(genders: dict):
        """Create a dictionary of aliases and the genders they refer to.
        May have issues if multiple genders have the same article or first letter.
        """
        aliases = {}
        for gender, article in genders.items():
            aliases[gender[0]] = gender
            aliases[article] = gender
        return aliases


def main():
    """Main body of the program."""
    args = _parse_args()
    path = pathlib.Path(args.words)

    words = WordList(path)
    print(f"WordList {args.words} successfully loaded.")

    if args.quiz_length is not None:
        if args.quiz_length == 0:
            print("Starting quiz in endless mode. Answer `quit` to end the quiz.")
            correct, answered = _quiz_endless(words)
        elif args.quiz_length > 0:
            print(f"Starting quiz with length {args.quiz_length}...\n")
            correct, answered, _ = _quiz(words, args.quiz_length)
        else:
            raise ValueError(f"Invalid quiz length: {args.quiz_length}.")

        print(f"\nYou successfully answered {correct} out of {answered} questions!")

    elif args.add_words:
        print("Entering word addition mode...")
        _add_words(words)

    elif args.load_words:
        print(f"Importing word file {args.load_words}...")
        added, reps = _load_words(words, args.load_words)
        print(f"{added} words successfully imported. {reps} duplicates skipped.")
    
    elif args.reset_scores:
        print("Resetting scores")
        words = WordList()
        words.new()
        _load_words(words, path.with_suffix('.csv'))

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
    mode.add_argument(
        "-r",
        "--reset-scores",
        action="store_true",
        help="Reset all scores in the specified word list."
    )
    parser.add_argument(
        "-w", "--words", default="main_list", help="The name of the WordList to use."
    )
    return parser.parse_args()


def _quiz(wordlist, quiz_length):
    """Runs a command line quiz of the specified length."""
    pd.options.mode.chained_assignment = None  # Suppresses SettingWithCopyWarning

    answered, correct = 0, 0
    for word, gender in wordlist.get_words(quiz_length):
        guess = input(f"What is the gender of {word}? ").lower()
        if guess in ("quit", "exit"):
            break

        answered += 1

        try:
            guess = wordlist.format_gender(guess)
        except ValueError:
            print("Unrecognised guess, skipping.\n")
            continue
        
        accurate = gender == guess
        wordlist.update_weight(word, accurate)
        if accurate:
            print("Correct!\n")
            correct += 1
        else:
            print(f"Incorrect! The correct gender is {gender}.\n")

    return correct, answered, answered == quiz_length


def _quiz_endless(wordlist):
    """Runs quizzes in batches of 20 until quit or exit is answered."""
    correct, answered = 0, 0
    finished = False
    while not finished:
        results = _quiz(wordlist, 20)
        correct += results[0]
        answered += results[1]
        finished = not results[2]

    return correct, answered


def _add_words(wordlist):
    """CLI for adding words individually to the wordlist."""
    print("Type a word with gender eg `m Mann` or `quit` when finished.")
    while True:
        input_str = input()
        if input_str in ("quit", "exit"):
            print("Exiting word addition mode...")
            break

        try:
            gender, word = input_str.split()
            wordlist.add(gender, word)
        except ValueError as e:
            print(e)


def _load_words(wordlist, import_path):
    """Loads words from a csv file at import_path into `wordlist`."""
    new_words = pd.read_csv(import_path)
    words_added = 0
    repetitions = 0
    for _, row in new_words.iterrows():
        try:
            wordlist.add(row.Gender, row.Word)
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
