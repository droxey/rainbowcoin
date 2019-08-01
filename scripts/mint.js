const HDWalletProvider = require("truffle-hdwallet-provider");
const web3 = require('web3');


const MNEMONIC = process.env.MNEMONIC;
const INFURA_KEY = process.env.INFURA_KEY;
const NFT_CONTRACT_ADDRESS = process.env.NFT_CONTRACT_ADDRESS;
const OWNER_ADDRESS = process.env.OWNER_ADDRESS;
const NETWORK = process.env.NETWORK;

if (!MNEMONIC || !INFURA_KEY || !OWNER_ADDRESS || !NETWORK) {
    console.error("Please set a mnemonic, infura key, owner, network, and contract address.")
    return
}

const START_COIN = 2342;
const COINS_TO_MINT = 1;
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
    const provider = new HDWalletProvider(MNEMONIC, `https://${NETWORK}.infura.io/v3/${INFURA_KEY}`);
    const web3Instance = new web3(provider);

    if (NFT_CONTRACT_ADDRESS) {
        const nftContract = new web3Instance.eth.Contract(NFT_ABI, NFT_CONTRACT_ADDRESS, { gasLimit: "1000000" });

        for (var tokenId = START_COIN; tokenId < (START_COIN + COINS_TO_MINT); tokenId++) {
          const result = await nftContract.methods.mintTo(OWNER_ADDRESS, tokenId).send({
            from: OWNER_ADDRESS
          });

          console.log("[" + result.transactionHash + "]", "Minted RainbowCoin #" + tokenId + " at", new Date().toTimeString());
        }

        console.log("Minting complete!", COINS_TO_MINT, "coins minted.");
    }
}

main();

