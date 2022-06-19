// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract TimeCapped {
    uint256 private _openingTime;
    uint256 private _closingTime;

    modifier onlyWhileOpen() {
        require(isOpen(), "Not Open");
        _;
    }

    modifier onlyWhileClosed() {
        require(isClosed(), "Not closed");
        _;
    }

    constructor(uint256 openingTime_, uint256 closingTime_) {
        require(
            openingTime_ >= block.timestamp,
            "Opening Time cannot be before the current time"
        );
        require(
            closingTime_ > openingTime_,
            "Opening Time should be before closing time"
        );
        _openingTime = openingTime_;
        _closingTime = closingTime_;
    }

    function openingTime() public view returns (uint256) {
        return _openingTime;
    }

    function closingTime() public view returns (uint256) {
        return _closingTime;
    }

    function isClosed() public view returns (bool) {
        return block.timestamp > _closingTime;
    }

    function isOpen() public view returns (bool) {
        return (block.timestamp >= _openingTime &&
            block.timestamp <= _closingTime);
    }
}
