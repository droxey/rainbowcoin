// [CONFIG] These values are safe to change.
const START_COIN = 19876;
const TOTAL_COINS = 10;
const MINT_RANDOM_COINS = true;
// [/CONFIG] Do not modify anything below this line.


const HDWalletProvider = require("truffle-hdwallet-provider");
const intToRGB = require('int-to-rgb');
const chalk = require('chalk');
const web3 = require('web3');
const log = console.log;
const info = console.info;

// Set these values in your .env file, then
// run `source .env` in your terminal before running this script.
const MNEMONIC = process.env.MNEMONIC;
const INFURA_KEY = process.env.INFURA_KEY;
const NFT_CONTRACT_ADDRESS = process.env.NFT_CONTRACT_ADDRESS;
const OWNER_ADDRESS = process.env.OWNER_ADDRESS;
const NETWORK = process.env.NETWORK;
const MAX_COINS = 16777215;
const CAN_MINT = START_COIN <= MAX_COINS && (START_COIN + TOTAL_COINS) <= MAX_COINS;
const VALIDATION_URL = `https://rinkeby-api.opensea.io/asset/${NFT_CONTRACT_ADDRESS}/`;
const GAS_ERROR = 'Transaction ran out of gas. Please provide more gas';

// Handle missing .env values.
if (!MNEMONIC || !INFURA_KEY || !OWNER_ADDRESS || !NETWORK) {
    log(chalk.red.bold("[ERROR]", "Please set a mnemonic, infura key, owner, network, and contract address. \n\nMinting failed."));
    return
}

// Handle invalid START_COIN / TOTAL_COINS values.
if (!CAN_MINT) {
    log(chalk.red.bold("[ERROR]", `The sum of START_COIN (${START_COIN}) and TOTAL_COINS (${TOTAL_COINS}) must equal an integer between 0 and 16777215.\n\nMinting failed.`));
    return
}

let coinsToMint = [];
if (MINT_RANDOM_COINS) {
    coinsToMint = Array(TOTAL_COINS).fill().map(() => Math.round(Math.random() * MAX_COINS));
}
else {
    coinsToMint = [...range(START_COIN, (START_COIN + TOTAL_COINS))];
}



const NFT_ABI = [{
    "constant": false,
    "inputs": [
      {
        "name": "_to",
        "type": "address"
      },
      {
        "name": "_rgbInt",
        "type": "uint256"
      }
    ],
    "name": "mintTo",
    "outputs": [],
    "payable": false,
    "stateMutability": "nonpayable",
    "type": "function"
}];

async function main() {
    // Connect to the specified provider.
    const provider = new HDWalletProvider(MNEMONIC, `https://${NETWORK}.infura.io/v3/${INFURA_KEY}`);
    const web3Instance = new web3(provider);

    if (NFT_CONTRACT_ADDRESS) {
        // Connect to the contract you created.
        const nftContract = new web3Instance.eth.Contract(NFT_ABI, NFT_CONTRACT_ADDRESS, { gasLimit: "1000000" });

        // Save the date and time we started minting.
        const scriptStartedOn = process.hrtime();
        let didMint = false;

        // Mint the coins!
        log(chalk.green.bold(`\n--- MINTING STARTED ---\n\n`));
        for (var tokenIndex = 0; tokenIndex < coinsToMint.length; tokenIndex++) {
          const tokenId = coinsToMint[tokenIndex];

          await nftContract.methods.mintTo(OWNER_ADDRESS, tokenId).send({
            from: OWNER_ADDRESS
          }).then(result => {
            didMint = true;

            // Log using the same color as the token.
            const rgb = intToRGB(tokenId);
            const rgbText = chalk.rgb(rgb.red, rgb.green, rgb.blue).bold(`${tokenId}`);
            const validationText = chalk.dim(chalk`          {underline Validate}: ${VALIDATION_URL}${tokenId}/validate?force_update=true`);
            const output = chalk`[{green.bold SUCCESS}] ${rgbText} Minted ➡ ${result.transactionHash}\n${validationText}\n`;
            log(chalk.white(output));
          }).catch(error => {
            // Handle errors.
            const isGasError = error.message.indexOf(GAS_ERROR) !== -1;
            if (isGasError) {
              log(chalk.yellow.bold(`[WARNING] ${tokenId} has already been minted.\n`));
            }
            else {
              log(chalk.red.bold(`[ERROR] ${error.message}\n`));
              process.exit(1);
            }
          });
        }

        if (didMint) {
          // Log when the minting is complete, then exit the script.
          const scriptEndedOn = process.hrtime(scriptStartedOn);
          log(chalk.green.bold(`--- MINTING COMPLETE ---\n\n${TOTAL_COINS} coins minted.`));
          info('Execution time (hr): %ds %dms', scriptEndedOn[0], scriptEndedOn[1] / 1000000);

          process.exit(0);
        }
    }
}

function* range(start, end) {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}

function randomInt(low, high) {
  return Math.floor(Math.random() * (high - low) + low);
}

main();
