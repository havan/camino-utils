#!/bin/env python3

# Retrieves the C-Chain (EVM) balance of an address on Camino Network
#
# Requirenments:
# - web3: run 'pip install web3'

import argparse, requests, sys

try:
    from web3 import Web3
except ModuleNotFoundError:
    print("Error: web3 module not found. Please install it with 'pip install web3'")
    sys.exit(1)

def get_cam_balance(address, provider_url, ncam=False):
    # Connect to the Camino network node
    web3 = Web3(Web3.HTTPProvider(provider_url))
    
    # Check if the connection is successful
    if not web3.is_connected():
        print("Failed to connect to the Camino network")
        return

    # Convert the address to a checksum address
    checksum_address = Web3.to_checksum_address(address)

    # Get the balance
    balance = web3.eth.get_balance(checksum_address)

    if ncam:
        # Return nCAM balance
        return balance
    else:
        # Convert the balance from nCAM to CAM and return
        return web3.from_wei(balance, 'ether')

def main():
    parser = argparse.ArgumentParser(description='Get the C-Chain (EVM) CAM balance of an address on the specified network.')
    parser.add_argument('-a', '--address', type=str, required=True, help='Camino network address to query')
    parser.add_argument('-n', '--network', type=str, choices=['camino', 'columbus', 'kopernikus'], default='camino', help='Network to query')
    parser.add_argument('--nano-camino', action="store_true", help="Return balance in nCAM")
    
    args = parser.parse_args()

    network_urls = {
        'camino': 'https://api.camino.network/ext/bc/C/rpc',
        'columbus': 'https://columbus.camino.network/ext/bc/C/rpc',
        'kopernikus': 'https://kopernikus.camino.network/ext/bc/C/rpc',
    }

    balance = get_cam_balance(args.address, network_urls[args.network], args.nano_camino)
    #print(f"{args.network} CAM balance of {args.address}: {balance} CAM")
    print(f"{balance}")

if __name__ == "__main__":
    main()
