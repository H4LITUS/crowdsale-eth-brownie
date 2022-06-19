// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

contract WhitelistedCrowdsale is Ownable {
    mapping(address => bool) private whiteListedUsers;

    function addWhitelistedUser(address _user) public onlyOwner returns (bool) {
        require(
            _user != address(0),
            "Failed: Whitelisted user address is the zero address"
        );
        whiteListedUsers[_user] = true;
        return true;
    }

    function removeWhitelistedUser(address _user)
        public
        onlyOwner
        returns (bool)
    {
        require(_user != address(0), "Failed: Address is the zero address");
        whiteListedUsers[_user] = false;
        return true;
    }

    function checkWhitelistedUser(address _user) public view returns (bool) {
        return whiteListedUsers[_user];
    }
}
