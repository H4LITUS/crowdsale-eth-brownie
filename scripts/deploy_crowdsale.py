from threading import local
from scripts.helpful_scripts import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONEMNTS,
    FORKED_LOCAL_ENVIRONMENTS,
    get_account,
)
from brownie import Token, TokenCrowdsale, chain, network, config, accounts
from web3 import Web3
import time


RATE = 20
CAP_LIMIT = Web3.toWei(8, "ether")
INVESTOR_MIN_CAP = Web3.toWei(0.05, "ether")
INVESTOR_MAX_CAP = Web3.toWei(5, "ether")
STARTING_TIME = 10
GOAL = Web3.toWei(7, "ether")


def deploy_token():
    account = get_account()
    token = Token.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    return token


def deploy_crowdsale(
    rate=RATE,
    wallet=None,
    token=None,
    cap_limit=CAP_LIMIT,
    investor_min_cap=INVESTOR_MIN_CAP,
    investor_max_cap=INVESTOR_MAX_CAP,
    opening_time=None,
    closing_time=None,
    goal=GOAL,
    foundersAddress=None,
    foundationAddress=None,
    partnersAddress=None,
    account=None,
):

    if not wallet:
        if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS
            or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
        ):
            wallet = get_account(index=1)
    if not token:
        if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS
            or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
        ):
            token = deploy_token()
        else:
            if Token:
                token = Token[-1]
            else:
                token = deploy_token()
    if not opening_time:
        opening_time = chain.time() + STARTING_TIME
    if not closing_time:
        closing_time = opening_time + 1000
    if not foundersAddress:
        if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS
            or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
        ):
            foundersAddress = get_account(index=7)
    if not foundationAddress:
        if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS
            or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
        ):
            foundationAddress = get_account(index=8)
    if not partnersAddress:
        if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS
            or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
        ):
            partnersAddress = get_account(index=9)
    if not account:
        account = get_account()

    crowdsale = TokenCrowdsale.deploy(
        rate,
        wallet,
        token.address,
        cap_limit,
        investor_min_cap,
        investor_max_cap,
        opening_time,
        closing_time,
        goal,
        foundersAddress,
        foundationAddress,
        partnersAddress,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )

    tx = token.transferOwnership(crowdsale, {"from": account})
    tx.wait(1)
    print("Token ownership transferred")

    return crowdsale


def open_crowdsale():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        chain.sleep(STARTING_TIME)
        chain.mine()


def main():
    account_1 = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        account_2 = get_account(index=1)
        account_3 = get_account(index=2)
    else:
        account_2 = accounts.add(config["wallets"]["from_key_2"])
        account_3 = accounts.add(config["wallets"]["from_key_3"])

    owner = account_1
    wallet = account_2
    beneficiary_1 = account_1
    beneficiary_2 = account_3

    cap_limit = Web3.toWei(10, "ether")
    investor_min_cap = Web3.toWei(0.001, "ether")
    investor_max_cap = Web3.toWei(0.1, "ether")
    opening_time = chain.time() + 120
    closing_time = opening_time + 120
    goal = investor_max_cap * 2

    token = deploy_token()

    crowdsale = deploy_crowdsale(
        rate=50,
        wallet=wallet,
        token=token,
        cap_limit=cap_limit,
        investor_min_cap=investor_min_cap,
        investor_max_cap=investor_max_cap,
        opening_time=opening_time,
        closing_time=closing_time,
        goal=goal,
        foundersAddress=account_1,
        foundationAddress=account_2,
        partnersAddress=account_3,
        account=owner,
    )
    print("Waiting for crowdsale to open..............")
    while not crowdsale.isOpen():
        if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
            chain.mine()
        else:
            pass
    print("Crowdsale Opened...........................")

    crowdsale.addWhitelistedUser(beneficiary_1, {"from": owner})
    print(f"{beneficiary_1} has been whitelisted")
    crowdsale.addWhitelistedUser(beneficiary_2, {"from": owner})
    print(f"{beneficiary_2} has been whitelisted\n")

    amount = Web3.toWei(0.1, "ether")

    crowdsale.buyToken(beneficiary_1, {"from": owner, "value": amount})
    token_received = crowdsale.calculateTokens(amount)
    print(
        f"{wallet} deposited {amount} ETH on behalf of {beneficiary_1}. \n{beneficiary_1} received {token_received} {token.symbol()}\n"
    )

    crowdsale.buyToken(beneficiary_2, {"from": beneficiary_2, "value": amount / 2})
    token_received = crowdsale.calculateTokens(amount / 2)
    print(
        f"{beneficiary_2} deposited {amount/2} ETH on behalf of {account_3}. \n{beneficiary_2} received {token_received} {token.symbol()}\n"
    )

    crowdsale.buyToken(beneficiary_2, {"from": beneficiary_2, "value": amount / 2})
    token_received = crowdsale.calculateTokens(amount / 2)
    print(
        f"{beneficiary_2} deposited {amount/2} ETH on behalf of {account_3}. \n{beneficiary_2} received {token_received} {token.symbol()}\n"
    )

    print(
        f"Token balances before finalizing crowdsale:\nFounders: {token.balanceOf(account_1)}, Foundation: {token.balanceOf(account_2)}, Partners: {{token.balanceOf(account_3)}}\n"
    )

    print("Waiting for crowdsale to close..............")
    while crowdsale.isOpen():
        if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
            chain.mine()
        else:
            pass
    print("Crowdsale Closed............................\n")

    tx = crowdsale.finalize({"from": owner})
    tx.wait(1)
    print("Crowdsale finalized...!!!!!\n")

    print(
        f"Token balances after finalizing crowdsale:\nFounders: {token.balanceOf(account_1)}, Foundation: {token.balanceOf(account_2)}, Partners: {token.balanceOf(account_3)}\n"
    )

    if crowdsale.goalReached():
        print(f"Wallet Balance before withdrawal: {wallet.balance()} ETH")
        tx = crowdsale.withdrawFunds({"from": owner})
        tx.wait(1)
        print(f"Wallet Balance after withdrawal: {wallet.balance()} ETH\n")

        print(
            f"Beneficiary token balances before claiming tokens \nBenefeciary 1: {token.balanceOf(beneficiary_1)} \nBenefeciary 2: {token.balanceOf(beneficiary_2)}"
        )
        tx = crowdsale.claimTokens({"from": beneficiary_1})
        tx.wait(1)
        tx = crowdsale.claimTokens({"from": beneficiary_2})
        tx.wait(1)
        print(
            f"Beneficiary token balances after claiming tokens \nBenefeciary 1: {token.balanceOf(beneficiary_1)} \nBenefeciary 2: {token.balanceOf(beneficiary_2)}"
        )

    else:
        print(
            f"Beneficiary token balances before refund \nBenefeciary 1: {beneficiary_1.balance()} \nBenefeciary 2: {beneficiary_2.balance()}"
        )
        tx = crowdsale.claimRefund({"from": beneficiary_1})
        tx.wait(1)
        tx = crowdsale.claimRefund({"from": beneficiary_2})
        tx.wait(1)
        print(
            f"Beneficiary token balances after refund \nBenefeciary 1: {beneficiary_1.balance()} \nBenefeciary 2: {beneficiary_2.balance()}"
        )

    time.sleep(1)
