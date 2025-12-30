#!/usr/bin/env bash

set -e

# Default values
PYTHON_VERSION="3.10"
DESCRIPTION="A new Python project"
AUTHOR_NAME=""
AUTHOR_EMAIL=""


usage() {
    echo "Usage: $(basename $0) <project_name> <author_name> <author_email> [--python-version <version>] [--description <desc>]"
    exit 1
}

parse_args() {
    if [[ $# -lt 3 ]]; then
        usage
    fi
    PROJECT_NAME="$1"
    shift
    AUTHOR_NAME="$1"
    shift
    AUTHOR_EMAIL="$1"
    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --description)
                DESCRIPTION="$2"
                shift 2
                ;;
            *)
                usage
                ;;
        esac
    done

    [[ -z "$PROJECT_NAME" ]] && { echo "Project name is required!"; exit 1; }
    [[ -z "$AUTHOR_NAME" ]] && { echo "Author name is required!"; exit 1; }
    [[ -z "$AUTHOR_EMAIL" ]] && { echo "Author email is required!"; exit 1; }

    echo "Creating project '$PROJECT_NAME' with author '$AUTHOR_NAME <$AUTHOR_EMAIL>'"
    echo ""

    PACKAGE_NAME="${PROJECT_NAME//-/_}"
}

create_project_structure() {
    [[ -d "$PROJECT_NAME" ]] && { echo "Directory '$PROJECT_NAME' already exists!"; exit 1; }

    mkdir -p "$PROJECT_NAME/src/$PACKAGE_NAME"
    mkdir -p "$PROJECT_NAME/tests"
    mkdir -p "$PROJECT_NAME/docs"

    # Create empty files
    echo "" > "$PROJECT_NAME/src/$PACKAGE_NAME/__init__.py"
    echo "# new-project: add dependencies here" > "$PROJECT_NAME/requirements.txt"
    echo "# new-project: add data files here" > "$PROJECT_NAME/MANIFEST.in"
}

create_gitignore() {
    cat > "$PROJECT_NAME/.gitignore" <<EOF
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*\$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
env.bak/
venv.bak/

# Pytest
.pytest_cache/

# VS Code
.vscode/

# mypy
.mypy_cache/

# Coverage
.coverage
htmlcov/
cov_html/
cov.xml

# Sphinx
docs/_build/

# Jupyter Notebook
.ipynb_checkpoints

# Mac
.DS_Store
EOF
}

