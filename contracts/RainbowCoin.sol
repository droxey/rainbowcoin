pragma solidity ^0.5.0;

import "./TradeableERC721Token.sol";
import "openzeppelin-solidity/contracts/ownership/Ownable.sol";

/**
 * @title RainbowCoin
 * RainbowCoin - a contract for non-fungible RGB tokens.
 */
contract RainbowCoin is TradeableERC721Token {
  constructor(address _proxyRegistryAddress) TradeableERC721Token("RainbowCoin", "RGB", _proxyRegistryAddress) public {  }

  function baseTokenURI() public view returns (string memory) {
    return "https://rainbowco.in/api/coin/";
  }

  function mintTo(address _to, uint256 _rgbInt) public onlyOwner {
    super._mint(_to, _rgbInt);
  }
}
