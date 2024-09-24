import copy
from xml.etree import ElementTree

import attrs
from .types import TypeDefinition


__all__ = [
    'EnumVal',
    'EnumDef',
    'FieldDef',
    'RecordDef',
    'MessageDef',
    'Definitions',
    'Parser'
]


@attrs.define(auto_attribs=True)
class EnumVal:
    name: str
    description: str
    value: str


@attrs.define(auto_attribs=True)
class EnumDef:
    name: str = ''
    type: str = None
    values: list[EnumVal] = attrs.field(factory=list)

    def get_codegen_context(self, _definitions: 'Definitions'):
        return {
            'name': self.name,
            'quote': TypeDefinition.Definitions[self.type].hint == 'str',
            'values': [
                {
                    'name': field.name,
                    'value': field.value
                } for field in self.values
            ]
        }


@attrs.define(auto_attribs=True)
class FieldDef:
    Definitions = {}
    name: str
    type: str = None
    ref: str = None
    array: str = None
    length: int = None
    default: str = None
    endian: str = None

    def get_codegen_context(self,  definitions: 'Definitions'):
        field_context = self._field_context(definitions)
        field_context.update({'name': self.name})
        return field_context

    def _field_context(self, definitions: 'Definitions'):
        context = {
            'type': '',
            'default': False,
            'default_value': '',
            'quote': False,
            'hint': ''
        }
        types_ = [self.type, self.ref]
        if all(_ is None for _ in types_) or all(_ is not None for _ in types_):
            raise ValueError(f'{self.name=}, invalid type and ref value')

        if self.ref:
            type_, hint = self.ref, self.ref
        elif self.type.startswith('enum:'):
            enum_name = self.type.replace('enum:', '')
            if enum_name not in definitions.enums:
                raise ValueError(f'{enum_name=} not found in definitions')
            enum_def = definitions.enums[enum_name]
            enum_type = TypeDefinition.Definitions[enum_def.type]
            type_, hint = enum_type.__name__, enum_name
        elif self.type.startswith('record:'):
            rec = self.type.replace('record:', '')
            if rec not in definitions.records:
                raise ValueError(f'{rec=} not found in definitions')
            rec = definitions.records[rec]
            type_, hint = rec.name, rec.name
        else:
            type_ = TypeDefinition.Definitions[self.type].__name__
            hint = TypeDefinition.Definitions[self.type].hint

        endian = 'uint_2_be' if self.endian == 'big' else 'uint_2'
        endian = TypeDefinition.Definitions[endian].__name__

        if self.array is not None:
            type_ = f'Array({type_}, {endian})'
            hint = f'list[{hint}]'
            if self.array == 'double':
                type_ = f'Array({type_}, {endian})'
                hint = f'list[{hint}]'

        is_fixed_len_str = self.type in ['str_ascii_n', 'str_iso-8859-1_n']
        type_ = f'{type_}(length={self.length})' if is_fixed_len_str else type_

        context['type'] = type_
        context['hint'] = hint
        context['quote'] = 'Char' in type_ or 'String' in type_
        context['default'] = self.default is not None
        context['default_value'] = self.default

        return context


@attrs.define(auto_attribs=True)
class RecordDef:
    name: str
    fields: list[FieldDef]

    def get_codegen_context(self, definitions: 'Definitions'):
        return {
            'name': self.name,
            'fields': [field.get_codegen_context(definitions) for field in self.fields]
        }


@attrs.define(auto_attribs=True)
class MessageDef:
    name: str
    id: str = attrs.field(converter=lambda x: x if x.isdigit() else str(ord(x)))  # pylint: disable=C0103
    group: str = None
    fields: list[FieldDef] = []
    direction: str = None

    def get_codegen_context(self, definitions: 'Definitions'):
        return {
            'name': self.name,
            'indicator': self.id,
            'group': self.group,
            'fields': [field.get_codegen_context(definitions) for field in self.fields],
            'direction': self.direction
        }


@attrs.define(auto_attribs=True)
class Definitions:
    enums: dict[str, EnumDef] = {}
    records: dict[str, RecordDef] = {}
    messages: list[MessageDef] = []

    def get_codegen_context(self):
        return {
            'enums': [enum.get_codegen_context(self) for enum in self.enums.values()],
            'messages': [message.get_codegen_context(self) for message in self.messages],
            'records': [record.get_codegen_context(self) for record in self.records.values()],
        }


class Parser:
    @staticmethod
    def parse(file: str, override_messages: bool = False) -> Definitions:
        root = ElementTree.parse(file).getroot()
        elements = list(root)
        definitions = Definitions()

        for element in elements:
            if element.tag == 'enums-root':
                definitions.enums = {_.name: _ for _ in Parser._parse_enums(element)}
            elif element.tag == 'fielddef-root':
                FieldDef.Definitions = Parser._parse_fielddefs(element)
            elif element.tag == 'records-root':
                definitions.records = {_.name: _ for _ in Parser._parse_records(element)}
            elif element.tag == 'messages-root':
                definitions.messages = Parser._parse_messages(element, override_messages)

        return definitions

    @staticmethod
    def _parse_fielddefs(element) -> dict[str, FieldDef]:
        return {f.name: f for f in Parser._parse_fields(element)}

    @staticmethod
    def _parse_records(element) -> list[RecordDef]:
        return [RecordDef(record.get('id'), Parser._parse_fields(record[0])) for record in list(element)]

    @staticmethod
    def _parse_messages(element, override_messages: bool = False) -> list[MessageDef]:
        def create_msg(child):
            return MessageDef(
                child.get('id'), child.get('message-id'), child.get('message-group'),
                Parser._parse_fields(child[0] if len(child) else None),
                child.get('direction')
            )
        messages = {}
        for child in list(element):
            msg = create_msg(child)
            key = f'{msg.id}-{msg.group}-{msg.direction}'
            if key in messages and not override_messages:
                raise ValueError(f'Message {key} already exists')
            messages[key] = msg
        return list(messages.values())

    @staticmethod
    def _parse_fields(element) -> list[FieldDef]:
        if element:
            return [Parser._parse_field(field) for field in list(element) if field is not None]
        return []

    @staticmethod
    def _parse_field(element):
        f_def = None
        if element is not None:
            if element.get('def', False):
                field = copy.deepcopy(FieldDef.Definitions[element.get('def')])
                field.name = element.get('name', field.name)
                return field

            f_def = FieldDef(
                element.get('name'),
                element.get('type'),
                element.get('ref'),
                element.get('array'),
                element.get('length'),
                element.get('default'),
                element.get('endian')
            )
        return f_def

    @staticmethod
    def _parse_enums(element):
        if element:
            return [Parser._parse_enum(e) for e in list(element) if e is not None]
        return []

    @staticmethod
    def _parse_enum(element):
        def _parse_value(val_element):
            return EnumVal(val_element.get('name'), val_element.get('description'), val_element.text)

        return EnumDef(element.get('id'), element.get('type'), [_parse_value(_) for _ in element if _ is not None])
