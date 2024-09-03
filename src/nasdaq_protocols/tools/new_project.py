from importlib import resources
from pathlib import Path

import attrs
import click
import chevron

from . import templates


__all__ = [
    'create'
]
SUPPORTED_PROTOCOLS = ['ouch', 'itch']
TEMPLATES_PATH = resources.files(templates)


@attrs.define(auto_attribs=True)
class AppInfo:
    app_name: str
    app_dir: Path
    app_xml: Path
    proto_name: str


@attrs.define(auto_attribs=True)
class Context:
    project_name: str
    project_src_name: str
    project_module_dir: Path
    target_dir: Path
    pyproject_toml: Path
    tox_ini: Path
    apps: list[AppInfo]


@click.command()
@click.option(
    '--name', '-n', required=True,
    help='Project name'
)
@click.option(
    '--target-dir', '-d', type=click.Path(), required=False, default='.',
    help='Target directory to create the project structure'
)
@click.option(
    '--application', '-a', multiple=True, required=True,
    help=f'''include applications in this project.
    format appname:protocol

    e.g. -a oe:ouch -a md:itch -a fix_oe:fix

    supported protocols: {SUPPORTED_PROTOCOLS}
    '''
)
def create(name, target_dir, application):
    try:
        _validate_applications(application)
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(f'Creating project {name} in {target_dir}')

    target_dir = Path(target_dir) / Path(name)
    project_src_name = name.replace('-', '_')
    context = Context(
        project_name=name,
        project_src_name=project_src_name,
        project_module_dir=Path(target_dir) / Path('src') / Path(project_src_name),
        target_dir=Path(target_dir),
        pyproject_toml=Path(target_dir) / Path('pyproject.toml'),
        tox_ini=Path(target_dir) / Path('tox.ini'),
        apps=[]
    )

    for app_proto in application:
        app_name, proto_name = app_proto.split(':')
        app_dir = context.project_module_dir / Path(app_name)
        app_info = AppInfo(
            app_name=app_name,
            app_dir=app_dir,
            app_xml=app_dir / Path(f'{app_name}.xml'),
            proto_name=proto_name
        )
        app_info.app_dir.mkdir(parents=True, exist_ok=True)
        _write_app_xml(app_info)
        context.apps.append(app_info)
        click.echo(f'Created application directory: {app_dir}')

    Path(context.project_module_dir / Path('__init__.py')).touch()
    _write_pyproject(context)
    _write_tox(context)

    click.echo(f'Created project {name} in {target_dir}')


def _write_app_xml(app_info: AppInfo):
    if app_info.app_xml.exists():
        return

    if app_info.proto_name in ['ouch', 'itch']:
        xml_template = TEMPLATES_PATH / Path('ouch_itch_xml.mustache')
    else:
        raise ValueError(f'Unsupported protocol: {app_info.proto_name}')

    with open(app_info.app_xml, 'w', encoding='utf-8') as op, open(xml_template, 'r', encoding='utf-8') as inp:
        content = chevron.render(inp.read(), attrs.asdict(app_info), partials_path=str(TEMPLATES_PATH))
        op.write(content)


def _write_pyproject(context: Context):
    toml_template = TEMPLATES_PATH / Path('toml.mustache')
    with (open(context.pyproject_toml, 'a', encoding='utf-8') as op,
          open(toml_template, 'r', encoding='utf-8') as inp):
        content = chevron.render(inp.read(), attrs.asdict(context), partials_path=str(TEMPLATES_PATH))
        op.write(content)


def _write_tox(context: Context):
    tox_template = TEMPLATES_PATH / Path('tox.mustache')
    with (open(context.tox_ini, 'a', encoding='utf-8') as op,
          open(tox_template, 'r', encoding='utf-8') as inp):
        content = chevron.render(inp.read(), attrs.asdict(context), partials_path=str(TEMPLATES_PATH))
        op.write(content)


def _validate_applications(applications):
    apps = {}
    for app_proto in applications:
        if ':' not in app_proto:
            raise ValueError(f'Invalid application protocol: {app_proto}, format = appname:protocol')

        app_name, proto_name = app_proto.split(':')
        if app_name in apps:
            raise ValueError(f'Application {app_name} already exists')

        if proto_name not in SUPPORTED_PROTOCOLS:
            raise ValueError(f'Unsupported protocol: {proto_name} for application: {app_name},'
                             f' Supported protocols: {SUPPORTED_PROTOCOLS}')

        apps[app_name] = proto_name
