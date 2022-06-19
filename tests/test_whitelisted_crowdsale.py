import brownie
import pytest
from brownie import WhitelistedCrowdsale, network
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONEMNTS, get_account


def test_add_remove_whitelist_user_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    owner = get_account()
    user1 = get_account(index=1)
    user2 = get_account(index=2)
    wl_crowdsale = WhitelistedCrowdsale.deploy({"from": owner})

    assert wl_crowdsale.addWhitelistedUser(user1, {"from": owner})
    assert wl_crowdsale.addWhitelistedUser(user2, {"from": owner})

    assert wl_crowdsale.checkWhitelistedUser(user1)
    assert wl_crowdsale.checkWhitelistedUser(user2)

    assert wl_crowdsale.removeWhitelistedUser(user1, {"from": owner})

    assert wl_crowdsale.checkWhitelistedUser(user1) == False
    assert wl_crowdsale.checkWhitelistedUser(user2)


def test_add_remove_whitelist_user_non_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    owner = get_account()
    non_owner = get_account(index=1)
    user = get_account(index=2)
    wl_crowdsale = WhitelistedCrowdsale.deploy({"from": owner})

    with brownie.reverts("Ownable: caller is not the owner"):
        wl_crowdsale.addWhitelistedUser(user, {"from": non_owner})

    wl_crowdsale.addWhitelistedUser(user, {"from": owner})

    with brownie.reverts("Ownable: caller is not the owner"):
        wl_crowdsale.removeWhitelistedUser(user, {"from": non_owner})


def test_check_non_whitelisted_user():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")

    owner = get_account()
    user1 = get_account(index=1)
    wl_crowdsale = WhitelistedCrowdsale.deploy({"from": owner})

    assert wl_crowdsale.checkWhitelistedUser(user1) == False
