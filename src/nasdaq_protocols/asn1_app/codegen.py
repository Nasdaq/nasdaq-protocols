import os
import logging
import shutil
from importlib import resources
from pathlib import Path

import attrs
import chevron
import click

from . import templates


__all__ = [
    'generate_soup_app'
]
TEMPLATES_PATH = resources.files(templates)
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
        context = {
            'app_name': self.app_name,
            'pdu_name': self.pdu,
            'package_name': self.package_name,
            'spec': {
                'name': self.app_name,
                'capitalised_name': self.app_name.capitalize()
            },
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
    def _generate(template, context, op_file):
        with open(op_file, 'a', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
            code_as_string = chevron.render(inp.read(), context, partials_path=str(TEMPLATES_PATH))
            op.write(code_as_string)
            print(f'Generated: {op_file}')
            return op_file


@click.command()
@click.option('--asn1-files-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('--app-name', type=click.STRING)
@click.option('--pdu-name', type=click.STRING)
@click.option('--prefix', type=click.STRING, default='')
@click.option('--op-dir', type=click.Path(exists=True, writable=True))
@click.option('--package-name', type=click.STRING)
@click.option('--init-file/--no-init-file', show_default=True, default=True)
def generate_soup_app(asn1_files_dir, app_name, pdu_name, prefix, op_dir, package_name, init_file):
    generator = Ans1Generator(
        asn1_files_dir,
        app_name,
        pdu_name,
        op_dir,
        template='ans1_soup_app.mustache',
        prefix=prefix,
        package_name=package_name,
        generate_init_file=init_file
    )
    generator.generate()
