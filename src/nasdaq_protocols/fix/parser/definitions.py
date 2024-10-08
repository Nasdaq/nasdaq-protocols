from typing import Any

import attr
import attrs

from nasdaq_protocols.common import TypeDefinition


__all__ = [
    'FieldDef',
    'Entry',
    'EntryContainer',
    'Field',
    'Group',
    'Component',
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
class Definitions:
    fields: dict[str, FieldDef] = attrs.field(init=False, factory=dict)
    components: dict[str, Component] = attr.field(kw_only=True, factory=dict)
