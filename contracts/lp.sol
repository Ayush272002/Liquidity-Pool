// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(
        address from,
        address to,
        uint value
    ) external returns (bool);
    function transfer(address to, uint value) external returns (bool);
    function balanceOf(address owner) external view returns (uint);
}

contract LiquidityPool {
    address public token0;
    address public token1;

    uint112 public reserve0;
    uint112 public reserve1;

    uint public totalSupply;
    mapping(address => uint) public balanceOf;

    bool private locked;

    modifier lock() {
        require(!locked, "LOCKED");
        locked = true;
        _;
        locked = false;
    }

    constructor(address _token0, address _token1) {
        token0 = _token0;
        token1 = _token1;
    }

    function addLiquidity(
        uint amount0,
        uint amount1
    ) external lock returns (uint liquidity) {
        IERC20(token0).transferFrom(msg.sender, address(this), amount0);
        IERC20(token1).transferFrom(msg.sender, address(this), amount1);

        if (totalSupply == 0) {
            liquidity = sqrt(amount0 * amount1);
        } else {
            liquidity = min(
                (amount0 * totalSupply) / reserve0,
                (amount1 * totalSupply) / reserve1
            );
        }

        require(liquidity > 0, "INSUFFICIENT_LIQUIDITY_MINTED");
        balanceOf[msg.sender] += liquidity;
        totalSupply += liquidity;

        _update();
    }

    function removeLiquidity(
        uint liquidity
    ) external lock returns (uint amount0, uint amount1) {
        require(balanceOf[msg.sender] >= liquidity, "NOT_ENOUGH");

        amount0 = (liquidity * reserve0) / totalSupply;
        amount1 = (liquidity * reserve1) / totalSupply;

        require(amount0 > 0 && amount1 > 0, "INSUFFICIENT_AMOUNT");

        balanceOf[msg.sender] -= liquidity;
        totalSupply -= liquidity;

        IERC20(token0).transfer(msg.sender, amount0);
        IERC20(token1).transfer(msg.sender, amount1);

        _update();
    }

    function swap(uint amount0Out, uint amount1Out) external lock {
        require(amount0Out > 0 || amount1Out > 0, "INVALID_OUTPUT");
        require(
            amount0Out < reserve0 && amount1Out < reserve1,
            "INSUFFICIENT_LIQ"
        );

        if (amount0Out > 0) IERC20(token0).transfer(msg.sender, amount0Out);
        if (amount1Out > 0) IERC20(token1).transfer(msg.sender, amount1Out);

        uint balance0 = IERC20(token0).balanceOf(address(this));
        uint balance1 = IERC20(token1).balanceOf(address(this));

        uint amount0In = balance0 > (reserve0 - amount0Out)
            ? balance0 - (reserve0 - amount0Out)
            : 0;

        uint amount1In = balance1 > (reserve1 - amount1Out)
            ? balance1 - (reserve1 - amount1Out)
            : 0;

        require(amount0In > 0 || amount1In > 0, "INSUFFICIENT_INPUT");

        // Apply 0.3% fee
        uint balance0Adjusted = (balance0 * 1000) - (amount0In * 3);
        uint balance1Adjusted = (balance1 * 1000) - (amount1In * 3);

        require(
            balance0Adjusted * balance1Adjusted >= uint(reserve0) * uint(reserve1) * (1000**2),
            "K"
        );

        _update();
    }

    function getReserves() external view returns (uint112, uint112) {
        return (reserve0, reserve1);
    }

    function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut)
        public
        pure
        returns (uint amountOut)
    {
        require(amountIn > 0, "INSUFFICIENT_INPUT");
        require(reserveIn > 0 && reserveOut > 0, "INSUFFICIENT_LIQ");

        uint amountInWithFee = amountIn * 997;
        amountOut = (amountInWithFee * reserveOut) /
            (reserveIn * 1000 + amountInWithFee);
    }

    function _update() private {
        reserve0 = uint112(IERC20(token0).balanceOf(address(this)));
        reserve1 = uint112(IERC20(token1).balanceOf(address(this)));
    }

    function sqrt(uint y) internal pure returns (uint z) {
        if (y > 3) {
            z = y;
            uint x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function min(uint x, uint y) private pure returns (uint) {
        return x < y ? x : y;
    }
}
