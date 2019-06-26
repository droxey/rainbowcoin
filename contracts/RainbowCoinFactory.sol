pragma solidity ^0.5.0;

import "openzeppelin-solidity/contracts/ownership/Ownable.sol";
import "./Factory.sol";
import "./RainbowCoin.sol";
import "./Strings.sol";

contract RainbowCoinFactory is Factory, Ownable {
  using Strings for string;

  address public proxyRegistryAddress;
  address public nftAddress;
  string public baseURI = "https://rainbowco.ion/api/factory/";

  /**
   * @dev Enforce the existence of only 16,777,216 RainbowCoins (2^24).
   */
  uint256 RAINBOWCOIN_SUPPLY = 16777216;

  constructor(address _proxyRegistryAddress, address _nftAddress) public {
    proxyRegistryAddress = _proxyRegistryAddress;
    nftAddress = _nftAddress;
  }

  function name() external view returns (string memory) {
    return "RainbowCoin Token Sale";
  }

  function symbol() external view returns (string memory) {
    return "RGBF";
  }

  function supportsFactoryInterface() public view returns (bool) {
    return true;
  }

  function numOptions() public view returns (uint256) {
    return 1;
  }

  function mint(uint256 _optionId, address _toAddress) public {
    // Must be sent from the owner proxy or owner.
    ProxyRegistry proxyRegistry = ProxyRegistry(proxyRegistryAddress);
    assert(address(proxyRegistry.proxies(owner())) == msg.sender || owner() == msg.sender);
    require(canMint());

    RainbowCoin coin = RainbowCoin(nftAddress);
    coin.mintTo(_toAddress);
  }

  function canMint() public view returns (bool) {
    RainbowCoin coin = RainbowCoin(nftAddress);
    uint256 coinSupplyPlusOne = coin.totalSupply() + 1;
    return coinSupplyPlusOne <= RAINBOWCOIN_SUPPLY;
  }

  function tokenURI(uint256 _optionId) external view returns (string memory) {
    return Strings.strConcat(baseURI, Strings.uint2str(_optionId));
  }

  /**
   * Hack to get things to work automatically on OpenSea.
   * Use transferFrom so the frontend doesn't have to worry about different method names.
   */
  function transferFrom(address _from, address _to, uint256 _tokenId) public {
    mint(_tokenId, _to);
  }

  /**
   * Hack to get things to work automatically on OpenSea.
   * Use isApprovedForAll so the frontend doesn't have to worry about different method names.
   */
  function isApprovedForAll(
    address _owner,
    address _operator
  )
    public
    view
    returns (bool)
  {
    if (owner() == _owner && _owner == _operator) {
      return true;
    }

    ProxyRegistry proxyRegistry = ProxyRegistry(proxyRegistryAddress);
    if (owner() == _owner && address(proxyRegistry.proxies(_owner)) == _operator) {
      return true;
    }

    return false;
  }

  /**
   * Hack to get things to work automatically on OpenSea.
   * Use isApprovedForAll so the frontend doesn't have to worry about different method names.
   */
  function ownerOf(uint256 _tokenId) public view returns (address _owner) {
    return owner();
  }
}
