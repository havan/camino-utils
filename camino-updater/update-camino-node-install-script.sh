#!/bin/bash

## A script to check for latest version of camino-node and install it via install script
## Prerquisites for this script:
### 1- sudo privilege
### 2- jq command installed
### 3- this script should be in the same directory where the camino-node-installer.sh is located


echo "Getting latest release"
export LATEST_VERSION=$(wget -q -O - https://api.github.com/repos/chain4travel/camino-node/releases \
      | grep tag_name \
      | grep -v "rc\|alpha" \
      | sed 's/.*: "\(.*\)".*/\1/' \
      | head -n 1)

echo "Latest Camino Node Version: $LATEST_VERSION"

echo "Getting current running node version"

export CURRENT_VERSION=$(curl -X POST --data '{
    "jsonrpc":"2.0",
    "id"     :1,
    "method" :"info.getNodeVersion"
}' -H 'content-type:application/json;' 127.0.0.1:9650/ext/info | jq  -r ".result.gitVersion")

echo "Current Camino Node Version: $LATEST_VERSION"

export SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )"; cd .. && pwd )
echo "Install Script Path: $SCRIPT_PATH/camino-node-installer.sh"

if [ "$LATEST_VERSION" != "$CURRENT_VERSION" ]
then
    echo "Current Node version is not the latest"
    echo "Updating current camino-node..."
    sudo systemctl stop camino-node
    $SCRIPT_PATH/camino-node-installer.sh
else
    echo "Current Node version is the latest"
    echo "DONE"
fi
