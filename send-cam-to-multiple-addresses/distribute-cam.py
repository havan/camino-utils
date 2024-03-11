#!/bin/env python
#
# Send CAM token to multiple addresses on Camino Network C-Chain
# 
# Author: Ekrem Seren 
#
# MIT License
# 
# Copyright (c) 2024 Ekrem Seren
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# For more information, please visit: https://opensource.org/licenses/MIT

import sys
import json
import yaml
import click
from web3 import Web3
from datetime import datetime

now = datetime.now()
timestamp = datetime.timestamp(now)
txn_log_file = open(f'txn_log_file.{timestamp}.log', 'w')

GAS_PRICE = None
GAS_LIMIT = 21000

def read_config():
    # Load the configuration file
    config_file='config.yaml'
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as ex:
        click.secho(f'Config file {config_file} file not found.', err=True)
        sys.exit(1)
    return config


def set_gas_price(config):
    global GAS_PRICE
    gas_price_gwei = config.get('gas_price', 200)
    GAS_PRICE = gas_price_gwei #* 10^9


@click.group()
@click.version_option()
def cli():
    """Send CAM tokens to multiple addresses"""


@cli.command()
@click.option('--network', metavar='NETWORK', default='columbus', help='Network name in the config file. Default: columbus')
@click.option('--account', metavar='ACCOUNT', required=True, help='Account to use for distribution.')
@click.option('--addresses-file', metavar='ADDR_FILE', required=True, help='Addresses file with addresses and amounts, seperated by space.')
def distribute(network, account, addresses_file):
    """Distribute CAM tokens"""
    
    config = read_config()
    network = get_network(network, config)
    account = get_account(account, config)

    set_gas_price(config)

    rpc_url = network['rpc_url']
    network_id = network['id']
    network_name = network['name']

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    # Ensure w3 is connected
    if not w3.is_connected():
        raise Exception("Failed to connect to Camino Network RPC")

    transfer_list = get_transfers_list(addresses_file)

    account_address = account['address']
    private_key = account['pkey']

    # Convert the address to a checksum address
    account_checksum_address = Web3.to_checksum_address(account_address)
    click.echo(click.style(f'Account checksum address: ') + click.style(f'{account_checksum_address}', fg='bright_magenta'))

    click.echo(f'Logging to file {txn_log_file.name}')

    # Check if we have enough balance
    check_balance(account_checksum_address, transfer_list, w3)
    # Log to txn log file
    grand_total_eth = check_balance(account_checksum_address, transfer_list, w3, file=txn_log_file)

    click.echo(
        f'This will create ' +
        click.style(f'{transfer_list.__len__()} transactions ', fg='bright_red') +
        f'and consume ' +
        click.style(f'{grand_total_eth} CAM ', fg='bright_red')
    )
    
    if not click.confirm(f'Do you want to continue?'):
        click.echo('Aborted!')
        sys.exit(99)

    click.echo(click.style(f'Starting sending {transfer_list.__len__()} transactions...'))
    click.echo(click.style(f'Starting sending {transfer_list.__len__()} transactions...'), file=txn_log_file)

    for address, amount in transfer_list:
        # Convert amount to Wei
        amount_in_wei = w3.to_wei(amount, 'ether')

        address = Web3.to_checksum_address(address)

        tx = {
            'nonce': w3.eth.get_transaction_count(account_checksum_address),
            'to': address,
            'value': amount_in_wei,
            'gas': 25000,
            #'gasPrice': w3.to_wei(GAS_PRICE, 'gwei'),
            'maxFeePerGas': w3.to_wei(GAS_PRICE, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(0, 'gwei'),
            'chainId': network_id,
        }

        # Sign transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print_transfer(address, amount, tx_hash, receipt)
        # Write to log file
        print_transfer(address, amount, tx_hash, receipt, file=txn_log_file)

    click.echo('Finished.')


def check_balance(account_address, transfer_list, w3, file=None):
    # Check for sufficient balance
    
    txn_fee = w3.to_wei(GAS_PRICE, 'gwei') * GAS_LIMIT
    total_tx_fee = sum(txn_fee for _,_ in transfer_list)
    total_tx_fee_eth = w3.from_wei(total_tx_fee, 'ether')
    
    total_amount = sum(w3.to_wei(float(amount), 'ether') for _, amount in transfer_list)
    total_amount_eth = w3.from_wei(total_amount, 'ether')

    balance = w3.eth.get_balance(account_address)
    balance_eth = w3.from_wei(balance, 'ether')

    grand_total = total_tx_fee + total_amount
    grand_total_eth = w3.from_wei(grand_total, 'ether')

    missing = balance - grand_total
    missing_eth = w3.from_wei(abs(missing), 'ether')

    msign = '-' if missing < 0 else '+'

    click.echo(
        f'Balance: ' +
        click.style(f'{balance_eth} CAM', fg='bright_green') +
        f' Total Amount: ' +
        click.style(f'{total_amount_eth} CAM', fg='bright_yellow') +
        f' Total TX Fee: ' +
        click.style(f'{total_tx_fee_eth} CAM', fg='bright_blue') +
        f' Grand Total: ' +
        click.style(f'{grand_total_eth} CAM', fg='bright_cyan') +
        f' Difference: ' +
        click.style(f'{msign}{missing_eth} CAM', fg='bright_red'),
        file=file
    )

    if balance < grand_total:
        click.echo(click.style('ERROR: Insufficient balance to complete all transactions. Aborting!', fg='bright_red', blink=True, bold=True), file=file)
        sys.exit(3)

    return grand_total_eth


def print_transfer(address, amount, tx_hash, receipt, file=None):
    
    click.echo(
        click.style(f'{address} ', fg='bright_cyan') +
        click.style(f'{amount} ', fg='bright_red') +
        click.style(f'{tx_hash.hex()} ', fg='bright_yellow'),
        nl=False,
        file=file,
    )

    if receipt.status == 1:
        click.echo(click.style(f"SUCCESS", fg='bright_green', bold=True), file=file)
    else:
        click.echo(click.style(f"FAIL", fg='bright_red', bold=True), file=file)


def get_transfers_list(addresses_file):
    addr_file = addresses_file
    transfer_list = []

    try:
        with open(addr_file, 'r') as file:
            for line in file:
                address, amount = line.split()
                transfer_list.append((address, amount))
    except ValueError as ex:
        click.echo(f'Error: addresses file "{addr_file}" is malformed.')
        sys.exit(2)
    
    return transfer_list

def print_network(network, file=None):
    rpc_url = network['rpc_url']
    network_id = network['id']
    network_name = network['name']

    click.echo(
        click.style(f'Using network ') +
        click.style(f'{network_name}', fg='bright_yellow') +
        click.style(f' with ID ') +
        click.style(f'{network_id}', fg='bright_cyan') +
        click.style(f' and RPC URL ') +
        click.style(f'{rpc_url}', fg='bright_green'),
        file=file
    )


def print_account(account, file=None):
    address = account['address']
    pkey = account['pkey']
    click.echo(
        click.style('Using account ') +
        click.style(f'{address}', fg='bright_red'),
        file=file
    )


def get_network(network, config):
    try:
        network = config['networks'][network]
        print_network(network)
        print_network(network, file=txn_log_file)
    except KeyError as ex:
        click.echo(f'Network "{network}" not found in config file', err=True)
        sys.exit(1)
    return network


def get_account(account, config):
    try:
        account_name = account
        account_dict = config['accounts'][account]
        print_account(account_dict)
        print_account(account_dict, file=txn_log_file)
    except KeyError as ex:
        click.echo(f'Account "{account}" not found in config file', err=True)
        sys.exit(1)
    return account_dict


if __name__ == '__main__':
    cli()
