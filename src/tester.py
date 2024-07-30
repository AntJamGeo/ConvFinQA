from conversation_handler import ConversationHandler
from client import Client
from _extra_typing import Entries, EntryKeyCollection

class Tester:
    """A class for testing the conversation handler.

    Args:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries
            to be tested, with a unique key for each that can be used
            access a specific entry.

    Attributes:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries
            to be tested, with a unique key for each that can be used
            access a specific entry.
        conversations (Dict[EntryKey, Conversation]): The message
            history of the each conversation, indexed by the entry's
            unique key.
    """
    def __init__(self, client: Client, entries: Entries):
        self.client = client
        self.entries = entries
        self.conversations = {}

    def run(self, indices: EntryKeyCollection):
        """Generate responses for each entry specified.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation, in order to
        start a conversation with an LLM using the client provided on
        initialisation, and attempt to answer each question.
        The results will be stored in the `conversations` attribute.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to generate responses
                for.
        """
        for i, entry_index in enumerate(indices):
            entry = self.entries[entry_index]
            ch = ConversationHandler(self.client, entry["context"])
            self.conversations[entry_index] = ch
            for j, question in enumerate(entry["questions"]):
                print(f"Processing Entry {i+1}/{len(indices)} (id: {entry_index}) - Question {j+1}/{len(entry["questions"])}                 ", end="\r")
                _, err = ch.ask(question)
                if err is not None:
                    print(
                        f"Found an error processing entry {entry_index}, question {j+1}. "
                        "Skipping to the next one..."
                    )
        print(f"Done                                                    ")

    def compare(self, indices: EntryKeyCollection):
        """View the difference between expected and generated results.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation. For each key,
        you can see the expected vs generated programs, followed by
        the expected vs generated final answers.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to compare results
                for.
        """
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation found with index {i}")
                continue
            entry, conv = self.entries[i], self.conversations[i]
            print(f"Entry {i}")
            print(entry["answers"])
            print(conv.extracted_answers)
            print("----------------------------------------")
            print(entry["exe_answers"])
            print(conv.exe_answers)
            print("\n----------------------------------------\n")

    def view_err_log(self, indices: EntryKeyCollection):
        """View the error logs.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation. For each key,
        you can see the errors raised while attempting to answer each
        question, if there were any.

        Args:
            indices (EntryKeyCollection): An iterable containing keys
                of the entries that you would like to view the errors
                for.
        """
        for i in indices:
            if i not in self.conversations:
                print(f"No conversation found with index {i}")
                continue
            if not self.conversations[i].err_log:
                continue
            print(f"Entry {i}")
            for err in self.conversations[i].err_log:
                print("----------------------------------------")
                print(err)
            print("\n----------------------------------------\n")