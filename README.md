# Liquidity Pool

A Uniswap V2-style AMM liquidity pool implemented in Solidity, tested with the [Ape Framework](https://docs.apeworx.io/ape/stable/).

## Contracts

### `LiquidityPool.sol`
A constant-product AMM (`x * y = k`) with:
- `addLiquidity(uint amount0, uint amount1)` — deposit tokens, receive LP tokens (geometric mean on first deposit, proportional thereafter)
- `removeLiquidity(uint liquidity)` — burn LP tokens, receive proportional share of reserves
- `swap(uint amount0Out, uint amount1Out)` — swap with 0.3% fee, enforces the K invariant
- `getAmountOut(uint amountIn, uint reserveIn, uint reserveOut)` — quote output amount for a given input
- `getReserves()` — returns current `(reserve0, reserve1)`

### `MockERC20.sol`
Minimal ERC-20 used in tests. Supports `mint`, `transfer`, `transferFrom`, and `approve`.

## Project Structure

```
contracts/
  lp.sol              # LiquidityPool contract
  MockERC20.sol       # Test token
tests/
  test_lp.py          # 23 tests for LiquidityPool
  test_mock_erc20.py  # 26 tests for MockERC20
ape-config.yaml       # Ape project config (pinned solc 0.8.20)
```

## Setup

**Requirements:** Python 3.13+

```bash
uv sync
```

## Commands

**Compile**
```bash
ape compile                        # compile all contracts
ape compile --force                # recompile even if unchanged
```

**Test**
```bash
ape test                           # run all tests
ape test -v                        # verbose output
ape test -s                        # show print statements
ape test tests/test_lp.py          # LP tests only
ape test tests/test_mock_erc20.py  # ERC-20 tests only
ape test -k test_swap              # run tests matching a keyword
```

**Console (interactive)**
```bash
ape console --network ethereum:local:foundry
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.