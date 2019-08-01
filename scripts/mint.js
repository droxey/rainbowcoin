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

    // Black, Red, OrangeYellow, Green, Blue, Purple, White
    const coinsToMint = [0, 15874875, 16765264, 5234049, 3582698, 11444714, 16777215];

    if (NFT_CONTRACT_ADDRESS) {
        const nftContract = new web3Instance.eth.Contract(NFT_ABI, NFT_CONTRACT_ADDRESS, { gasLimit: "1000000" });

        for (var i = 0; i < coinsToMint.length; i++) {
          const result = await nftContract.methods.mintTo(OWNER_ADDRESS, coinsToMint[i]).send({
            from: OWNER_ADDRESS
          });

          console.log("Minted RainbowCoin #" + coinsToMint[i] + "! Transaction:", result.transactionHash);
        }

        console.log("Minting complete!", coinsToMint.length, "coins minted.");
    }
}

main();

