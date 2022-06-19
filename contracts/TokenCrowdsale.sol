// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "./Token.sol";
import "./TimeCapped.sol";
import "./WhitelistedCrowdsale.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TokenCrowdsale is Ownable, TimeCapped, WhitelistedCrowdsale {
    uint256 public rate;
    address payable public wallet;
    Token public token;

    uint256 public cap;
    uint256 public investorMinCap;
    uint256 public investorMaxCap;
    mapping(address => uint256) public contributions;

    mapping(address => uint256) public beneficiaryTokensOwned;
    address[] public tokenHolders;

    uint256 public amountRaised;
    uint256 public goal;
    bool public didWithdrawFunds;
    bool public finalized;

    uint256 public tokenSalePercentage = 60;
    uint256 public foundersPercentage = 20;
    uint256 public foundationPercentage = 15;
    uint256 public partnersPercentage = 5;

    address public foundersAddress;
    address public foundationAddress;
    address public partnersAddress;

    enum CrowdsaleState {
        PreICO,
        ICO
    }

    CrowdsaleState private state;

    event TokensPurchased(
        address indexed purchaser,
        address indexed beneficiary,
        uint256 weiAmount,
        uint256 tokenAmount
    );

    event FundsWithdrawn(address indexed wallet, uint256 amount);
    event RefundClaimed(address indexed refundee, uint256 amount);

    event CrowdsaleFinalized();

    constructor(
        uint256 _rate,
        address payable _wallet,
        address _token,
        uint256 _cap,
        uint256 _investorMinCap,
        uint256 _investorMaxCap,
        uint256 _openingTime,
        uint256 _closingTime,
        uint256 _goal,
        address _foundersAddress,
        address _foundationAddress,
        address _partnersAddress
    ) TimeCapped(_openingTime, _closingTime) {
        require(_rate > 0, "Crowdsale rate is 0");
        require(_wallet != address(0), "Wallet is the zero address");
        require(address(_token) != address(0), "Token is the zero address");
        require(_cap > 0, "Cap limit is zero");
        require(
            (_investorMinCap < _investorMaxCap),
            "Investor minimum cap should be less than the max cap"
        );
        require(
            (_investorMaxCap > 0 && _investorMaxCap < _cap),
            "Investor max cap should be less than the max cap of crowdsale and shouldn't be zero"
        );
        require(_goal > 0, "Goal should be greater than zero");
        require(
            _goal <= _cap,
            "Goal should be less than/equal to the crowdsale cap"
        );

        require(
            _foundersAddress != address(0),
            "Crowdsale: Founders address cannot be address 0"
        );
        require(
            _foundationAddress != address(0),
            "Crowdsale: Foundation address cannot be address 0"
        );
        require(
            _partnersAddress != address(0),
            "Crowdsale: Partners address cannot be address 0"
        );

        rate = _rate;
        wallet = _wallet;
        token = Token(_token);
        cap = _cap;
        investorMinCap = _investorMinCap;
        investorMaxCap = _investorMaxCap;
        goal = _goal;
        foundersAddress = _foundersAddress;
        foundationAddress = _foundationAddress;
        partnersAddress = _partnersAddress;
    }

    function capLimitReached() external view returns (bool) {
        return amountRaised >= cap;
    }

    function getCrowdsaleState() external view returns (CrowdsaleState) {
        return state;
    }

    function setCrowdsaleState(CrowdsaleState _state) public onlyOwner {
        require(
            _state > state,
            "Crowdsale: Cannot set ICO state to an older state"
        );
        state = _state;
        if (state == CrowdsaleState.ICO) rate = 10;
    }

    fallback() external payable {
        buyToken(msg.sender);
    }

    function buyToken(address _beneficiary)
        public
        payable
        onlyWhileOpen
        returns (bool)
    {
        require(
            checkWhitelistedUser(_beneficiary),
            "Crowdsale: Beneficiary is not whitelisted"
        );
        require(msg.value != 0, "Ether amount should be more than 0");
        require(
            _beneficiary != address(0),
            "Beneficiary address is the zero address"
        );

        contributions[_beneficiary] += msg.value;
        require(
            contributions[_beneficiary] >= investorMinCap,
            "Ether amount is less than the minimum contribution amount"
        );
        require(
            contributions[_beneficiary] <= investorMaxCap,
            "Ether amount is more than the max contribution amount"
        );

        amountRaised += msg.value;
        require(amountRaised <= cap, "Crowdsale cap exceeded");

        uint256 tokensToIssue = calculateTokens(msg.value);
        require(
            token.mint(address(this), tokensToIssue),
            "Crowdsale: Token minting failed"
        );
        if (beneficiaryTokensOwned[_beneficiary] == 0) {
            tokenHolders.push(_beneficiary);
        }
        beneficiaryTokensOwned[_beneficiary] += tokensToIssue;

        emit TokensPurchased(
            msg.sender,
            _beneficiary,
            msg.value,
            tokensToIssue
        );
        return true;
    }

    function calculateTokens(uint256 weiAmount) public view returns (uint256) {
        return weiAmount * rate;
    }

    function goalReached() public view returns (bool) {
        return amountRaised >= goal;
    }

    function withdrawFunds() external onlyOwner returns (bool) {
        require(isClosed(), "Crowdsale not closed yet");
        require(goalReached(), "Crowdsale: Goal not reached");
        require(finalized, "Crowdsale: Not finalized");

        require(
            !didWithdrawFunds,
            "Crowdsale: Funds have already been withdrawn to wallet"
        );
        didWithdrawFunds = true;
        (bool sent, ) = wallet.call{value: amountRaised}("");
        require(sent, "Failed to transfer ether to wallet");
        emit FundsWithdrawn(wallet, amountRaised);
        return true;
    }

    function claimRefund() external returns (bool) {
        require(isClosed(), "Crowdsale not closed yet");
        require(!goalReached(), "Crowdsale: Goal has been acheived");
        require(
            contributions[msg.sender] > 0,
            "Crowdsale: You haven't made any contributions"
        );
        uint256 balance = contributions[msg.sender];
        contributions[msg.sender] = 0;

        address payable _to = payable(msg.sender);
        (bool sent, ) = _to.call{value: balance}("");
        require(sent, "Crowdsale: Transaction failed");
        emit RefundClaimed(msg.sender, balance);
        return sent;
    }

    function claimTokens() external returns (bool) {
        uint256 tokensOwned = beneficiaryTokensOwned[msg.sender];
        require(tokensOwned > 0, "Crowdsale: Beneficiary isn't due any tokens");
        require(isClosed(), "Crowdsale not closed yet");
        require(goalReached(), "Crowdsale: Goal not reached");
        require(finalized, "Crowdsale: Not finalized");

        beneficiaryTokensOwned[msg.sender] = 0;
        require(
            token.transfer(msg.sender, tokensOwned),
            "Failed to claim tokens"
        );
        return true;
    }

    function finalize() public onlyOwner {
        require(!finalized, "Crowdsale already finalized");
        require(isClosed(), "Crowdsale not closed yet");

        finalized = true;

        uint256 _mintedTokens = token.totalSupply();
        uint256 _finalTotalSupply = (_mintedTokens * 100) / tokenSalePercentage;
        token.mint(
            foundersAddress,
            (_finalTotalSupply * foundersPercentage) / 100
        );
        token.mint(
            foundationAddress,
            (_finalTotalSupply * foundationPercentage) / 100
        );
        token.mint(
            partnersAddress,
            (_finalTotalSupply * partnersPercentage) / 100
        );

        token.finishMinting();

        token.transferOwnership(wallet);
        emit CrowdsaleFinalized();
    }
}
