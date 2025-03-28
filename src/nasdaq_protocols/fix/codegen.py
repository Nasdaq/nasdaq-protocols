import click
from nasdaq_protocols.fix.parser import parse, Generator


__all__ = [
    'generate'
]


@click.command()
@click.option('--spec-file', type=click.Path(exists=True))
@click.option('--app-name', type=click.STRING)
@click.option('--prefix', type=click.STRING, default='')
@click.option('--op-dir', type=click.Path(exists=True, writable=True))
@click.option('--init-file/--no-init-file', show_default=True, default=True)
@click.option('--fix-version',
              type=click.Choice(['4.2', '4.4', '5.0', '5.0SP2']),
              default='5.0SP2')
def generate(spec_file, app_name, op_dir, prefix, init_file, fix_version):

    try:
        generator = Generator(
            parse(spec_file, fix_version),
            app_name,
            op_dir,
            prefix,
            generate_init_file=init_file
        )
        generator.generate()
    except Exception as e:
        print(f'Error: {e}')
        raise e
