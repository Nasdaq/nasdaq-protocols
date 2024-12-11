import click

from nasdaq_protocols.common import Ans1Generator


__all__ = [
    'generate_soup_app'
]


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


