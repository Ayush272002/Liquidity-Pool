import pytest
from ape import project


@pytest.fixture
def owner(accounts):
    return accounts[0]


@pytest.fixture
def alice(accounts):
    return accounts[1]


@pytest.fixture
def bob(accounts):
    return accounts[2]


@pytest.fixture
def token(owner):
    return owner.deploy(project.MockERC20, "Test Token", "TST")


class TestDeployment:
    def test_name(self, token):
        assert token.name() == "Test Token"

    def test_symbol(self, token):
        assert token.symbol() == "TST"

    def test_decimals(self, token):
        assert token.decimals() == 18

    def test_initial_total_supply_is_zero(self, token):
        assert token.totalSupply() == 0

    def test_initial_balance_is_zero(self, token, alice):
        assert token.balanceOf(alice) == 0


class TestMint:
    def test_increases_balance(self, token, alice, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        assert token.balanceOf(alice) == 1_000 * 10**18

    def test_increases_total_supply(self, token, alice, owner):
        token.mint(alice, 500 * 10**18, sender=owner)
        assert token.totalSupply() == 500 * 10**18

    def test_multiple_mints_accumulate(self, token, alice, owner):
        token.mint(alice, 100 * 10**18, sender=owner)
        token.mint(alice, 200 * 10**18, sender=owner)
        assert token.balanceOf(alice) == 300 * 10**18
        assert token.totalSupply() == 300 * 10**18

    def test_mint_to_different_accounts(self, token, alice, bob, owner):
        token.mint(alice, 100 * 10**18, sender=owner)
        token.mint(bob, 200 * 10**18, sender=owner)
        assert token.balanceOf(alice) == 100 * 10**18
        assert token.balanceOf(bob) == 200 * 10**18
        assert token.totalSupply() == 300 * 10**18

    def test_mint_zero(self, token, alice, owner):
        token.mint(alice, 0, sender=owner)
        assert token.balanceOf(alice) == 0
        assert token.totalSupply() == 0


class TestApprove:
    def test_sets_allowance(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        assert token.allowance(alice, bob) == 500 * 10**18

    def test_overwrites_existing_allowance(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        token.approve(bob, 100 * 10**18, sender=alice)
        assert token.allowance(alice, bob) == 100 * 10**18

    def test_approve_zero_clears_allowance(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        token.approve(bob, 0, sender=alice)
        assert token.allowance(alice, bob) == 0

    def test_allowance_does_not_affect_other_spenders(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        assert token.allowance(alice, owner) == 0


class TestTransfer:
    def test_moves_tokens(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.transfer(bob, 400 * 10**18, sender=alice)
        assert token.balanceOf(alice) == 600 * 10**18
        assert token.balanceOf(bob) == 400 * 10**18

    def test_total_supply_unchanged(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.transfer(bob, 400 * 10**18, sender=alice)
        assert token.totalSupply() == 1_000 * 10**18

    def test_full_balance_transfer(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.transfer(bob, 1_000 * 10**18, sender=alice)
        assert token.balanceOf(alice) == 0
        assert token.balanceOf(bob) == 1_000 * 10**18

    def test_transfer_zero(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.transfer(bob, 0, sender=alice)
        assert token.balanceOf(alice) == 1_000 * 10**18
        assert token.balanceOf(bob) == 0

    def test_insufficient_balance_reverts(self, token, alice, bob, owner):
        token.mint(alice, 100 * 10**18, sender=owner)
        with pytest.raises(Exception, match="INSUFFICIENT_BALANCE"):
            token.transfer(bob, 101 * 10**18, sender=alice)

    def test_no_balance_reverts(self, token, alice, bob):
        with pytest.raises(Exception, match="INSUFFICIENT_BALANCE"):
            token.transfer(bob, 1, sender=alice)


class TestTransferFrom:
    def test_moves_tokens_within_allowance(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        token.transferFrom(alice, owner, 300 * 10**18, sender=bob)

        assert token.balanceOf(alice) == 700 * 10**18
        assert token.balanceOf(owner) == 300 * 10**18

    def test_reduces_allowance(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 500 * 10**18, sender=alice)
        token.transferFrom(alice, owner, 200 * 10**18, sender=bob)

        assert token.allowance(alice, bob) == 300 * 10**18

    def test_exceeds_allowance_reverts(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)
        token.approve(bob, 100 * 10**18, sender=alice)

        with pytest.raises(Exception, match="INSUFFICIENT_ALLOWANCE"):
            token.transferFrom(alice, owner, 101 * 10**18, sender=bob)

    def test_exceeds_balance_reverts(self, token, alice, bob, owner):
        token.mint(alice, 50 * 10**18, sender=owner)
        token.approve(bob, 1_000 * 10**18, sender=alice)

        with pytest.raises(Exception, match="INSUFFICIENT_BALANCE"):
            token.transferFrom(alice, owner, 51 * 10**18, sender=bob)

    def test_no_allowance_reverts(self, token, alice, bob, owner):
        token.mint(alice, 1_000 * 10**18, sender=owner)

        with pytest.raises(Exception, match="INSUFFICIENT_ALLOWANCE"):
            token.transferFrom(alice, owner, 1, sender=bob)

    def test_full_allowance_transfer(self, token, alice, bob, owner):
        amt = 1_000 * 10**18
        token.mint(alice, amt, sender=owner)
        token.approve(bob, amt, sender=alice)
        token.transferFrom(alice, bob, amt, sender=bob)

        assert token.balanceOf(alice) == 0
        assert token.balanceOf(bob) == amt
        assert token.allowance(alice, bob) == 0
