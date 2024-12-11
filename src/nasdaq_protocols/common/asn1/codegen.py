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
    'ENUMERATED',
    'INTEGER',
    'REAL',
    'OCTET STRING',
    'BOOLEAN',
    'NumericString',
    'VisibleString',
    'PrintableString',
    'GraphicString'
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
        asn1_parsed = _parse_asn1(self._asn1_files)
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
            if type_['type'] == 'ENUMERATED':
                types.append(_prepare_enum_context(type_name, type_))
            elif type_['type'] == 'CHOICE':
                types.append(_prepare_complex_context(type_name, type_, choice=True))
            elif type_['type'] == 'SEQUENCE':
                types.append(_prepare_complex_context(type_name, type_, sequence=True))
            elif type_['type'] == 'SEQUENCE OF':
                types.append(_prepare_complex_context(type_name, type_,
                                                      sequence=True, list_=True))
            elif type_['type'] == 'BIT STRING':
                types.append({
                    'bitstring': True,
                    'name': _fix_name(type_name),
                })
        return types

    @staticmethod
    def _generate(template, context, op_file):
        with open(op_file, 'a', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
            code_as_string = chevron.render(inp.read(), context, partials_path=str(TEMPLATES_PATH))
            op.write(code_as_string)
            print(f'Generated: {op_file}')
            return op_file


def _prepare_complex_context(type_name, type_, choice=False, sequence=False,
                             list_=False):
    def member(member_):
        member_type = Asn1Type.TypeMap.get(member_['type'], None)
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
    return {
        'enum': True,
        'name': _fix_name(type_name),
        'values': [
            {
                'name': _fix_name(_[0]),
                'value': _[1]
            }
            for _ in type_['values']
        ]
    }


def _fix_name(name):
    return f'{name}_' if keyword.iskeyword(name) else name


def _find_type_in_spec(full_spec, type_name):
    if type_name not in BASIC_TYPES:
        for _, module in full_spec.items():
            if type_name in module['types']:
                return module['types'][type_name]


def _add_type(in_specification, op_types, type_name, type_):
    if type_name in op_types or type_name in BASIC_TYPES:
        return

    if type_ is None:
        LOG.warning("Type %s not found in specification, likely an inline type which is not supported now", type_name)
        return

    if type_['type'] == 'SEQUENCE OF':
        type_name_1 = type_['element']['type']
        type_1 = _find_type_in_spec(in_specification, type_name_1)
        _add_type(in_specification, op_types, type_name_1, type_1)
    elif type_['type'] not in ['ENUMERATED', 'BIT STRING']:
        for member in type_['members']:
            type_name_1 = member['type']
            type_1 = _find_type_in_spec(in_specification, type_name_1)
            _add_type(in_specification, op_types, type_name_1, type_1)

    op_types[type_name] = type_


def _parse_asn1(asn1_files):
    specification = asn1tools.parse_files(asn1_files)
    types = {}

    for _, module in specification.items():
        for type_name, type_ in module['types'].items():
            _add_type(specification, types, type_name, type_)

    return types
