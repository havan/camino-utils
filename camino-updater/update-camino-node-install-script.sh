#!/bin/bash

# A script to check for latest version of camino-node and install it via install script
# Prerquisites for this script:
#  - sudo privilege (passwordless sudo if you want to use it from cron)
#  - jq command installed
#  - this script should be in the same directory where the camino-node-installer.sh is located
#    (script will download installer script if it does exist)


if ! command -v jq &> /dev/null
then
    echo "jq command could not be found"
    echo 'please install jq (on Ubuntu run "apt install jq"'
    exit 1
fi

INSTALL_SCRIPT="camino-node-installer.sh"
INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/chain4travel/camino-docs/c4t/scripts/camino-node-installer.sh"
LATEST_RELEASE_URL="https://api.github.com/repos/chain4travel/camino-node/releases/latest"

# Get latest released version with "latest" tag
echo -n "Checking latest release..."
export LATEST_VERSION=$(wget -q -O - $LATEST_RELEASE_URL \
      | grep tag_name \
      | grep -v "rc\|alpha" \
      | sed 's/.*: "\(.*\)".*/\1/' \
      | head -n 1)

echo " latest camino-node version is: $LATEST_VERSION"

# Get running camino-node's version
echo -n "Getting current running node version..."

# Check if have the current version
if [ -z "$LATEST_VERSION" ]
then 
    echo "ERROR: Can not get the latest version. Exiting..."
    exit 2
fi

export CURRENT_VERSION=$(curl -s -X POST --data '{
    "jsonrpc":"2.0",
    "id"     :1,
    "method" :"info.getNodeVersion"
}' -H 'content-type:application/json;' 127.0.0.1:9650/ext/info | jq  -r ".result.gitVersion")

echo " current running camino-node version is: $CURRENT_VERSION"

# Check if have the current version
if [ -z "$CURRENT_VERSION" ]
then 
    echo "ERROR: Can not get the current running version. Exiting..."
    exit 3
fi

# Do the update if the version does not match the latest version
if [ "$LATEST_VERSION" != "$CURRENT_VERSION" ]
then
    # Get the this scripts path
    export SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )"; cd .. && pwd )

    # Change directory
    cd $SCRIPT_PATH

    # Check if the install script exist and download if not
    if [[ -f "$INSTALL_SCRIPT" ]]; then
        echo "Found install script"
    else
        echo "Install script does not exist. Downloading latest from $INSTALL_SCRIPT_URL"
        wget -nd -m $INSTALL_SCRIPT_URL
        chmod 755 $INSTALL_SCRIPT
    fi
    echo "Using install script at: $SCRIPT_PATH/$INSTALL_SCRIPT"

    # Start the update
    echo "Current Node version ($CURRENT_VERSION) is NOT the latest ($LATEST_VERSION)"
    echo "Updating camino-node..."
    echo "Stopping camino-node service..."
    sudo systemctl stop camino-node
    echo "Running auto install script..."
    INSTALL_COMMAND="$SCRIPT_PATH/camino-node-installer.sh --version $LATEST_VERSION"
    echo "command: $INSTALL_COMMAND"
    $INSTALL_COMMAND
else
    echo "Current node version ($CURRENT_VERSION) is the latest ($LATEST_VERSION). Skipping..."
fi
echo "FINISHED."

