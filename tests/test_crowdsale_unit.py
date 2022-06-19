import brownie
from scripts.deploy_crowdsale import deploy_crowdsale, deploy_token, open_crowdsale
from scripts.helpful_scripts import get_account, LOCAL_BLOCKCHAIN_ENVIRONEMNTS
from web3 import Web3
import pytest
from brownie import chain, network, exceptions, reverts
import time


def test_token_has_correct_attributes():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    token = deploy_token()
    tokenName = "ICO Token"
    tokenSymbol = "iTok"
    tokenDecimals = 18

    assert token.name() == tokenName
    assert token.symbol() == tokenSymbol
    assert token.decimals() == tokenDecimals


def test_crowdsale_attributes():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    wallet = get_account(index=1)
    rate = 20
    cap_limit = Web3.toWei(8, "ether")
    investor_min_cap = Web3.toWei(0.05, "ether")
    investor_max_cap = Web3.toWei(5, "ether")
    opening_time = chain.time()
    closing_time = opening_time + 10
    goal = Web3.toWei(7, "ether")

    token = deploy_token()
    crowdsale = deploy_crowdsale(
        rate=rate,
        token=token,
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
    )

    assert crowdsale.rate() == rate
    assert crowdsale.wallet() == wallet
    assert crowdsale.token() == token.address
    assert crowdsale.cap() == cap_limit
    assert crowdsale.investorMinCap() == investor_min_cap
    assert crowdsale.investorMaxCap() == investor_max_cap
    assert crowdsale.openingTime() == opening_time
    assert crowdsale.closingTime() == closing_time
    assert crowdsale.goal() == goal


def test_crowdsale_state():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    owner = get_account()
    rate = 10
    crowdsale = deploy_crowdsale(rate=rate)

    assert crowdsale.getCrowdsaleState() == 0

    with brownie.reverts("Crowdsale: Cannot set ICO state to an older state"):
        crowdsale.setCrowdsaleState(0, {"from": owner})

    with brownie.reverts():
        crowdsale.setCrowdsaleState(2, {"from": owner})

    with brownie.reverts("Ownable: caller is not the owner"):
        crowdsale.setCrowdsaleState(1, {"from": get_account(index=1)})

    crowdsale.setCrowdsaleState(1, {"from": owner})
    assert crowdsale.getCrowdsaleState() == 1
    assert crowdsale.rate() == 10


def test_token_owner_is_crowdsale():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    token = deploy_token()
    crowdsale = deploy_crowdsale(token=token)
    assert token.owner() == crowdsale


def test_crowdsale_buy_tokens():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    token = deploy_token()
    crowdsale = deploy_crowdsale(token=token)

    open_crowdsale()

    owner = get_account()
    investor1 = get_account(index=2)
    beneficiary = get_account(index=3)
    eth_amount = Web3.toWei(2, "ether")
    init_token_supply = token.totalSupply()
    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})

    # Act
    crowdsale.buyToken(beneficiary, {"from": investor1, "value": eth_amount})
    new_token_supply = token.totalSupply()

    # Assert
    assert (
        crowdsale.beneficiaryTokensOwned(beneficiary) == crowdsale.rate() * eth_amount
    )
    assert crowdsale.beneficiaryTokensOwned(investor1) == 0
    assert new_token_supply == init_token_supply + (crowdsale.rate() * eth_amount)


def test_crowdsale_amount_raised():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    crowdsale = deploy_crowdsale()
    open_crowdsale()

    wallet = get_account(index=1)
    investor1 = get_account(index=2)
    eth_amount = Web3.toWei(2, "ether")
    # init_wallet_balance = wallet.balance()
    crowdsale.addWhitelistedUser(investor1, {"from": crowdsale.owner()})

    # Act
    crowdsale.buyToken(investor1, {"from": investor1, "value": eth_amount})

    # Assert
    assert crowdsale.amountRaised() == eth_amount
    assert crowdsale.balance() == eth_amount


