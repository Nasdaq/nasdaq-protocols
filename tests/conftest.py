import os
import pytest


@pytest.fixture(scope='function')
def tmp_file_writer(tmp_path):
    """
    Fixture that returns a file writer.

    The returned filewriter can be called with a string to write to a temporary file.
    The filename is returned and the file is deleted after the test.
    """
    tmp_xml_file = os.path.join(tmp_path, 'test.xml')

    def write_file(data):

        with open(tmp_xml_file, 'w') as file:
            file.write(data)
        return tmp_xml_file

    yield write_file

    os.remove(tmp_xml_file)
