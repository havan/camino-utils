const { Web3 } = require('web3');
const fs = require('fs');

// Initialize Web3
const web3 = new Web3("https://api.camino.network/ext/bc/C/rpc");

let blockNum = 0;
const CONCURRENCY_LIMIT = 30; // Adjust this to your preference

let addresses = {};

let fromAddresses = {};

let processedBlocks = 0;

let blk_number = ''

const processBlock = async (blockNumber) => {
  try {
    let block = await web3.eth.getBlock(blockNumber, true);
    if (!block || !block.transactions) {
      //console.log('block', block.number, 'has no transactions');
      return;
    }

    //console.log('block', block.number, 'transactions', block.transactions.length);

    for (let tx of block.transactions) {
      //console.log(tx)
      if (parseInt(tx.value) > 0) {
        //console.log("Address added", tx.to)
        if (tx.to) {
          addresses[tx.to] = true;
        }
        if (tx.from) {
          fromAddresses[tx.from] = true;
        }
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
    blk_number = blockNumber
    process.stdout.write(`\rProcessed blocks: ${processedBlocks} (block ${blockNumber})`);
  }  
};

let run = async () => {
  let positiveAddresses = [];

  try {
    // Fetch block number for latest block
    const latestBlock = await web3.eth.getBlockNumber();

    // Create an array of promises for each block to be processed
    let promises = [];
    for (let i = blockNum; i <= latestBlock; i++) {
      promises.push(processBlock(i));

      if (promises.length >= CONCURRENCY_LIMIT || i === latestBlock) {
        let results = await Promise.all(promises);
        if (results.includes('unfinalized')) {
          console.log('\nEncountered unfinalized block. Stopping.');
          break;
        }
        promises = [];
      }
    }
    
    // console.log()
    // console.log("------------------------- ADDRESSES -------------------------")
    // console.log(addresses)

    for (let address in addresses) {
      if (address) {
        let balance = await web3.eth.getBalance(address);
        if (parseInt(balance) > 0) {
          //console.log('Positive balanced address found:', address);
          positiveAddresses.push(address);
        }
      }
    }

    // console.log()
    // console.log("------------------------- POSITIVE BALANCE ADDRESSES -------------------------")
    // console.log(positiveAddresses)

    // Write all collected addresses to a file
    fs.writeFileSync('allAddresses.txt', Object.keys(addresses).join('\n'));
    console.log('All "to" addresses have been saved to allAddresses.txt');

    // Write all collected fromAddresses to a file
    fs.writeFileSync('allFromAddresses.txt', Object.keys(fromAddresses).join('\n'));
    console.log('All "from" addresses have been saved to allFromAddresses.txt');

    // Write positive balance addresses to a different file
    fs.writeFileSync('positiveBalanceAddresses.txt', positiveAddresses.join('\n'));
    console.log('Positive balance addresses have been saved to positiveBalanceAddresses.txt');

    console.log(`Last block number: ${blk_number}`)
  } catch (err) {
    console.error('An error occurred:', err);
  }
};

run();