def test_crowdsale_cap_limit():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    cap_limit = Web3.toWei(3, "ether")
    investor_max_cap = Web3.toWei(2, "ether")
    goal = Web3.toWei(3, "ether")
    crowdsale = deploy_crowdsale(
        investor_max_cap=investor_max_cap, cap_limit=cap_limit, goal=goal
    )
    open_crowdsale()

    investor1 = get_account(index=2)
    investor2 = get_account(index=3)

    crowdsale.addWhitelistedUser(investor1, {"from": crowdsale.owner()})
    crowdsale.addWhitelistedUser(investor2, {"from": crowdsale.owner()})

    # Act
    crowdsale.buyToken(investor1, {"from": investor1, "value": investor_max_cap})

    # Assert
    assert not crowdsale.capLimitReached()

    crowdsale.buyToken(investor2, {"from": investor2, "value": investor_max_cap / 2})
    assert crowdsale.capLimitReached()

    with pytest.raises(exceptions.VirtualMachineError):
        crowdsale.buyToken(
            investor2, {"from": investor2, "value": investor_max_cap / 2}
        )


def test_crowdsale_investor_min_cap_limit():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    crowdsale = deploy_crowdsale()
    open_crowdsale()

    investor1 = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()
    inv_amount_less_than_min = investor_min_cap - 1
    crowdsale.addWhitelistedUser(investor1, {"from": crowdsale.owner()})

    with pytest.raises(exceptions.VirtualMachineError):
        crowdsale.buyToken(
            investor1, {"from": investor1, "value": inv_amount_less_than_min}
        )

    assert crowdsale.buyToken(investor1, {"from": investor1, "value": investor_min_cap})

    assert crowdsale.buyToken(
        investor1, {"from": investor1, "value": inv_amount_less_than_min}
    )


def test_crowdsale_investor_max_cap_limit():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    crowdsale = deploy_crowdsale()
    open_crowdsale()

    investor1 = get_account(index=2)
    investor_max_cap = crowdsale.investorMaxCap()
    crowdsale.addWhitelistedUser(investor1, {"from": crowdsale.owner()})

    crowdsale.buyToken(investor1, {"from": investor1, "value": investor_max_cap})

    with pytest.raises(exceptions.VirtualMachineError):
        crowdsale.buyToken(investor1, {"from": investor1, "value": 1})


def test_crowdsale_contribute_before_after_opening():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    opening_time = chain.time() + 10
    closing_time = opening_time + 100
    crowdsale = deploy_crowdsale(opening_time=opening_time, closing_time=closing_time)

    investor1 = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()
    crowdsale.addWhitelistedUser(investor1, {"from": crowdsale.owner()})

    # with pytest.raises(exceptions.VirtualMachineError):
    with reverts("Not Open"):
        crowdsale.buyToken(investor1, {"from": investor1, "value": investor_min_cap})

    chain.sleep(20)
    chain.mine()

    assert crowdsale.buyToken(investor1, {"from": investor1, "value": investor_min_cap})


def test_crowdsale_contribute_after_closed():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    opening_time = chain.time() + 5
    closing_time = opening_time + 20
    crowdsale = deploy_crowdsale(opening_time=opening_time, closing_time=closing_time)

    investor1 = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()

    chain.sleep(200)
    chain.mine()

    with reverts("Not Open"):
        crowdsale.buyToken(investor1, {"from": investor1, "value": investor_min_cap})


def test_crowdsale_buy_tokens_non_whitelisted():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    token = deploy_token()
    crowdsale = deploy_crowdsale(token=token)
    open_crowdsale()

    beneficiary = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()

    with brownie.reverts("Crowdsale: Beneficiary is not whitelisted"):
        crowdsale.buyToken(
            beneficiary, {"from": beneficiary, "value": investor_min_cap}
        )

    assert not crowdsale.checkWhitelistedUser(beneficiary)


