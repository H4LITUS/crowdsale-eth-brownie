// SPDX-License-Identifier: MIT

/*
Crowdsale
Timed Crowdsale
Capped Crowdsale
Minted Crowdsale
Whitelisted Crowdsale
Refundable Crowdsale

Presale/Public sale

Token distribution and Vesting
*/

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";

contract Token is ERC20, Ownable {
    bool private _canMint;

    constructor() ERC20("ICO Token", "iTok") {
        _canMint = true;
    }

    function mint(address _account, uint256 _amount)
        external
        onlyOwner
        returns (bool)
    {
        require(_canMint, "Minting Finished");
        _mint(_account, _amount);
        return true;
    }

    function finishMinting() external onlyOwner {
        require(_canMint, "Minting already finished");
        _canMint = false;
    }

    function canMint() public view returns (bool) {
        return _canMint;
    }

    // function pause() public onlyOwner {
    //     _pause();
    // }

    // function unpause() public onlyOwner {
    //     _unpause();
    // }
}
