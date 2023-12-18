const { Web3 } = require('web3');
const fs = require('fs');

// Initialize Web3
const web3 = new Web3("https://api.camino.network/ext/bc/C/rpc");

let blockNum = 0;

let run = async () => {
  let addresses = {};

  while (true) {
    let blck = blockNum++;
    let block = await web3.eth.getBlock(blck, true); // 'true' to get the full transaction objects
    if (!block) break;

    // Check if the block has transactions
    if (block.transactions && block.transactions.length) {
      console.log('block', blck, 'transactions', block.transactions.length);
      for (let i = 0; i < block.transactions.length; i++) {
        let tx = block.transactions[i];
        if (parseInt(tx.value) > 0) {
          addresses[tx.to] = true;
        }
      }
    } else {
      console.log('block', blck, 'does not contain individual transactions');
    }
  }

  let positiveAddresses = [];
  for (let address in addresses) {
    try {
      let balance = await web3.eth.getBalance(address);
      if (parseInt(balance) > 0) {
        positiveAddresses.push(address);
      }
    } catch (err) {
      console.log(err);
    }
  }
  // Write all collected addresses to a file
  fs.writeFile('allAddresses.txt', Object.keys(addresses).join('\n'), (err) => {
    if (err) throw err;
    console.log('All addresses have been saved to allAddresses.txt');
  });

  // Write positive balance addresses to a different file
  fs.writeFile('positiveAddresses.txt', positiveAddresses.join('\n'), (err) => {
    if (err) throw err;
    console.log('Positive balance addresses have been saved to positiveAddresses.txt');
  });
};

run();
