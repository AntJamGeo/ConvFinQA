from typing import Optional

from conversation_handler import ConversationHandler
from client import Client
from _extra_typing import Entries, EntryKeyCollection

class Tester:
    """A class for testing the conversation handler.

    Args:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries to be tested, with a
            unique key for each that can be used access a specific
            entry.

    Attributes:
        client (Client): A client that handles sending and
            receiving messages to and from an LLM.
        entries (Entries): A collection of entries to be tested, with a
            unique key for each that can be used access a specific
            entry.
        conversations (Dict[EntryKey, ConversationHandler]): The
            conversation handler for each entry, indexed by the entry's
            unique key.
    """
    def __init__(self, client: Client, entries: Entries):
        self.client = client
        self.entries = entries
        self.conversations = {}

    def run(self, indices: Optional[EntryKeyCollection] = None):
        """Generate responses for each entry specified.
        
        Will run through each key provided to access the correct entry
        from the collection provided on initialisation, in order to
        start a conversation with an LLM using the client provided on
        initialisation, and attempt to answer each question.
        The results will be stored in the `conversations` attribute.

        Args:
            indices (Optional[EntryKeyCollection]): An iterable
                containing keys of the entries that you would like to
                generate responses for.
        """
        if indices is None:
            indices = list(self.entries.keys())

        for entry_number, entry_id in enumerate(indices):
            entry = self.entries[entry_id]
            ch = ConversationHandler(self.client, entry.context)
            self.conversations[entry_id] = ch
            for question_number, question in enumerate(entry.questions):
                print(
                    (
                        f"Processing Entry {entry_number+1}/{len(indices)} "
                        f"(id: {entry_id}) - "
                        f"Question {question_number+1}/{len(entry.questions)}"
                        "                 "
                    ),
                    end="\r",
                )
                _, err = ch.ask(question)
                if err is not None:
                    print(
                        f"Found an error processing entry {entry_id}, "
                        f"question {question_number+1}. "
                        "Skipping to the next one..."
                    )
        print(f"Done                                                    ")
