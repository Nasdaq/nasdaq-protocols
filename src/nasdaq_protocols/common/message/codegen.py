import os
from importlib import resources
from pathlib import Path

import attrs
import chevron
from .parser import Definitions
from . import templates


__all__ = [
    'Generator'
]
TEMPLATES_PATH = resources.files(templates)


@attrs.define(auto_attribs=True)
class Generator:
    definitions: Definitions
    impl: str
    op_dir: str
    customer: str
    package_name: str
    template: str
    generate_init_file: bool = False
    _op_file: str = None
    _module_name: str = None
    _init_file: str = None

    def __attrs_post_init__(self):
        self._module_name = f'{self.customer}_{self.impl}_messages'
        self._op_file = os.path.join(self.op_dir, f'{self._module_name}.py')
        self._init_file = os.path.join(self.op_dir, '__init__.py')
        self.template = self.template if self.template.endswith('.mustache') else f'{self.template}.mustache'
        self.template = os.path.join(str(TEMPLATES_PATH), self.template)
        Path(self.op_dir).mkdir(parents=True, exist_ok=True)

    def generate(self, extra_context=None):
        generated_files = []
        context = self.definitions.get_codegen_context()
        context.update({'impl': self.impl})
        context.update(extra_context or {})

        Generator._generate(self.template, context, self._op_file)
        generated_files.append(self._op_file)

        if self.generate_init_file:
            context = {
                'modules': [
                    {'name': self._module_name}
                ]
            }
            init_template = os.path.join(str(TEMPLATES_PATH), 'init.mustache')
            Generator._generate(init_template, context, self._init_file)
            generated_files.append(self._init_file)

        return generated_files

    @staticmethod
    def _generate(template, context, op_file):
        with open(op_file, 'w', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
            op.write(chevron.render(inp, context, partials_path=str(TEMPLATES_PATH)))
            print(f'Generated {op_file}')
