from functools import partial
import logging
import xml.etree.ElementTree as e_tree

from .definitions import (
    Definitions,
    FieldDef,
    Component,
    Field,
    EntryContainer,
    Group,
    Message
)
from .version_types import (
    get_supported_types,
    Version,
    SupportedTypes
)


__all__ = [
    'parse'
]
LOG = logging.getLogger(__name__)


def parse(file: str) -> Definitions:
    tree = e_tree.parse(file)
    root = tree.getroot()

    if root.tag != 'fix':
        raise ValueError('root tag is not fix')

    version_str = f'{root.get("major")}{root.get("minor")}'
    servicepack = int(root.get('servicepack', '0'))
    if servicepack > 0:
        version_str += f'{servicepack}'
    version = int(version_str)

    try:
        version = Version(version)
    except ValueError as v_error:
        raise ValueError(f'Version {version} is not supported') from v_error

    handlers = {
        'fields': partial(_handle_fields, get_supported_types(version)),
        'components': _handle_components,
        'header': _handle_header,
        'trailer': _handle_trailer,
        'messages': _handle_messages
    }
    definitions = Definitions(version)

    for element in list(root)[::-1]:
        handlers[element.tag](definitions, root, element)

    return definitions


def _handle_header(definitions: Definitions, root, element) -> None:
    LOG.debug('parsing <header>')
    for entry in element:
        _handle_entry(definitions, definitions.header, root, entry)


def _handle_trailer(definitions: Definitions, root, element) -> None:
    LOG.debug('parsing <trailer>')
    for entry in element:
        _handle_entry(definitions, definitions.trailer, root, entry)


def _handle_messages(definitions: Definitions, root, element) -> None:
    LOG.debug('parsing <messages>')
    for msg in element:
        message = Message(
            tag=msg.get('msgtype'),
            name=msg.get('name'),
            category=msg.get('msgcat')
        )
        for entry in msg:
            _handle_entry(definitions, message, root, entry)
        definitions.messages.append(message)


def _handle_fields(types: SupportedTypes,
                   definitions: Definitions,
                   _root,
                   element) -> None:
    LOG.debug('parsing <fields>')
    for field in element:

        if field.tag != 'field':
            raise ValueError(f'expected field tag, got {field.tag}')

        values = {v.get('enum'): v.get('description') for v in field.iter('value')}
        name = field.get('name')

        definitions.fields[name] = FieldDef(
            tag=field.get('number'),
            name=name,
            type=types[field.get('type')],
            possible_values=values
        )


def _handle_components(definitions: Definitions, root, element) -> None:
    LOG.debug('parsing <components>')
    for component in element:
        _handle_component(definitions, root, component)


def _handle_component(definitions: Definitions, root, component) -> None:
    LOG.debug('parsing <component>')
    comp_name = component.get('name')
    container = Component(name=comp_name)
    LOG.debug('parsing component: %s', comp_name)
    for entry in component:
        _handle_entry(definitions, container, root, entry)
    definitions.components[comp_name] = container


def _handle_entry(definitions: Definitions, container: EntryContainer, root, entry) -> None:
    entry_name = entry.get('name')
    if entry.tag == 'field':
        LOG.debug('-- adding field %s to container', entry_name)
        if entry_name not in definitions.fields:
            raise ValueError(f'Field definition for {entry_name} not found')
        container.entries.append(Field(
            field=definitions.fields[entry_name],
            required=_is_required(entry)
        ))
    elif entry.tag == 'group':
        container.entries.append(_create_group(definitions, root, entry))
    elif entry.tag == 'component':
        LOG.debug('-- processing component')
        try:
            component = definitions.components[entry_name]
        except KeyError as k_error:
            comp = [x for x in root.findall('./components/component') if x.get('name') == entry_name]
            if len(comp) == 0:
                raise ValueError(f'Component definition for {entry_name} not found') from k_error
            _handle_component(definitions, root, comp[0])
            component = definitions.components[entry_name]
        for component_entry in component.entries:
            container.entries.append(component_entry)


def _create_group(definitions: Definitions, root, element) -> Group:
    LOG.debug('parsing tag <group>')
    group_name = element.get('name')
    group = Group(name=group_name, required=_is_required(element))
    for entry in element:
        _handle_entry(definitions, group, root, entry)
    return group


def _is_required(entry) -> bool:
    return entry.get('required') == 'Y'
