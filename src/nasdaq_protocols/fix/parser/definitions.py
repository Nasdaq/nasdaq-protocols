import keyword
from collections import defaultdict
from itertools import count
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

from nasdaq_protocols.fix.parser.version_types import Version


@attrs.define
class FieldDef:
    tag: str
    name: str
    type: TypeDefinition
    possible_values: dict[str, Any] = None

    def _values_ctx(self):
        output = []
        if self.possible_values:
            for key, value in self.possible_values.items():
                value = f'{value}' if not keyword.iskeyword(value) else f'{value}_'
                output.append({
                    'f_name': key,
                    'f_value': value,
                    'quote': self.type.type_cls in [str, bool]
                })
        return output

    def get_codegen_context(self, _definitions):
        return {
            'tag': self.tag,
            'name': self.name,
            'type': self.type.__name__,
            'type_hint': self.type.hint,
            'values': self._values_ctx()
        }


@attrs.define
class Entry:
    required: bool = attrs.field(kw_only=True)

    def get_codegen_context(self, _definitions):
        return {
            'required': 'True' if self.required else 'False'
        }


@attrs.define
class EntryContainer:
    entries: list[Entry] = attrs.field(kw_only=True, factory=list)

    def get_codegen_context(self, definitions):
        return {
            'entries': [entry.get_codegen_context(definitions) for entry in self.entries]
        }


@attrs.define
class Field(Entry):
    field: FieldDef = attrs.field(kw_only=True)

    def get_codegen_context(self, definitions):
        return super().get_codegen_context(definitions) | {
            'field': self.field.get_codegen_context(definitions)
        }


@attrs.define
class Group(Entry):
    name: str = attrs.field(kw_only=True)
    entries: list[Entry] = attrs.field(kw_only=True, factory=list)

    Contexts = []
    UniqueNameCounter = defaultdict(lambda: count(1))

    def get_codegen_context(self, definitions):
        unique_name = f'{self.name}_{next(Group.UniqueNameCounter[self.name])}'  # to avoid name conflicts
        group_context = super().get_codegen_context(definitions) | {
            'name': self.name,
            'unique_name': unique_name,
            'is_group': True,
            'entries': [entry.get_codegen_context(definitions) for entry in self.entries],
        }

        Group.Contexts.append({
            'name': self.name,
            'unique_name': unique_name,
            'entries': [entry.get_codegen_context(definitions) for entry in self.entries],
        })
        return group_context


@attrs.define
class Component(EntryContainer):
    name: str = attrs.field(kw_only=True)


@attrs.define
class Message(EntryContainer):
    tag: str
    name: str
    category: str

    def get_codegen_context(self, definitions):
        return super().get_codegen_context(definitions) | {
            'tag': self.tag,
            'name': self.name,
            'category': self.category,
        }


@attrs.define
class Definitions:
    version: Version
    fields: dict[str, FieldDef] = attrs.field(init=False, factory=dict)
    components: dict[str, Component] = attrs.field(kw_only=True, factory=dict)
    header: EntryContainer = attrs.field(kw_only=True, factory=EntryContainer)
    trailer: EntryContainer = attrs.field(kw_only=True, factory=EntryContainer)
    messages: list[Message] = attrs.field(kw_only=True, factory=list)

    def get_codegen_context(self):
        message_context = [
            message.get_codegen_context(self) | {
                'body_name': f'{message.name}Body',
            }
            for message in self.messages
        ]
        return {
            'client_session': self._client_session(),
            'fields': [field.get_codegen_context(self) for field in self.fields.values()],
            'bodies': [
                          self.header.get_codegen_context(self) | {
                              'body_name': 'Header',
                          },
                          self.trailer.get_codegen_context(self) | {
                              'body_name': 'Trailer',
                          },
                      ] + message_context,
            'messages': message_context,
            'groups': Group.Contexts,  # always last, as it is dependent on other entries
        }

    def _client_session(self):
        if self.version == Version.FIX_4_4:
            return 'Fix44Session'
        if self.version in (Version.FIX_5_0, Version.FIX_5_0_2):
            return 'Fix50Session'
        raise ValueError(f'Version {self.version} is not supported')
