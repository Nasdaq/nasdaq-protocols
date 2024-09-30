from importlib import resources
import os

import chevron
import click
from nasdaq_protocols.common.message import Parser, Generator, templates


__all__ = [
    'generate'
]
TEMPLATES_PATH = resources.files(templates)


@click.command()
@click.option('--spec-file', type=click.Path(exists=True))
@click.option('--app-name', type=click.STRING)
@click.option('--prefix', type=click.STRING, default='')
@click.option('--op-dir', type=click.Path(exists=True, writable=True))
@click.option('--override-messages/--no-override-messages', show_default=True, default=True)
@click.option('--init-file/--no-init-file', show_default=True, default=True)
def generate(spec_file, app_name, prefix, op_dir, override_messages, init_file):
    context = {
        'record_type': 'Record',
    }
    generator = Generator(
        Parser.parse(spec_file, override_messages=override_messages),
        'itch',
        app_name,
        op_dir,
        'message_ouch_itch.mustache',
        prefix,
        generate_init_file=init_file
    )
    generator.generate(extra_context=context)


@click.command()
@click.option('--op-dir', type=click.Path(exists=True, writable=True))
@click.option('--app-name', type=click.STRING)
@click.option('--package', type=click.STRING)
def generate_itch_tools(op_dir, app_name, package):
    op_file = os.path.join(op_dir, f'itch_{app_name}_tools.py')
    template = os.path.join(str(TEMPLATES_PATH), 'itch_tail.mustache')
    with open(op_file, 'w', encoding='utf-8') as op, open(template, 'r', encoding='utf-8') as inp:
        context = {
            'package': package,
            'app': app_name,
        }
        code_as_string = chevron.render(inp.read(), context, partials_path=str(TEMPLATES_PATH))
        op.write(code_as_string)
        print(f'Generated: {op_file}')
