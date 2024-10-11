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
    app_name: str
    op_dir: str
    prefix: str = ''
    generate_init_file: bool = False
    _init_file: str = None
    _module_prefix: str = None
    _context: dict = None

    def __attrs_post_init__(self):
        prefix = f'{self.prefix}_' if self.prefix else ''
        self._module_prefix = f'{prefix}fix_{self.app_name}'
        self._init_file = os.path.join(self.op_dir, '__init__.py')
        Path(self.op_dir).mkdir(parents=True, exist_ok=True)
        self._prepare_context()

    def _prepare_context(self):
        self._context = self.definitions.get_codegen_context() | {
            'module_prefix': self._module_prefix,
            'app_name': self.app_name,
        }

    def generate(self):
        files = ['fields', 'groups', 'bodies', 'messages']
        generated_modules = []
        generated_files = []
        # Generate the modules
        for file in files:
            module_name = f'{self._module_prefix}_{file}'
            generated_file = os.path.join(self.op_dir, f'{module_name}.py')
            Generator._generate(
                self._context,
                os.path.join(str(TEMPLATES_PATH), f'{file}.mustache'),
                generated_file
            )
            generated_modules.append(module_name)
            generated_files.append(generated_file)

        # Generate the app module
        Generator._generate(
            self._context,
            os.path.join(str(TEMPLATES_PATH), 'app.mustache'),
            os.path.join(self.op_dir, 'app.py')
        )
        generated_modules.append('app')
        generated_files.append(os.path.join(self.op_dir, 'app.py'))

        # Generate the __init__.py file
        if self.generate_init_file:
            context = {
                'app_name': self.app_name,
                'client_session': self._context['client_session'],
                'modules': [
                    {'name': module} for module in generated_modules
                ]
            }
            Generator._generate(
                context,
                os.path.join(str(TEMPLATES_PATH), 'init.mustache'),
                self._init_file
            )
            generated_files.append(self._init_file)
        return generated_files

    @staticmethod
    def _generate(context, template, op_file):
        with open(op_file, 'a', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
            code_as_string = chevron.render(inp.read(), context, partials_path=str(TEMPLATES_PATH))
            op.write(code_as_string)
            print(f'Generated: {op_file}')
