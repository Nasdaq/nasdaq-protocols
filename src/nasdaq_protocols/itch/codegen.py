import click
from nasdaq_protocols.common.message import Parser, Generator


__all__ = [
    'generate'
]


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.argument('gen_dir', type=click.Path(exists=True, writable=True))
@click.argument('customer', type=click.STRING)
@click.argument('package_name', type=click.STRING)
@click.option('--generate-init-file', is_flag=True, show_default=True, default=True)
def generate(file, gen_dir, customer, package_name, generate_init_file):
    context = {
        'record_type': 'Record',
    }
    generator = Generator(
        Parser.parse(file),
        'itch',
        gen_dir,
        customer,
        package_name,
        'message_ouch_itch.mustache',
        generate_init_file
    )
    generator.generate(extra_context=context)
