from scripts.helpful_scripts import get_account, LOCAL_BLOCKCHAIN_ENVIRONEMNTS
from brownie import network, TimeCapped, exceptions, chain
import pytest


def test_timecapped_attributes():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    account = get_account()
    opening_time = chain.time()
    closing_time = opening_time + 1000
    timecapped = TimeCapped.deploy(opening_time, closing_time, {"from": account})

    assert timecapped.openingTime() == opening_time
    assert timecapped.closingTime() == closing_time
    assert timecapped.isOpen() == True
    assert timecapped.isClosed() == False


def test_timecapped_is_not_open():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    account = get_account()
    opening_time = chain.time() + 5
    closing_time = opening_time + 5
    timecapped = TimeCapped.deploy(opening_time, closing_time, {"from": account})
    chain.mine()
    assert timecapped.isOpen() == False


def test_timecapped_is_closed():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    account = get_account()
    opening_time = chain.time()
    closing_time = opening_time + 1
    timecapped = TimeCapped.deploy(opening_time, closing_time, {"from": account})
    chain.sleep(2)
    chain.mine()
    assert timecapped.isClosed() == True


def test_timecapped_opening_time_before_now():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    account = get_account()
    opening_time = chain.time() - 1
    closing_time = opening_time + 1000

    with pytest.raises(exceptions.VirtualMachineError):
        TimeCapped.deploy(opening_time, closing_time, {"from": account})


def test_timecapped_opening_time_after_closing_time():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONEMNTS:
        pytest.skip("Only for local testing")
    account = get_account()
    closing_time = chain.time() + 1
    opening_time = closing_time + 10

    with pytest.raises(exceptions.VirtualMachineError):
        TimeCapped.deploy(opening_time, closing_time, {"from": account})