def test_crowdsale_whitelist_user():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    token = deploy_token()
    crowdsale = deploy_crowdsale(token=token)
    open_crowdsale()

    owner = crowdsale.owner()
    beneficiary = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()

    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})

    assert crowdsale.checkWhitelistedUser(beneficiary)

    assert crowdsale.buyToken(
        beneficiary, {"from": beneficiary, "value": investor_min_cap}
    )


def test_crowdsale_remove_whitelist_user():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    token = deploy_token()
    crowdsale = deploy_crowdsale(token=token)
    open_crowdsale()

    owner = crowdsale.owner()
    beneficiary = get_account(index=2)
    investor_min_cap = crowdsale.investorMinCap()

    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})

    assert crowdsale.checkWhitelistedUser(beneficiary)

    assert crowdsale.removeWhitelistedUser(beneficiary, {"from": owner})

    with brownie.reverts("Crowdsale: Beneficiary is not whitelisted"):
        crowdsale.buyToken(
            beneficiary, {"from": beneficiary, "value": investor_min_cap}
        )


def test_crowdsale_claim_refund_withdraw_goal_not_reached():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    cap_limit = Web3.toWei(8, "ether")
    investor_min_cap = Web3.toWei(0.05, "ether")
    investor_max_cap = Web3.toWei(5, "ether")
    opening_time = chain.time()
    closing_time = opening_time + 20
    goal = Web3.toWei(5, "ether")

    crowdsale = deploy_crowdsale(
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
    )
    open_crowdsale()

    owner = get_account()
    beneficiary = get_account(index=2)

    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})
    crowdsale.buyToken(beneficiary, {"from": beneficiary, "value": goal - 1})

    assert not crowdsale.goalReached()

    with brownie.reverts("Crowdsale not closed yet"):
        crowdsale.claimRefund({"from": beneficiary})

    with brownie.reverts("Crowdsale not closed yet"):
        crowdsale.withdrawFunds({"from": owner})

    with brownie.reverts("Crowdsale not closed yet"):
        crowdsale.claimTokens({"from": beneficiary})

    with brownie.reverts("Crowdsale: Beneficiary isn't due any tokens"):
        crowdsale.claimTokens({"from": get_account(index=5)})

    chain.sleep(30)
    chain.mine()

    with brownie.reverts("Crowdsale: Goal not reached"):
        crowdsale.claimTokens({"from": beneficiary})

    with brownie.reverts("Crowdsale: You haven't made any contributions"):
        crowdsale.claimRefund({"from": get_account(index=5)})

    with brownie.reverts("Crowdsale: Goal not reached"):
        crowdsale.withdrawFunds({"from": owner})

    assert crowdsale.claimRefund({"from": beneficiary})


def test_crowdsale_claim_refund_withdraw_after_goal_met():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    wallet = get_account(index=1)
    cap_limit = Web3.toWei(8, "ether")
    investor_min_cap = Web3.toWei(0.05, "ether")
    investor_max_cap = Web3.toWei(5, "ether")
    opening_time = chain.time()
    closing_time = opening_time + 20
    goal = Web3.toWei(5, "ether")
    token = deploy_token()

    crowdsale = deploy_crowdsale(
        token=token,
        wallet=wallet,
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
    )
    open_crowdsale()

    owner = get_account()
    beneficiary = get_account(index=2)
    initial_wallet_balance = wallet.balance()

    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})
    crowdsale.buyToken(beneficiary, {"from": beneficiary, "value": goal})

    chain.sleep(30)
    chain.mine()

    tokens_owned = crowdsale.calculateTokens(goal)

    assert crowdsale.goalReached()

    with brownie.reverts("Crowdsale: Goal has been acheived"):
        crowdsale.claimRefund({"from": beneficiary})

    with brownie.reverts("Crowdsale: Not finalized"):
        assert crowdsale.withdrawFunds({"from": owner})

    crowdsale.finalize({"from": owner})

    assert crowdsale.withdrawFunds({"from": owner})

    assert wallet.balance() == initial_wallet_balance + goal

    with brownie.reverts("Crowdsale: Funds have already been withdrawn to wallet"):
        crowdsale.withdrawFunds({"from": owner})

    assert token.balanceOf(beneficiary) == 0
    assert crowdsale.beneficiaryTokensOwned(beneficiary) == tokens_owned

    assert crowdsale.claimTokens({"from": beneficiary})

    assert token.balanceOf(beneficiary) == tokens_owned
    assert crowdsale.beneficiaryTokensOwned(beneficiary) == 0
    time.sleep(2)


