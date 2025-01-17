from typing import Any, Dict, List
from collections.abc import Hashable, Iterable

from entry import Entry

# A message from a conversation.
# Each message is a dict with two keys:
#   - "role": the agent who sent the message (this can either be the
#       "user" or the LLM "assistant")
#   - "content": the content of the message
type Message = Dict[str, str]

# A conversation is an ordered collection of messages
type Conversation = List[Message]

# An entry key uniquely identifies an entry
type EntryKey = Hashable

type Entries = Dict[EntryKey, Entry]

type EntryKeyCollection = Iterable[EntryKey]