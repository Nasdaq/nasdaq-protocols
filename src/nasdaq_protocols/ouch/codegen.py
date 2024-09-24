import click
from nasdaq_protocols.common.message import Parser, Generator


__all__ = [
    'generate'
]


@click.command()
@click.option('--spec-file', type=click.Path(exists=True))
@click.option('--app-name', type=click.STRING)
@click.option('--prefix', type=click.STRING, default='')
@click.option('--op-dir', type=click.Path(exists=True, writable=True))
@click.option('--override-messages/--no-override-messages', show_default=True, default=True)
@click.option('--init-file/--no-init-file', show_default=True, default=True)
def generate(spec_file, app_name, op_dir, prefix, override_messages, init_file):
    context = {
        'record_type': 'Record',
    }
    generator = Generator(
        Parser.parse(spec_file, override_messages=override_messages),
        'ouch',
        app_name,
        op_dir,
        'message_ouch_itch.mustache',
        prefix,
        generate_init_file=init_file
    )
    generator.generate(extra_context=context)