def test_crowdsale_token_owner_after_funds_withdraw():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    # Arrange
    wallet = get_account(index=1)
    cap_limit = Web3.toWei(8, "ether")
    investor_min_cap = Web3.toWei(0.05, "ether")
    investor_max_cap = Web3.toWei(5, "ether")
    opening_time = chain.time()
    closing_time = opening_time + 20
    goal = investor_max_cap

    token = deploy_token()

    crowdsale = deploy_crowdsale(
        token=token,
        wallet=wallet,
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
    )
    open_crowdsale()

    owner = get_account()
    beneficiary = get_account(index=2)

    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})
    crowdsale.buyToken(beneficiary, {"from": beneficiary, "value": goal})

    chain.sleep(30)
    chain.mine()

    crowdsale.finalize({"from": owner})
    crowdsale.withdrawFunds({"from": owner})
    assert token.owner() == wallet


def test_crowdsale_token_distribution():

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    crowdsale = deploy_crowdsale()

    tokenSalePercentage = 60
    foundersPercentage = 20
    foundationPercentage = 15
    partnersPercentage = 5

    _tokenSalePercentage = crowdsale.tokenSalePercentage()
    _foundersPercentage = crowdsale.foundersPercentage()
    _foundationPercentage = crowdsale.foundationPercentage()
    _partnersPercentage = crowdsale.partnersPercentage()

    assert _tokenSalePercentage == tokenSalePercentage
    assert _foundersPercentage == foundersPercentage
    assert _foundationPercentage == foundationPercentage
    assert _partnersPercentage == partnersPercentage

    totalPercentage = (
        _tokenSalePercentage
        + _foundersPercentage
        + _foundationPercentage
        + _partnersPercentage
    )
    assert totalPercentage == 100


def test_crowdsale_finalize():

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    cap_limit = Web3.toWei(8, "ether")
    investor_min_cap = Web3.toWei(0.05, "ether")
    investor_max_cap = Web3.toWei(5, "ether")
    opening_time = chain.time()
    closing_time = opening_time + 20
    goal = investor_max_cap

    token = deploy_token()

    crowdsale = deploy_crowdsale(
        token=token,
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
    )
    open_crowdsale()

    owner = get_account()
    investor1 = get_account(index=2)
    beneficiary = get_account(index=3)
    eth_amount = crowdsale.investorMaxCap()
    crowdsale.addWhitelistedUser(beneficiary, {"from": owner})
    crowdsale.buyToken(beneficiary, {"from": investor1, "value": eth_amount})

    tokenSalePercentage = 60
    foundersPercentage = 20
    foundationPercentage = 15
    partnersPercentage = 5

    mintedTokens = token.totalSupply() / (10**18)
    total_tokens = mintedTokens / tokenSalePercentage
    founders_tokens = total_tokens * foundersPercentage
    foundation_tokens = total_tokens * foundationPercentage
    partners_tokens = total_tokens * partnersPercentage

    chain.sleep(30)
    chain.mine()

    crowdsale.finalize({"from": owner})

    founders_balance = token.balanceOf(get_account(index=7)) / (10**18)
    foundation_balance = token.balanceOf(get_account(index=8)) / (10**18)
    partners_balance = token.balanceOf(get_account(index=9)) / (10**18)

    assert founders_balance == founders_tokens
    assert foundation_balance == foundation_tokens
    assert partners_balance == partners_tokens
