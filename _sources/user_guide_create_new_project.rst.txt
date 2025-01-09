.. _user-guide-create-new-project:

Create New Project Guide
========================

This guide will walk you through creating a new python package that contains the message definitions
of the applications you want to use with the nasdaq-protocols.

.. note::

    This guide assumes you have already installed the nasdaq-protocols package. If you have not, please
    refer to the :ref:`installation guide <install-guide>`.


Steps
-----

1. Install `tox` if you have not already done so.

    .. code-block:: bash

        bash$ pip install tox

Refer to the `tox documentation <https://tox.wiki/en/latest/installation.html>`_ for detailed information.

2. Create a new python package structure using the `nasdaq-protocols-create-new-project` command line tool.

        .. code-block:: bash

            bash$ nasdaq-protocols-create-new-project --name <project-name> \
                     --application app:proto [--target-dir <target-dir>]

        Replace `<project-name>` with the name of your project and `<target-dir>` with the directory where you want to
        create the project.

        For example, to create a project named `nasdaq-protocols-messages` in the current directory, with 2 applications `ouch_oe`
        and `itch_feed`, you would run the following command:

        .. code-block:: bash

            bash$ nasdaq-protocols-create-new-project --name nasdaq-protocols-messages \
                    --application ouch_oe:ouch \
                    --application itch_feed:itch

3. The `nasdaq-protocols-create-new-project` command will create a new python package with the following structure:

    For the above example, the following directory structure will be created.

    .. code-block:: bash

        nasdaq-protocols-messages/
        ├── src/
        |    ├── nasdaq_protocols_messages/
        |    │   ├── __init__.py
        |    │   ├── ouch_oe/
        |    │   │   └── ouch_oe.xml
        |    │   └── itch_feed/
        |    │       └── itch_feed.xml
        ├── pyproject.toml
        └── tox.ini

    .. note::
        - **ouch_oe.xml** is the file where you define all the messages for the `ouch_oe` application.
        - **itch_feed.xml** is the file where you define all the messages for the `itch_feed` application.

        The XML file contains the format and guidelines on how to define the messages.

4. Edit the XML files to define the messages for the applications you want to use with the nasdaq-protocols.

5. Build the package

        .. code-block:: bash

            bash$ cd target-dir/nasdaq-protocols-messages
            bash$ tox r

6. The package will be built and stored in the `dist` directory. This can be uploaded to your PyPI repository or
   installed locally.