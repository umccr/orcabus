#!/usr/bin/env bash

set -euo pipefail

: '
Quick shell script to perform the following tasks

1. Check if "uv" is installed, if not, install it
2. Create a virtual environment
3. Install the required dependencies into the virtual environment
4. Add the python script into the virtual env bin directory
5. Create an alias for the script to be placed in the users .rc file
'

# Globals
DATA_SHARING_INSTALL_VENV="${HOME}/.local/data-sharing-cli-venv"

# Get this directory
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if "uv" is installed
if ! command -v uv &> /dev/null; then
    echo "uv could not be found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv is already installed"
fi

# Create a virtual environment
uv venv --python '==3.12' --allow-existing "${DATA_SHARING_INSTALL_VENV}"

# Activate the virtual environment
source "${DATA_SHARING_INSTALL_VENV}/bin/activate"

# Install the required dependencies into the virtual environment
# Pretty 'meh' about versions here, but I guess we can always update them later
uv pip install --quiet \
  pandas \
  pandera \
  docopt \
  requests \
  boto3

# Copy the python script into the virtual environment bin directory
cp "${THIS_DIR}/data-sharing-tool.py" "${DATA_SHARING_INSTALL_VENV}/bin/data-sharing-tool"
chmod +x "${DATA_SHARING_INSTALL_VENV}/bin/data-sharing-tool"

# Get user's shell
SHELL="$(basename "${SHELL}")"

# Create an alias for the script to be placed in the users .rc file
if ! grep -q "alias data-sharing-tool" "${HOME}/.${SHELL}rc"; then
    echo "alias data-sharing-tool='${DATA_SHARING_INSTALL_VENV}/bin/python3 ${DATA_SHARING_INSTALL_VENV}/bin/data-sharing-tool'" >> "${HOME}/.${SHELL}rc"
    echo "Alias 'data-sharing-tool' added to .${SHELL}rc, please restart your terminal or run 'source ~/.${SHELL}rc' to use the alias."
else
    echo "Alias already exists in .${SHELL}rc"
fi