create_tox_ini() {
    cat > "$PROJECT_NAME/tox.ini" <<EOF
[tox]
requires =
    tox>4
    virtualenv>20.2
env_list =
    test
    lint
    flake
    build
    doc

[testenv:lint]
description = Run pylint
deps = pylint
commands = pylint --fail-under=10.0 "--ignore-patterns=.*egg-info.*,.*test.*" src/*

[testenv:flake]
description = Run flake8
deps = flake8
commands = flake8

[testenv:test]
description = Run pytest
deps =
    pytest
    pytest-asyncio
    pytest-sugar
    pytest-cov
    pytest-timeout
commands = pytest \\
    -vv \\
    --timeout=120 \\
    --junitxml=pytest.xml \\
    --cov-config=.coveragerc \\
    --cov=src \\
    --cov-report html:cov_html \\
    --cov-report xml:cov.xml \\
    --cov-fail-under=97  # Locking down the current cov percent as baseline

[testenv:build]
description = Build package
deps = build
commands = python -m build

[testenv:doc]
description = Build documenation
deps = sphinx
commands = make html
change_dir = docs
allowlist_externals = make

[flake8]
exclude =
    .git,
    .tox,
    venv,
    __pycache__,
    tests,
    build,
    dist
max-complexity = 10
max-line-length = 120
per-file-ignores =
EOF
}

create_mit_license() {
    YEAR=$(date +%Y)
    CPR="Copyright (c) ${YEAR}"
    [[ -n "$AUTHOR_NAME" ]] && CPR+=" ${AUTHOR_NAME}"
    cat > "$PROJECT_NAME/docs/LICENSE.rst" <<EOF
MIT License
===========

${CPR}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
}

create_pyproject_toml() {
    cat > "$PROJECT_NAME/pyproject.toml" <<EOF
[build-system]
requires = ["setuptools>=64", "setuptools_scm[toml]>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "$PROJECT_NAME"
description = "$DESCRIPTION"
license-files = ["docs/LICENSE.rst"]
requires-python = ">= $PYTHON_VERSION"
classifiers = [
# new-project: add appropriate classifiers
    'Programming Language :: Python :: "$PYTHON_VERSION"',
    'Development Status :: 3 - Alpha',
    'Topic :: Software Development :: Libraries :: Python Modules'
]
authors = [
# new-project: fill in author information
    {name = "$AUTHOR_NAME", email = "$AUTHOR_EMAIL"},
]
readme = "README.md"
dynamic = ["version"]

dependencies = [
# new-project: add your project dependencies here
]

[project.scripts]
# new-project: add your CLI entry point here

[tool.setuptools_scm]
# new-project: adjust if needed

[tool.setuptools.packages.find]
# new-project: adjust if needed
where = ["src"]
include = ["${PACKAGE_NAME}*"]
namespaces = false
EOF
}

create_readme_files() {
    cat > "$PROJECT_NAME/README.md" <<EOF
# $PROJECT_NAME
$DESCRIPTION

## Development
See [docs/README.dev.md](docs/README.dev.md) for development instructions.

EOF

    cat > "$PROJECT_NAME/docs/README.dev.md" <<EOF
# Development Guide

## Build
This project uses 'tox' to drive the build process. To get started, install tox if you haven't already:
https://tox.wiki/en/latest/installation.html

Once tox is installed, you can run the following commands from within the '$PROJECT_NAME' directory:
\`\`\`sh
cd "$PROJECT_NAME"
tox r            # Run the full chain.
tox -e lint      # Run linter
tox -e flake     # Run flake8 checks
tox -e test      # Run tests with pytest
tox -e build     # Build the package
tox -e doc       # Build the documentation
\`\`\`

The built distributions will be located in the 'dist/' directory.

## Virtual Environment
It is recommended to use a virtual environment for development. You can create one using:
\`\`\`sh
python -m venv venv
source venv/bin/activate
\`\`\`

## PyCharm
To load the project in PyCharm:
1. Open PyCharm and select "Open".
2. Navigate to the '$PROJECT_NAME' directory and open it.

### Selecting the Interpreter
If you're using PyCharm, you can set the project interpreter to the virtual environment created above.

EOF
}

create_rc_files() {
    cat > "$PROJECT_NAME/.coveragerc" <<EOF
# new-project: adjust coverage settings as needed
[run]
concurrency = multiprocessing
parallel = true
sigterm = true
omit =
EOF

    cat > "$PROJECT_NAME/.pylintrc" <<EOF
# new-project: adjust pylint settings as needed
[FORMAT]
max-line-length=180
class-naming-style=PascalCase
attr-naming-style=any

[MASTER]
disable=
    C0114, #missing-module-docstring
    C0115, #missing-class-docstring
    C0116, #missing-function-docstring
    R0903, #too-few-public-methods
EOF
}

main() {
    parse_args "$@"
    create_project_structure
    create_gitignore
    create_tox_ini
    create_pyproject_toml
    create_mit_license
    create_readme_files
    create_rc_files

# Project creation complete
    cat <<EOF
Project '$PROJECT_NAME' created successfully!


Next steps:
1. grep for 'new-project' in the created files to find placeholders to fill in.
2. Implement your project code in 'src/$PACKAGE_NAME/'.
3. Add your tests in the 'tests/' directory.
4. Update the 'docs/' directory with your project documentation.

EOF
}

main "$@"
