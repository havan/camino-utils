const { Web3 } = require('web3');
const fs = require('fs');
const PQueue = require('p-queue').default;

// Initialize Web3
const web3 = new Web3("https://api.camino.network/ext/bc/C/rpc");

let blockStart = 0;
let blockEnd = null;  // Set to null to go to the last block if not specified

const CONCURRENCY_LIMIT = 50; // Adjust this to your preference

let transactions = [];

let processedBlocks = 0;

let blk_number = '';

const processBlock = async (blockNumber) => {
  try {
    let block = await web3.eth.getBlock(blockNumber, true);
    if (!block || !block.transactions) {
      return;
    }

    const receiptPromises = block.transactions.map(tx => web3.eth.getTransactionReceipt(tx.hash));
    const receipts = await Promise.all(receiptPromises);

    for (let i = 0; i < block.transactions.length; i++) {
      let tx = block.transactions[i];
      let receipt = receipts[i];
      if (receipt) {
        let gasPrice = web3.utils.toBigInt(tx.gasPrice);
        let gasUsed = web3.utils.toBigInt(receipt.gasUsed);
        let txnFee = gasPrice * gasUsed;

        // Convert gasPrice to Gwei
        let gasPriceGwei = web3.utils.fromWei(gasPrice.toString(), 'gwei');

        // Convert txnFee to ETH
        let txnFeeEth = web3.utils.fromWei(txnFee.toString(), 'ether');

        transactions.push({
          txn_id: tx.hash,
          gas_price_gwei: parseFloat(gasPriceGwei),
          gas_used: gasUsed.toString(),
          txn_fee_eth: parseFloat(txnFeeEth)
        });
      }
    }
  } catch (err) {
    if (err.message.includes('cannot query unfinalized data')) {
      console.error(`\nBlock ${blockNumber} is not finalized yet. Skipping.`);
      return 'unfinalized';
    } else {
      console.error(`\nError processing block ${blockNumber}:`, err);
      return 'error';
    }
  } finally {
    processedBlocks++;
    blk_number = blockNumber;
    process.stdout.write(`\rProcessed blocks: ${processedBlocks} (block ${blockNumber})`);
  }
};

let run = async () => {
  try {
    // Fetch block number for latest block if blockEnd is not specified
    if (blockEnd === null) {
      blockEnd = await web3.eth.getBlockNumber();
    }

    const queue = new PQueue({ concurrency: CONCURRENCY_LIMIT });

    for (let i = blockStart; i <= blockEnd; i++) {
      queue.add(() => processBlock(i));
    }

    await queue.onIdle();

    // Calculate statistics
    let totalGasPrice = 0;
    let totalTxnFee = 0;
    let minGasPrice = Number.MAX_VALUE;
    let maxGasPrice = 0;
    let minTxnFee = Number.MAX_VALUE;
    let maxTxnFee = 0;

    transactions.forEach(tx => {
      totalGasPrice += tx.gas_price_gwei;
      totalTxnFee += tx.txn_fee_eth;
      if (tx.gas_price_gwei < minGasPrice) minGasPrice = tx.gas_price_gwei;
      if (tx.gas_price_gwei > maxGasPrice) maxGasPrice = tx.gas_price_gwei;
      if (tx.txn_fee_eth < minTxnFee) minTxnFee = tx.txn_fee_eth;
      if (tx.txn_fee_eth > maxTxnFee) maxTxnFee = tx.txn_fee_eth;
    });

    const avgGasPrice = totalGasPrice / transactions.length;
    const avgTxnFee = totalTxnFee / transactions.length;

    const statistics = {
      avg_gas_price_gwei: avgGasPrice,
      min_gas_price_gwei: minGasPrice,
      max_gas_price_gwei: maxGasPrice,
      avg_txn_fee_eth: avgTxnFee,
      min_txn_fee_eth: minTxnFee,
      max_txn_fee_eth: maxTxnFee
    };

    // Sort transactions by txn_fee_eth and get the top 100
    const top100Transactions = transactions
      .sort((a, b) => b.txn_fee_eth - a.txn_fee_eth)
      .slice(0, 100);

    fs.writeFileSync('transactions.json', JSON.stringify(transactions, null, 2));
    console.log('Transaction details have been saved to transactions.json');

    fs.writeFileSync('statistics.json', JSON.stringify(statistics, null, 2));
    console.log('Statistics have been saved to statistics.json');

    fs.writeFileSync('top100Transactions.json', JSON.stringify(top100Transactions, null, 2));
    console.log('Top 100 transactions have been saved to top100Transactions.json');

    console.log(`Last block number: ${blk_number}`);
  } catch (err) {
    console.error('An error occurred:', err);
  }
};

run();
