from typing import Any

import attrs

from nasdaq_protocols.common import TypeDefinition


__all__ = [
    'FieldDef',
    'Entry',
    'EntryContainer',
    'Field',
    'Group',
    'Component',
    'Message',
    'Definitions'
]


@attrs.define
class FieldDef:
    tag: str
    name: str
    type: TypeDefinition
    possible_values: dict[str, Any] = None


@attrs.define
class Entry:
    required: bool = attrs.field(kw_only=True)


@attrs.define
class EntryContainer:
    entries: list[Entry] = attrs.field(kw_only=True, factory=list)


@attrs.define
class Field(Entry):
    field: FieldDef = attrs.field(kw_only=True)


@attrs.define
class Group(Entry):
    name: str = attrs.field(kw_only=True)
    entries: list[Entry] = attrs.field(kw_only=True, factory=list)


@attrs.define
class Component(EntryContainer):
    name: str = attrs.field(kw_only=True)


@attrs.define
class Message(EntryContainer):
    tag: str
    name: str
    category: str


@attrs.define
class Definitions:
    fields: dict[str, FieldDef] = attrs.field(init=False, factory=dict)
    components: dict[str, Component] = attrs.field(kw_only=True, factory=dict)
    header: EntryContainer = attrs.field(kw_only=True, factory=EntryContainer)
    trailer: EntryContainer = attrs.field(kw_only=True, factory=EntryContainer)
    messages: list[Message] = attrs.field(kw_only=True, factory=list)
