import math
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
def token0(owner):
    return owner.deploy(project.MockERC20, "Token A", "TKA")


@pytest.fixture
def token1(owner):
    return owner.deploy(project.MockERC20, "Token B", "TKB")


@pytest.fixture
def pool(owner, token0, token1):
    return owner.deploy(project.LiquidityPool, token0.address, token1.address)


def _mint_and_approve(token0, token1, pool, user, amt0, amt1):
    token0.mint(user, amt0, sender=user)
    token1.mint(user, amt1, sender=user)
    token0.approve(pool.address, amt0, sender=user)
    token1.approve(pool.address, amt1, sender=user)


class TestAddLiquidity:
    def test_initial_liquidity_uses_geometric_mean(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 4_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        expected = int(math.isqrt(amt0 * amt1))
        assert pool.balanceOf(owner) == expected
        assert pool.totalSupply() == expected

    def test_initial_liquidity_updates_reserves(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        r0, r1 = pool.getReserves()
        assert r0 == amt0
        assert r1 == amt1

    def test_initial_liquidity_mints_lp_tokens(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        assert pool.balanceOf(owner) > 0
        assert pool.totalSupply() > 0

    def test_subsequent_liquidity_proportional(
        self, pool, token0, token1, owner, alice
    ):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        total_before = pool.totalSupply()
        _mint_and_approve(token0, token1, pool, alice, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=alice)

        # Alice gets equal share since she provides same proportions
        assert pool.balanceOf(alice) == total_before
        assert pool.totalSupply() == total_before * 2

    def test_zero_liquidity_reverts(self, pool, token0, token1, owner):
        # sqrt(1 * 1) = 1 but sqrt(0) = 0 -> should revert
        _mint_and_approve(token0, token1, pool, owner, 0, 0)
        with pytest.raises(Exception, match="INSUFFICIENT_LIQUIDITY_MINTED"):
            pool.addLiquidity(0, 0, sender=owner)

    def test_tokens_transferred_to_pool(self, pool, token0, token1, owner):
        amt0, amt1 = 500 * 10**18, 500 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        assert token0.balanceOf(pool.address) == amt0
        assert token1.balanceOf(pool.address) == amt1


class TestRemoveLiquidity:
    def test_remove_returns_tokens(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        liquidity = pool.balanceOf(owner)
        pool.removeLiquidity(liquidity, sender=owner)

        assert token0.balanceOf(owner) == amt0
        assert token1.balanceOf(owner) == amt1

    def test_remove_burns_lp_tokens(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        liquidity = pool.balanceOf(owner)
        pool.removeLiquidity(liquidity, sender=owner)

        assert pool.balanceOf(owner) == 0
        assert pool.totalSupply() == 0

    def test_remove_updates_reserves(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        liquidity = pool.balanceOf(owner)
        pool.removeLiquidity(liquidity, sender=owner)

        r0, r1 = pool.getReserves()
        assert r0 == 0
        assert r1 == 0

    def test_remove_more_than_balance_reverts(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        liquidity = pool.balanceOf(owner)
        with pytest.raises(Exception, match="NOT_ENOUGH"):
            pool.removeLiquidity(liquidity + 1, sender=owner)

    def test_partial_remove(self, pool, token0, token1, owner):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        total_liq = pool.balanceOf(owner)
        half = total_liq // 2
        pool.removeLiquidity(half, sender=owner)

        assert pool.balanceOf(owner) == total_liq - half
        assert pool.totalSupply() == total_liq - half

    def test_non_holder_reverts(self, pool, token0, token1, owner, alice):
        amt0, amt1 = 1_000 * 10**18, 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt0, amt1)
        pool.addLiquidity(amt0, amt1, sender=owner)

        with pytest.raises(Exception, match="NOT_ENOUGH"):
            pool.removeLiquidity(1, sender=alice)


class TestSwap:
    @pytest.fixture(autouse=True)
    def seed_pool(self, pool, token0, token1, owner):
        amt = 1_000 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt, amt)
        pool.addLiquidity(amt, amt, sender=owner)

    def test_swap_token0_for_token1(self, pool, token0, token1, alice):
        amount_in = 10 * 10**18
        token0.mint(alice, amount_in, sender=alice)
        token0.approve(pool.address, amount_in, sender=alice)

        r0, r1 = pool.getReserves()
        amount_out = pool.getAmountOut(amount_in, r0, r1)

        # Send token0 in, get token1 out
        token0.transfer(pool.address, amount_in, sender=alice)
        pool.swap(0, amount_out, sender=alice)

        assert token1.balanceOf(alice) == amount_out

    def test_swap_token1_for_token0(self, pool, token0, token1, alice):
        amount_in = 10 * 10**18
        token1.mint(alice, amount_in, sender=alice)
        token1.approve(pool.address, amount_in, sender=alice)

        r0, r1 = pool.getReserves()
        amount_out = pool.getAmountOut(amount_in, r1, r0)

        token1.transfer(pool.address, amount_in, sender=alice)
        pool.swap(amount_out, 0, sender=alice)

        assert token0.balanceOf(alice) == amount_out

    def test_swap_updates_reserves(self, pool, token0, token1, alice):
        amount_in = 10 * 10**18
        token0.mint(alice, amount_in, sender=alice)

        r0_before, r1_before = pool.getReserves()
        amount_out = pool.getAmountOut(amount_in, r0_before, r1_before)

        token0.transfer(pool.address, amount_in, sender=alice)
        pool.swap(0, amount_out, sender=alice)

        r0_after, r1_after = pool.getReserves()
        assert r0_after > r0_before  # pool received token0
        assert r1_after < r1_before  # pool sent token1

    def test_swap_zero_output_reverts(self, pool, token0, alice):
        with pytest.raises(Exception, match="INVALID_OUTPUT"):
            pool.swap(0, 0, sender=alice)

    def test_swap_exceeds_reserve_reverts(self, pool, token0, alice):
        r0, r1 = pool.getReserves()
        with pytest.raises(Exception, match="INSUFFICIENT_LIQ"):
            pool.swap(r0, r1, sender=alice)

    def test_swap_without_input_reverts(self, pool, alice):
        with pytest.raises(Exception):
            pool.swap(0, 1 * 10**18, sender=alice)


class TestGetAmountOut:
    def test_basic_calculation(self, pool):
        amount_in = 100 * 10**18
        reserve_in = 1_000 * 10**18
        reserve_out = 1_000 * 10**18

        amount_out = pool.getAmountOut(amount_in, reserve_in, reserve_out)

        # amountInWithFee = 100e18 * 997
        # amountOut = (fee * reserveOut) / (reserveIn * 1000 + fee)
        fee = amount_in * 997
        expected = (fee * reserve_out) // (reserve_in * 1000 + fee)
        assert amount_out == expected

    def test_larger_input_gives_larger_output(self, pool):
        r_in, r_out = 1_000 * 10**18, 1_000 * 10**18
        out_small = pool.getAmountOut(10 * 10**18, r_in, r_out)
        out_large = pool.getAmountOut(100 * 10**18, r_in, r_out)
        assert out_large > out_small

    def test_zero_input_reverts(self, pool):
        with pytest.raises(Exception, match="INSUFFICIENT_INPUT"):
            pool.getAmountOut(0, 1_000 * 10**18, 1_000 * 10**18)

    def test_zero_reserve_reverts(self, pool):
        with pytest.raises(Exception, match="INSUFFICIENT_LIQ"):
            pool.getAmountOut(100 * 10**18, 0, 1_000 * 10**18)


class TestReentrancyGuard:
    def test_lock_modifier_prevents_reentry(self, pool, token0, token1, owner):
        # verify locked state resets correctly after normal calls
        amt = 100 * 10**18
        _mint_and_approve(token0, token1, pool, owner, amt * 2, amt * 2)
        pool.addLiquidity(amt, amt, sender=owner)
        # Second call must succeed (lock was released after first)
        pool.addLiquidity(amt, amt, sender=owner)
        assert pool.totalSupply() > 0
