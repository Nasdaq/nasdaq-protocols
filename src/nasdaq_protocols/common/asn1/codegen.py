import keyword
import os
import logging
import shutil
from importlib import resources
from pathlib import Path

import attrs
import chevron
import asn1tools
from . import templates
from .types import Asn1Type

__all__ = [
    'Ans1Generator'
]
TEMPLATES_PATH = resources.files(templates)
BASIC_TYPES = [
    'enumerated',
    'integer',
    'real',
    'octetstring',
    'bitstring',
    'boolean',
    'numericstring',
    'visiblestring',
    'printablestring',
    'graphicstring'
]
LOG = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class Ans1Generator:
    asn1_input_files_dir: str
    app_name: str
    pdu: str
    op_dir: str
    template: str
    prefix: str = ''
    package_name: str = ''
    generate_init_file: bool = False
    _op_file: str = None
    _module_name: str = None
    _asn1_files: list = None

    def __attrs_post_init__(self):
        prefix = f'{self.prefix}_' if self.prefix else ''
        self.template = self.template if self.template.endswith('.mustache') else f'{self.template}.mustache'
        self.template = os.path.join(str(TEMPLATES_PATH), self.template)
        self._module_name = f'{prefix}{self.app_name}'
        self._op_file = os.path.join(self.op_dir, f'{self._module_name}.py')
        self._asn1_files = [
            os.path.join(self.asn1_input_files_dir, file)
            for file in os.listdir(self.asn1_input_files_dir)
            if file.endswith('.asn1')
        ]
        shutil.rmtree(self.op_dir)
        Path(self.op_dir).mkdir(parents=True, exist_ok=True)

    def generate(self, extra_context=None):
        asn1_parsed = _Parser(self._asn1_files).parse()
        context = {
            'app_name': self.app_name,
            'pdu_name': self.pdu,
            'package_name': self.package_name,
            'spec': {
                'name': self.app_name,
                'capitalised_name': self.app_name.capitalize()
            },
            'types': Ans1Generator._prepare_types_context(asn1_parsed),
        }
        context.update(extra_context or {})

        generated_files = [Ans1Generator._generate(self.template, context, self._op_file)]
        if self.generate_init_file:
            generated_files.append(self._generate_init_file())

        self._copy_asn1_files()

        return generated_files

    def _generate_init_file(self):
        init_file = os.path.join(self.op_dir, '__init__.py')
        context = {
            'modules': [
                {'name': self._module_name}
            ]
        }
        init_template = os.path.join(str(TEMPLATES_PATH), 'init.mustache')
        Ans1Generator._generate(init_template, context, init_file)
        return init_file

    def _copy_asn1_files(self):
        op_spec_dir = os.path.join(self.op_dir, 'spec')
        Path(op_spec_dir).mkdir(parents=True, exist_ok=True)
        for spec_file in self._asn1_files:
            shutil.copy2(spec_file, os.path.join(op_spec_dir, os.path.basename(spec_file)))

    @staticmethod
    def _prepare_types_context(asn1_parsed):
        types = []
        for type_name, type_ in asn1_parsed.items():
            if _strip_and_lower(type_['type']) in ['enumerated', 'bitstring']:
                types.append(_prepare_enum_context(type_name, type_))
            elif _strip_and_lower(type_['type']) == 'choice':
                types.append(_prepare_complex_context(type_name, type_, choice=True))
            elif _strip_and_lower(type_['type']) in ['sequence', 'set']:
                types.append(_prepare_complex_context(type_name, type_, sequence=True))
            elif _strip_and_lower(type_['type']) in ['sequenceof', 'setof']:
                types.append(_prepare_complex_context(type_name, type_,
                                                      sequence=True, list_=True))
            else:
                raise NotImplementedError(f'Unsupported type {type_["type"]}')
        return types

    @staticmethod
    def _generate(template, context, op_file):
        with open(op_file, 'a', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
            code_as_string = chevron.render(inp.read(), context, partials_path=str(TEMPLATES_PATH))
            op.write(code_as_string)
            print(f'Generated: {op_file}')
            return op_file

def _strip_and_lower(s):
    return s.replace(' ', '').lower()


def _prepare_complex_context(type_name, type_, choice=False, sequence=False,
                             list_=False):
    def member(member_):
        member_type = Asn1Type.TypeMap.get(member_['type'], None)
        member_type = member_type or Asn1Type.TypeMap.get(_strip_and_lower(member_['type']), None)
        member_type = member_type.Hint if member_type is not None else member_['type']
        member_name = member_['name'] if 'name' in member_ else member_['type']
        return {
            'name': _fix_name(member_name),
            'type': member_type
        }

    if list_:
        members = [member(type_['element'])]
    else:
        members = [member(_) for _ in type_['members']]

    return {
        'choice': choice,
        'sequence': sequence,
        'list': list_,
        'name': _fix_name(type_name),
        'members': members
    }


def _prepare_enum_context(type_name, type_):
    # For enum types use 'values', for bitstring use 'named-bits'
    values = type_['values'] if 'values' in type_ else type_['named-bits']
    return {
        'enum': True,
        'name': _fix_name(type_name),
        'values': [
            {
                'name': _fix_name(_[0]),
                'value': _[1]
            }
            for _ in values
        ]
    }


def _fix_name(name):
    name = f'{name}_' if keyword.iskeyword(name) else name
    name = name.replace('-', '_')
    return name


@attrs.define(auto_attribs=True)
class _Parser:
    """
    Parses the asn.1 files using asn1tools and prepares a mapping of type names
    to their definitions
    """
    asn1_files: list[Path]
    parsed_types: dict = attrs.field(init=False)
    in_spec: dict = attrs.field(init=False)

    def parse(self):
        self.parsed_types = {}
        self.in_spec = asn1tools.parse_files(self.asn1_files)

        for _, module in self.in_spec.items():
            for type_name, type_ in module['types'].items():
                self.add_type(type_name, type_)

        return self.parsed_types


    def find_type_in_spec(self, type_name):
        if _strip_and_lower(type_name) not in BASIC_TYPES:
            for _, module in self.in_spec.items():
                if type_name in module['types']:
                    return module['types'][type_name]

    def add_type(self, type_name, type_):
        """
        Resolves the type and adds it to the parsed_types dictionary.
        """
        if type_name in self.parsed_types or _strip_and_lower(type_name) in BASIC_TYPES:
            # Type already added or basic types, no processing needed
            return

        if type_ is None:
            LOG.warning("Type %s not found in specification, likely an inline type which is not supported now", type_name)
            return

        if _strip_and_lower(type_['type']) == 'sequenceof':
            # SEQUENCE OF has special handling
            type_name_1 = type_['element']['type']
            type_1 = self.find_type_in_spec(type_name_1)
            self.add_type(type_name_1, type_1)
        elif _strip_and_lower(type_['type']) not in ['enumerated', 'bitstring']:
            for member in type_['members']:
                type_name_1 = member['type']
                type_1 = self.find_type_in_spec(type_name_1)
                self.add_type(type_name_1, type_1)

        self.parsed_types[type_name] = type_