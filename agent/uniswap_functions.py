from enum import (
    auto,
    Enum,
)
from statistics import quantiles
from typing import Optional, Dict, Any, Tuple, Union, Sequence, List, cast, TypedDict, TypeVar
from eth_account.messages import SignableMessage
from eth_account.signers.local import LocalAccount
from eth_account.account import SignedMessage
from web3 import Web3
from web3.types import (
    BlockIdentifier,
    ChecksumAddress,
    Nonce,
    Wei,
    HexBytes,
    HexStr,
    TxData,
    TxParams
)
from eth_abi import encode
from eth_abi.registry import registry
from eth_utils import keccak
from io import BytesIO
from web3.contract.contract import BaseContractFunction
from eth_abi.exceptions import DecodingError
from eth_abi import decode
from web3.exceptions import Web3Exception
import json
from datetime import datetime
from eth_account.messages import (
    encode_typed_data,
    SignableMessage,
)
from itertools import chain
from abc import ABC

class TransactionSpeed(Enum):
    SLOW = 0
    AVERAGE = 1
    FAST = 2
    FASTER = 3

_speed_multiplier = {
    TransactionSpeed.SLOW: 1,
    TransactionSpeed.AVERAGE: 1,
    TransactionSpeed.FAST: 1.25,
    TransactionSpeed.FASTER: 1.5,
}

class TransactionSpeed(Enum):
    SLOW = 0
    AVERAGE = 1
    FAST = 2
    FASTER = 3

def compute_gas_fees(
        w3: Web3,
        trx_speed: TransactionSpeed = TransactionSpeed.FAST,
        block_identifier: BlockIdentifier = "latest") -> Tuple[Wei, Wei]:
    """
    Compute the priority_fee (maxPriorityFeePerGas) and max_fee_per_gas (maxFeePerGas) according to the given
    transaction 'speed'. All speeds will compute gas fees in order to try to place the transaction in the next block
    (without certainty, of course).
    Higher speeds would place the transaction higher in the block than lower ones.
    So, during strained conditions, the computed gas fees could be very high and should be double-checked before
    using them.

    :param w3: valid Web3 instance
    :param trx_speed: the desired transaction 'speed'
    :param block_identifier: the block number or identifier, default to 'latest'
    :return: the tuple (priority_fee, max_fee_per_gas)
    """
    block = w3.eth.get_block(block_identifier, True)
    transactions = cast(Sequence[TxData], block["transactions"])
    tips = [
        int(trx.get("maxPriorityFeePerGas", 0))
        for trx
        in transactions
        if trx.get("maxPriorityFeePerGas", 0) > 0
    ]
    if len(tips) < 3:
        priority_fee = 1
    else:
        quintiles = quantiles(tips, n=5, method="inclusive")
        priority_fee = int(quintiles[trx_speed.value] * _speed_multiplier[trx_speed])

    base_fee = block["baseFeePerGas"]
    max_fee_per_gas = int(base_fee * 1.5 + priority_fee)

    return Wei(priority_fee), Wei(max_fee_per_gas)

def compute_sqrt_price_x96(amount_0: Wei, amount_1: Wei) -> int:
    """
    Compute the sqrtPriceX96
    :param amount_0: amount of PoolKey.currency_0
    :param amount_1: amount of PoolKey.currency_1
    :return: floor(sqrt(amount_1 / amount_0) * 2^96)
    """
    return int(pow(amount_1 / amount_0, 1/2) * 2**96)

TV4ChainedCommonFunctionBuilder = TypeVar("TV4ChainedCommonFunctionBuilder", bound="_V4ChainedCommonFunctionBuilder")

_permit2_address = Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")
_permit2_domain_data = {'name': 'Permit2', 'chainId': 1, 'verifyingContract': _permit2_address}
_ur_address = Web3.to_checksum_address("0x66a9893cC07D91D95644AEDD05D03f95e1dBA8Af")
_permit2_types = {
    'PermitDetails': [
        {'name': 'token', 'type': 'address'},
        {'name': 'amount', 'type': 'uint160'},
        {'name': 'expiration', 'type': 'uint48'},
        {'name': 'nonce', 'type': 'uint48'},
    ],
    'PermitSingle': [
        {'name': 'details', 'type': 'PermitDetails'},
        {'name': 'spender', 'type': 'address'},
        {'name': 'sigDeadline', 'type': 'uint256'},
    ],
}

class PoolKey(TypedDict):
    """
    Use v4_pool_key() to make sure currency_0 < currency_1
    """
    currency_0: ChecksumAddress
    currency_1: ChecksumAddress
    fee: int
    tick_spacing: int
    hooks: ChecksumAddress

class PathKey(TypedDict):
    intermediate_currency: ChecksumAddress
    fee: int
    tick_spacing: int
    hooks: ChecksumAddress
    hook_data: bytes

class _RouterConstant(Enum):
    # https://github.com/Uniswap/universal-router/blob/main/contracts/libraries/Constants.sol
    MSG_SENDER = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")
    ADDRESS_THIS = Web3.to_checksum_address("0x0000000000000000000000000000000000000002")
    ROUTER_BALANCE = Wei(2**255)
    FLAG_ALLOW_REVERT = 0x80
    COMMAND_TYPE_MASK = 0x3f

class RouterFunction(Enum):
    # https://docs.uniswap.org/contracts/universal-router/technical-reference#command
    V3_SWAP_EXACT_IN = 0
    V3_SWAP_EXACT_OUT = 1
    PERMIT2_TRANSFER_FROM = 2
    SWEEP = 4
    TRANSFER = 5
    PAY_PORTION = 6
    V2_SWAP_EXACT_IN = 8
    V2_SWAP_EXACT_OUT = 9
    PERMIT2_PERMIT = 10
    WRAP_ETH = 11
    UNWRAP_WETH = 12
    V4_SWAP = 16
    V4_INITIALIZE_POOL = 19
    V4_POSITION_MANAGER_CALL = 20

class V4Actions(Enum):
    # https://github.com/Uniswap/v4-periphery/blob/main/src/libraries/Actions.sol
    # Positions
    MINT_POSITION = 0x02
    MINT_POSITION_FROM_DELTAS = 0x05
    SETTLE_PAIR = 0x0d
    TAKE_PAIR = 0x11
    CLOSE_CURRENCY = 0x12
    CLEAR_OR_TAKE = 0x13
    SWEEP = 0x14
    WRAP = 0x15
    UNWRAP = 0x16

    # Swaps
    SWAP_EXACT_IN_SINGLE = 0x06
    SWAP_EXACT_IN = 0x07
    SWAP_EXACT_OUT_SINGLE = 0x08
    SWAP_EXACT_OUT = 0x09
    SETTLE_ALL = 0x0c
    TAKE_ALL = 0x0f
    TAKE_PORTION = 0x10

    # Common
    SETTLE = 0x0b
    TAKE = 0x0e

class MiscFunctions(Enum):
    EXECUTE = auto()
    EXECUTE_WITH_DEADLINE = auto()  # value = "execute" would be nice, but enum names and values must be unique
    UNLOCK_DATA = auto()
    V4_POOL_ID = auto()

    STRICT_V4_SWAP_EXACT_IN = auto()
    STRICT_V4_SWAP_EXACT_OUT = auto()

def _get_types_from_list(type_list: List[Any]) -> List[str]:
    types = []
    for item in type_list:
        if item["type"][:5] == "tuple":
            brackets = item["type"][5:]
            types.append(f"({','.join(_get_types_from_list(item['components']))}){brackets}")
        else:
            types.append(item["type"])
    return types

def build_abi_type_list(abi_dict: Dict[str, Any]) -> List[str]:
    return _get_types_from_list(abi_dict["inputs"])

class FunctionABI:
    def __init__(self, inputs: List[Any], name: str, _type: str) -> None:
        self.inputs = inputs
        self.name = name
        self.type = _type

    def get_abi(self) -> Dict[str, Any]:
        return {"inputs": self.inputs, "name": self.name, "type": self.type}

    def get_struct_abi(self) -> Dict[str, Any]:
        result = self.get_abi()
        result["components"] = result.pop("inputs")
        return result

    def get_full_abi(self) -> List[Dict[str, Any]]:
        return [self.get_abi()]

    def get_abi_types(self) -> List[str]:
        return build_abi_type_list(self.get_abi())

    def get_signature(self) -> str:
        return f"{self.name}({','.join(self.get_abi_types())})"

    def get_selector(self) -> bytes:
        return keccak(text=self.get_signature())[:4]

    def encode(self, args: Sequence[Any]) -> bytes:
        return encode(self.get_abi_types(), args)

ABIMap = Dict[Union[MiscFunctions, RouterFunction, V4Actions], FunctionABI]

class FunctionRecipient(Enum):
    """
    SENDER: When the function recipient is the sender

    ROUTER: When the function recipient is the router

    CUSTOM: When the function recipient is neither the trx sender nor the router
    """
    SENDER = "recipient is transaction sender"
    ROUTER = "recipient is universal router"
    CUSTOM = "recipient is custom"


class _V4ChainedCommonFunctionBuilder(ABC):
    def __init__(self, builder: "_ChainedFunctionBuilder", w3: Web3, abi_map: ABIMap):
        self.builder = builder
        self._w3 = w3
        self._abi_map = abi_map
        self.actions: bytearray = bytearray()
        self.arguments: List[bytes] = []

    def _add_action(self, action: V4Actions, args: Sequence[Any]) -> None:
        abi = self._abi_map[action]
        self.actions.append(action.value)
        self.arguments.append(abi.encode(args))

    def settle(
            self: TV4ChainedCommonFunctionBuilder,
            currency: ChecksumAddress,
            amount: int,
            payer_is_user: bool) -> TV4ChainedCommonFunctionBuilder:
        """
        Pay the contract for a given amount of tokens (currency). Used for swaps and position management.

        :param currency: The token addr or "0x0000000000000000000000000000000000000000" for the native currency (ie ETH)
        :param amount: The amount to send to the contract
        :param payer_is_user: Whether this amount comes from the transaction sender or not.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, amount, payer_is_user)
        self._add_action(V4Actions.SETTLE, args)
        return self

    def take(
            self: TV4ChainedCommonFunctionBuilder,
            currency: ChecksumAddress,
            recipient: ChecksumAddress,
            amount: int) -> TV4ChainedCommonFunctionBuilder:
        """
        Get the given amount of tokens (currency) from the contract. Used for swaps and position management.

        :param currency: The token addr or "0x0000000000000000000000000000000000000000" for the native currency (ie ETH)
        :param recipient: Address of who gets the tokens
        :param amount: The token amount to get
        :return: The chain link corresponding to this function call.
        """
        args = (currency, recipient, amount)
        self._add_action(V4Actions.TAKE, args)
        return self


class _V4ChainedPositionFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def mint_position(
            self,
            pool_key: PoolKey,
            tick_lower: int,
            tick_upper: int,
            liquidity: int,
            amount_0_max: int,
            amount_1_max: int,
            recipient: ChecksumAddress,
            hook_data: bytes) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Mint a V4 position, ie add some liquidity to a given pool and get a position as ERC-721 token.

        :param pool_key: The PoolKey to identify the pool where the liquidity will be added to.
        :param tick_lower: The lower tick boundary of the position
        :param tick_upper: The upper tick boundary of the position
        :param liquidity: The amount of liquidity units to mint
        :param amount_0_max: The maximum amount of currency_0 the sender is willing to pay
        :param amount_1_max: The maximum amount of currency_1 the sender is willing to pay
        :param recipient: The address that will receive the liquidity position (ERC-721)
        :param hook_data: The encoded hook data to be forwarded to the hook functions
        :return: The chain link corresponding to this function call.
        """
        args = (
            tuple(pool_key.values()),
            tick_lower,
            tick_upper,
            liquidity,
            amount_0_max,
            amount_1_max,
            recipient,
            hook_data
        )
        self._add_action(V4Actions.MINT_POSITION, args)
        return self

    def settle_pair(
            self,
            currency_0: ChecksumAddress,
            currency_1: ChecksumAddress) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Indicates that tokens are to be paid by the caller to create the position.

        :param currency_0: The address of 1 token
        :param currency_1: The address of the other token
        :return: The chain link corresponding to this function call.
        """
        args = (currency_0, currency_1)
        self._add_action(V4Actions.SETTLE_PAIR, args)
        return self

    def close_currency(self, currency: ChecksumAddress) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Automatically determines if a currency should be settled or taken.

        :param currency: The token or ETH to be paid or received.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, )
        self._add_action(V4Actions.CLOSE_CURRENCY, args)
        return self

    def sweep(self, currency: ChecksumAddress, to: ChecksumAddress) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Sweep the contract

        :param currency: The token or ETH address to sweep
        :param to: The sweep recipient address
        :return: The chain link corresponding to this function call.
        """
        args = (currency, to)
        self._add_action(V4Actions.SWEEP, args)
        return self

    # def mint_position_from_deltas(
    #         self,
    #         pool_key: PoolKey,
    #         tick_lower: int,
    #         tick_upper: int,
    #         amount_0_max: int,
    #         amount_1_max: int,
    #         recipient: ChecksumAddress,
    #         hook_data: bytes) -> _V4ChainedPositionFunctionBuilder:
    #     args = (
    #         tuple(pool_key.values()),
    #         tick_lower,
    #         tick_upper,
    #         amount_0_max,
    #         amount_1_max,
    #         recipient,
    #         hook_data
    #     )
    #     self._add_action(V4Actions.MINT_POSITION_FROM_DELTAS, args)
    #     return self

    def wrap_eth(self, amount: Wei) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Encode the call to the function WRAP which convert ETH to WETH in the position manager contract

        :param amount: The amount of ETH in Wei.
        :return: The chain link corresponding to this function call.
        """
        args = (amount, )
        self._add_action(V4Actions.WRAP, args)
        return self

    def unwrap_weth(self, amount: Wei) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - Encode the call to the function UNWRAP which convert WETH to ETH in the position manager contract

        :param amount: The amount of WETH in Wei.
        :return: The chain link corresponding to this function call.
        """
        args = (amount, )
        self._add_action(V4Actions.UNWRAP, args)
        return self

    def take_pair(
            self,
            currency_0: ChecksumAddress,
            currency_1: ChecksumAddress,
            recipient: ChecksumAddress) -> "_V4ChainedPositionFunctionBuilder":
        args = (currency_0, currency_1, recipient)
        self._add_action(V4Actions.TAKE_PAIR, args)
        return self

    def clear_or_take(
            self,
            currency: ChecksumAddress,
            amount_max: int) -> "_V4ChainedPositionFunctionBuilder":
        """
        Position - If the token amount to-be-collected is below a threshold, opt to forfeit the dust.
        Otherwise, claim the tokens.

        :param currency: The token or ETH address to be forfeited or claimed.
        :param amount_max: The threshold.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, amount_max)
        self._add_action(V4Actions.CLEAR_OR_TAKE, args)
        return self

    def build_v4_posm_call(self, deadline: int) -> "_ChainedFunctionBuilder":
        """
        Position - Build the V4 position manager call

        :param deadline: When this call is not valid anymore
        :return: The chain link corresponding to this function call.
        """
        action_values = (bytes(self.actions), self.arguments)
        abi = self._abi_map[MiscFunctions.UNLOCK_DATA]
        encoded_data = abi.encode(action_values)
        args = (encoded_data, deadline)
        self.builder._add_command(RouterFunction.V4_POSITION_MANAGER_CALL, args, True)
        return self.builder




class _ChainedFunctionBuilder:
    def __init__(self, w3: Web3, abi_map: ABIMap):
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self.commands: bytearray = bytearray()
        self.arguments: List[bytes] = []

    def _add_command(self, command: RouterFunction, args: Sequence[Any], add_selector: bool = False) -> None:
        abi = self._abi_map[command]
        self.commands.append(command.value)
        arguments = abi.get_selector() + abi.encode(args) if add_selector else abi.encode(args)
        self.arguments.append(arguments)

    @staticmethod
    def _get_recipient(
            function_recipient: FunctionRecipient,
            custom_recipient: Optional[ChecksumAddress] = None) -> ChecksumAddress:
        recipient_mapping = {
            FunctionRecipient.SENDER: _RouterConstant.MSG_SENDER.value,
            FunctionRecipient.ROUTER: _RouterConstant.ADDRESS_THIS.value,
            FunctionRecipient.CUSTOM: custom_recipient,
        }
        recipient = recipient_mapping[function_recipient]
        if recipient:
            return Web3.to_checksum_address(recipient)
        else:
            raise ValueError(
                f"Invalid function_recipient: {function_recipient} or custom_recipient: {custom_recipient}: "
                f"custom_recipient address must be provided if FunctionRecipient.CUSTOM is selected."
            )

    @staticmethod
    def _get_command(router_function: RouterFunction, revert_on_fail: bool) -> int:
        return int(router_function.value if revert_on_fail else router_function.value | 0x80)

    def wrap_eth(
            self,
            function_recipient: FunctionRecipient,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function WRAP_ETH which convert ETH to WETH through the UR

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount: The amount of sent ETH in WEI.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount)
        self._add_command(RouterFunction.WRAP_ETH, args)
        return self

    def unwrap_weth(
            self,
            function_recipient: FunctionRecipient,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function UNWRAP_WETH which convert WETH to ETH through the UR

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount: The amount of sent WETH in WEI.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount)
        self._add_command(RouterFunction.UNWRAP_WETH, args)
        return self

    def v2_swap_exact_in(
            self,
            function_recipient: FunctionRecipient,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V2_SWAP_EXACT_IN, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount_in, amount_out_min, path, payer_is_sender)
        self._add_command(RouterFunction.V2_SWAP_EXACT_IN, args)
        return self

    def v2_swap_exact_in_from_balance(
            self,
            function_recipient: FunctionRecipient,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V2_SWAP_EXACT_IN, using the router balance as amount_in,
        which swaps tokens on Uniswap V2.
        Typically used when the amount_in is unknown because it comes from a V*_SWAP_EXACT_IN output.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        return self.v2_swap_exact_in(
            function_recipient,
            _RouterConstant.ROUTER_BALANCE.value,
            amount_out_min,
            path,
            custom_recipient,
            False,
        )

    def v2_swap_exact_out(
            self,
            function_recipient: FunctionRecipient,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V2_SWAP_EXACT_OUT, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount_out, amount_in_max, path, payer_is_sender)
        self._add_command(RouterFunction.V2_SWAP_EXACT_OUT, args)
        return self

    def v3_swap_exact_in(
            self,
            function_recipient: FunctionRecipient,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V3_SWAP_EXACT_IN, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        encoded_v3_path = _Encoder.v3_path(RouterFunction.V3_SWAP_EXACT_IN.name, path)
        args = (recipient, amount_in, amount_out_min, encoded_v3_path, payer_is_sender)
        self._add_command(RouterFunction.V3_SWAP_EXACT_IN, args)
        return self

    def v3_swap_exact_in_from_balance(
            self,
            function_recipient: FunctionRecipient,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V3_SWAP_EXACT_IN, using the router balance as amount_in,
        which swaps tokens on Uniswap V3.
        Typically used when the amount_in is unknown because it comes from a V*_SWAP_EXACT_IN output.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out_min: The minimum accepted bought token (token_out) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        return self.v3_swap_exact_in(
            function_recipient,
            _RouterConstant.ROUTER_BALANCE.value,
            amount_out_min,
            path,
            custom_recipient,
            False,
        )

    def v3_swap_exact_out(
            self,
            function_recipient: FunctionRecipient,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function V3_SWAP_EXACT_OUT, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        encoded_v3_path = _Encoder.v3_path(RouterFunction.V3_SWAP_EXACT_OUT.name, path)
        args = (recipient, amount_out, amount_in_max, encoded_v3_path, payer_is_sender)
        self._add_command(RouterFunction.V3_SWAP_EXACT_OUT, args)
        return self

    def permit2_permit(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function PERMIT2_PERMIT, which gives token allowances to the Permit2 contract.
        In addition, the Permit2 must be approved using the token contracts as usual.

        :param permit_single: The 1st element returned by create_permit2_signable_message()
        :param signed_permit_single: The 2nd element returned by create_permit2_signable_message(), once signed.

        :return: The chain link corresponding to this function call.
        """
        struct = (
            tuple(permit_single["details"].values()),
            permit_single["spender"],
            permit_single["sigDeadline"],
        )
        args = (struct, signed_permit_single.signature)
        self._add_command(RouterFunction.PERMIT2_PERMIT, args)
        return self

    def sweep(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            amount_min: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function SWEEP which sweeps all of the router's ERC20 or ETH to an address

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of the token to sweep or "0x0000000000000000000000000000000000000000" for ETH.
        :param amount_min: The minimum desired amount
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, amount_min)
        self._add_command(RouterFunction.SWEEP, args)
        return self

    def pay_portion(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            bips: int,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function PAY_PORTION which transfers a part of the router's ERC20 or ETH to an address.
        Transferred amount = balance * bips / 10_000

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of token to pay or "0x0000000000000000000000000000000000000000" for ETH.
        :param bips: integer between 0 and 10_000
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        if (
            bips < 0
            or bips > 10_000
            or not isinstance(bips, int)
        ):
            raise ValueError(f"Invalid argument: bips must be an int between 0 and 10_000. Received {bips}")

        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, bips)
        self._add_command(RouterFunction.PAY_PORTION, args)
        return self

    def transfer(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            value: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the call to the function TRANSFER which transfers an amount of ERC20 or ETH from the router's balance
        to an address.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of token to pay or "0x0000000000000000000000000000000000000000" for ETH.
        :param value: The amount to transfer (in Wei)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """

        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, value)
        self._add_command(RouterFunction.TRANSFER, args)
        return self

    def permit2_transfer_from(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> "_ChainedFunctionBuilder":
        """
        Encode the transfer of tokens from the caller address to the given recipient.
        The UR must have been permit2'ed for the token first.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of the token to be transferred.
        :param amount: The amount to transfer.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, amount)
        self._add_command(RouterFunction.PERMIT2_TRANSFER_FROM, args)
        return self

    def v4_swap(self) -> "_V4ChainedSwapFunctionBuilder":
        """
        V4 - Start building a call to the V4 swap functions

        :return: The chain link corresponding to this function call.
        """
        return _V4ChainedSwapFunctionBuilder(self, self._w3, self._abi_map)

    def v4_initialize_pool(self, pool_key: PoolKey, amount_0: Wei, amount_1: Wei) -> "_ChainedFunctionBuilder":
        """
        V4 - Encode the call to initialize (create) a V4 pool.
        The amounts are used to compute the initial sqrtPriceX96. They are NOT sent.
        So, basically only the ratio amount_0 / amount_1 is relevant.
        For ex, to create a pool with 2 USD stable coins, you just need to set amount_0 = amount_1 = 1

        :param pool_key: The pool key that identify the pool to create
        :param amount_0: "virtual" amount of PoolKey.currency_0
        :param amount_1: "virtual" amount of PoolKey.currency_1
        :return: The chain link corresponding to this function call.
        """
        sqrt_price_x96 = compute_sqrt_price_x96(amount_0, amount_1)
        args = (tuple(pool_key.values()), sqrt_price_x96)
        self._add_command(RouterFunction.V4_INITIALIZE_POOL, args)
        return self

    def v4_posm_call(self) -> _V4ChainedPositionFunctionBuilder:
        """
        V4 - Start building a call to the V4 positon manager functions
        :return: The chain link corresponding to this function call.
        """
        return _V4ChainedPositionFunctionBuilder(self, self._w3, self._abi_map)

    def build(self, deadline: Optional[int] = None) -> HexStr:
        """
        Build the encoded input for all the chained commands, ready to be sent to the UR

        :param deadline: The optional unix timestamp after which the transaction won't be valid anymore.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        if deadline:
            execute_with_deadline_args = (bytes(self.commands), self.arguments, deadline)
            abi = self._abi_map[MiscFunctions.EXECUTE_WITH_DEADLINE]
            return Web3.to_hex(abi.get_selector() + abi.encode(execute_with_deadline_args))
        else:
            execute_args = (bytes(self.commands), self.arguments)
            abi = self._abi_map[MiscFunctions.EXECUTE]
            return Web3.to_hex(abi.get_selector() + abi.encode(execute_args))

    def build_transaction(
            self,
            sender: ChecksumAddress,
            value: Wei = Wei(0),
            trx_speed: Optional[TransactionSpeed] = TransactionSpeed.FAST,
            *,
            priority_fee: Optional[Wei] = None,
            max_fee_per_gas: Optional[Wei] = None,
            max_fee_per_gas_limit: Wei = Wei(100 * 10 ** 9),
            gas_limit: Optional[int] = None,
            chain_id: int = 8453,
            nonce: Optional[Union[int, Nonce]] = None,
            ur_address: ChecksumAddress = _ur_address,
            deadline: Optional[int] = None,
            block_identifier: BlockIdentifier = "latest") -> TxParams:
        """
        Build the encoded data and the transaction dictionary, ready to be signed.

        By default, compute the gas fees, chain_id, nonce, deadline, ... but custom values can be used instead.
        Gas fees are computed with a given TransactionSpeed (default is FAST).
        All speeds will compute gas fees in order to try to place the transaction in the next block
        (without certainty, of course).
        So, during strained conditions, the computed gas fees could be very high but can be controlled
        thanks to 'max_fee_per_gas_limit'.

        Either a transaction speed is provided or custom gas fees, otherwise a ValueError is raised.

        The RouterCodec must be built with a Web3 instance or a rpc endpoint address except if custom values are used.

        :param sender: The 'from' field - Mandatory
        :param value: The quantity of ETH sent to the Universal Router - Default is 0
        :param trx_speed: The indicative 'speed' of the transaction - Default is TransactionSpeed.FAST
        :param priority_fee: custom 'maxPriorityFeePerGas' - Default is None
        :param max_fee_per_gas: custom 'maxFeePerGas' - Default is None
        :param max_fee_per_gas_limit: if the computed 'max_fee_per_gas' is greater than 'max_fee_per_gas_limit', raise a ValueError  # noqa
        :param gas_limit: custom 'gas' - Default is None
        :param chain_id: custom 'chainId'
        :param nonce: custom 'nonce'
        :param ur_address: custom Universal Router address
        :param deadline: The optional unix timestamp after which the transaction won't be valid anymore.
        :param block_identifier: specify at what block the computing is done. Mostly for test purposes.
        :return: a transaction (TxParams) ready to be signed
        """
        encoded_data = self.build(deadline)

        print("🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡🧡", self._w3.provider.is_connected())

        if chain_id is None:
            chain_id = self._w3.eth.chain_id

        if nonce is None:
            nonce = self._w3.eth.get_transaction_count(sender, block_identifier)

        if not trx_speed:
            if priority_fee is None or max_fee_per_gas is None:
                raise ValueError("Either trx_speed or both priority_fee and max_fee_per_gas must be set.")
            else:
                _priority_fee = priority_fee
                _max_fee_per_gas = max_fee_per_gas
        else:
            if priority_fee or max_fee_per_gas:
                raise ValueError("priority_fee and max_fee_per_gas can't be set with trx_speed")
            else:
                _priority_fee, _max_fee_per_gas = compute_gas_fees(self._w3, trx_speed, block_identifier)
                if _max_fee_per_gas > max_fee_per_gas_limit:
                    raise ValueError(
                        "Computed max_fee_per_gas is greater than max_fee_per_gas_limit. "
                        "Either provide max_fee_per_gas, increase max_fee_per_gas_limit "
                        "or wait for less strained conditions"
                    )

        tx_params: TxParams = {
            "from": sender,
            "value": value,
            "to": ur_address,
            "chainId": chain_id,
            "nonce": Nonce(nonce),
            "type": HexStr('0x2'),
            "maxPriorityFeePerGas": _priority_fee,
            "maxFeePerGas": _max_fee_per_gas,
            "data": encoded_data,
        }

        if gas_limit is None:
            estimated_gas = self._w3.eth.estimate_gas(tx_params, block_identifier)
            gas_limit = int(estimated_gas * 1.15)

        tx_params["gas"] = Wei(gas_limit)

        return tx_params


class _V4ChainedSwapFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def swap_exact_in_single(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_in: Wei,
            amount_out_min: Wei,
            hook_data: bytes = b'') -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Encode the call to the V4_SWAP function SWAP_EXACT_IN_SINGLE.

        :param pool_key: the target pool key returned by encode.v4_pool_key()
        :param zero_for_one: the swap direction, true for currency_0 to currency_1, false for currency_1 to currency_0
        :param amount_in: the exact amount of the sold currency in Wei
        :param amount_out_min: the minimum accepted bought currency
        :param hook_data: encoded data sent to the pool's hook, if any.
        :return: The chain link corresponding to this function call.
        """
        args = ((tuple(pool_key.values()), zero_for_one, amount_in, amount_out_min, hook_data),)
        self._add_action(V4Actions.SWAP_EXACT_IN_SINGLE, args)
        return self

    def take_all(self, currency: ChecksumAddress, min_amount: Wei) -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Final action that collects all output tokens after the swap is complete.

        :param currency: The address of the token or ETH ("0x0000000000000000000000000000000000000000") to receive
        :param min_amount: The expected minimum amount to be received.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, min_amount)
        self._add_action(V4Actions.TAKE_ALL, args)
        return self

    def settle_all(self, currency: ChecksumAddress, max_amount: Wei) -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Final action that ensures all input tokens involved in the swap are properly paid to the contract.

        :param currency: The address of the token or ETH ("0x0000000000000000000000000000000000000000") to pay.
        :param max_amount: The expected maximum amount to pay.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, max_amount)
        self._add_action(V4Actions.SETTLE_ALL, args)
        return self

    def swap_exact_in(
            self,
            currency_in: ChecksumAddress,
            path_keys: Sequence[PathKey],
            amount_in: int,
            amount_out_min: int) -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Encode Multi-hop V4 SWAP_EXACT_IN swaps.

        :param currency_in: The address of the token (or ETH) to send to the first pool.
        :param path_keys: The sequence of path keys to identify the pools
        :param amount_in: The amount to send to the contract
        :param amount_out_min: The expected minimum amount to be received
        :return: The chain link corresponding to this function call.
        """
        args = ((currency_in, [tuple(path_key.values()) for path_key in path_keys], amount_in, amount_out_min), )
        self._add_action(V4Actions.SWAP_EXACT_IN, args)
        return self

    def swap_exact_out_single(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_out: Wei,
            amount_in_max: Wei,
            hook_data: bytes = b'') -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Encode the call to the V4_SWAP function SWAP_EXACT_IN_SINGLE.

        :param pool_key: the target pool key returned by encode.v4_pool_key()
        :param zero_for_one: the swap direction, true for currency_0 to currency_1, false for currency_1 to currency_0
        :param amount_out: the exact amount of the bought currency in Wei
        :param amount_in_max: the maximum accepted sold currency
        :param hook_data: encoded data sent to the pool's hook, if any.
        :return: The chain link corresponding to this function call.
        """
        args = ((tuple(pool_key.values()), zero_for_one, amount_out, amount_in_max, hook_data),)
        self._add_action(V4Actions.SWAP_EXACT_OUT_SINGLE, args)
        return self

    def swap_exact_out(
            self,
            currency_out: ChecksumAddress,
            path_keys: Sequence[PathKey],
            amount_out: int,
            amount_in_max: int) -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Encode Multi-hop V4 SWAP_EXACT_OUT swaps.

        :param currency_out: The address of the token (or ETH) to be received
        :param path_keys: The sequence of path keys to identify the pools
        :param amount_out: The amount to be received
        :param amount_in_max: The maximum amount that the transaction sender is willing to pay.
        :return: The chain link corresponding to this function call.
        """
        args = ((currency_out, [tuple(path_key.values()) for path_key in path_keys], amount_out, amount_in_max), )
        self._add_action(V4Actions.SWAP_EXACT_OUT, args)
        return self

    def take_portion(
            self,
            currency: ChecksumAddress,
            recipient: ChecksumAddress,
            bips: int) -> "_V4ChainedSwapFunctionBuilder":
        """
        Swap - Send a portion of token to a given recipient.

        :param currency: The address of the token (or ETH) to use for this action
        :param recipient: The address which will receive the tokens
        :param bips: The recipient will receive balance * bips / 10_000
        :return: The chain link corresponding to this function call.
        """
        args = (currency, recipient, bips)
        self._add_action(V4Actions.TAKE_PORTION, args)
        return self

    def build_v4_swap(self) -> _ChainedFunctionBuilder:
        """
        Build the V4 swap call

        :return: The chain link corresponding to this function call.
        """
        args = (bytes(self.actions), self.arguments)
        self.builder._add_command(RouterFunction.V4_SWAP, args)
        return self.builder


class FunctionABIBuilder:
    def __init__(self, fct_name: str, _type: str = "function") -> None:
        self.abi = FunctionABI(inputs=[], name=fct_name, _type=_type)

    def add_address(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "address"})
        return self

    def add_uint256(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "uint256"})
        return self

    def add_uint160(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "uint160"})
        return self

    def add_uint48(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "uint48"})
        return self

    def add_uint24(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "uint24"})
        return self

    def add_int24(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "int24"})
        return self

    def add_uint128(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "uint128"})
        return self

    def add_address_array(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "address[]"})
        return self

    def add_bool(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "bool"})
        return self

    def build(self) -> FunctionABI:
        return self.abi

    @staticmethod
    def create_struct_array(arg_name: str) -> "FunctionABIBuilder":
        return FunctionABIBuilder(arg_name, "tuple[]")

    @staticmethod
    def create_struct(arg_name: str) -> "FunctionABIBuilder":
        return FunctionABIBuilder(arg_name, "tuple")

    def add_struct(self, struct: "FunctionABIBuilder") -> "FunctionABIBuilder":
        self.abi.inputs.append(struct.abi.get_struct_abi())
        return self

    def add_struct_array(self, struct_array: "FunctionABIBuilder") -> "FunctionABIBuilder":
        self.abi.inputs.append(struct_array.abi.get_struct_abi())
        return self

    def add_bytes(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "bytes"})
        return self

    def add_bytes_array(self, arg_name: str) -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "bytes[]"})
        return self

    def add_v4_exact_input_params(self, arg_name: str = "params") -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "ExactInputParams"})
        return self

    def add_v4_exact_output_params(self, arg_name: str = "params") -> "FunctionABIBuilder":
        self.abi.inputs.append({"name": arg_name, "type": "ExactOutputParams"})
        return self

class _ABIBuilder:
    def __init__(self, w3: Optional[Web3] = None) -> None:
        if w3:
            print("🩷")
        else:
            print("🩷🩷")

        self.w3 = w3 if w3 else Web3()
        self.abi_map = self.build_abi_map()
        if not registry.has_encoder("ExactInputParams"):
            registry.register("ExactInputParams", self.encode_v4_exact_input_params, self.decode_v4_exact_input_params)
        if not registry.has_encoder("ExactOutputParams"):
            registry.register(
                "ExactOutputParams",
                self.encode_v4_exact_output_params,
                self.decode_v4_exact_output_params,
            )

    def build_abi_map(self) -> ABIMap:
        abi_map: ABIMap = {
            # mapping between command identifier and function abi
            RouterFunction.V3_SWAP_EXACT_IN: self._build_v3_swap_exact_in(),
            RouterFunction.V3_SWAP_EXACT_OUT: self._build_v3_swap_exact_out(),
            RouterFunction.V2_SWAP_EXACT_IN: self._build_v2_swap_exact_in(),
            RouterFunction.V2_SWAP_EXACT_OUT: self._build_v2_swap_exact_out(),
            RouterFunction.PERMIT2_PERMIT: self._build_permit2_permit(),
            RouterFunction.WRAP_ETH: self._build_wrap_eth(),
            RouterFunction.UNWRAP_WETH: self._build_unwrap_weth(),
            RouterFunction.SWEEP: self._build_sweep(),
            RouterFunction.PAY_PORTION: self._build_pay_portion(),
            RouterFunction.TRANSFER: self._build_transfer(),
            RouterFunction.V4_SWAP: self._build_v4_swap(),
            RouterFunction.V4_INITIALIZE_POOL: self._build_v4_initialize_pool(),
            RouterFunction.V4_POSITION_MANAGER_CALL: self._build_modify_liquidities(),
            RouterFunction.PERMIT2_TRANSFER_FROM: self._build_permit2_transfer_from(),

            V4Actions.SWAP_EXACT_IN_SINGLE: self._build_v4_swap_exact_in_single(),
            V4Actions.MINT_POSITION: self._build_v4_mint_position(),
            V4Actions.SETTLE_PAIR: self._build_v4_settle_pair(),
            V4Actions.SETTLE: self._build_v4_settle(),
            V4Actions.CLOSE_CURRENCY: self._build_v4_close_currency(),
            V4Actions.SWEEP: self._build_v4_sweep(),
            V4Actions.TAKE_ALL: self._build_v4_take_all(),
            V4Actions.SETTLE_ALL: self._build_v4_settle_all(),
            V4Actions.SWAP_EXACT_IN: self._build_v4_swap_exact_in(),
            V4Actions.MINT_POSITION_FROM_DELTAS: self._build_v4_mint_position_from_deltas(),
            V4Actions.WRAP: self._build_v4_wrap_eth(),
            V4Actions.UNWRAP: self._build_v4_unwrap_weth(),
            V4Actions.SWAP_EXACT_OUT_SINGLE: self._build_v4_swap_exact_out_single(),
            V4Actions.SWAP_EXACT_OUT: self._build_v4_swap_exact_out(),
            V4Actions.TAKE_PAIR: self._build_v4_take_pair(),
            V4Actions.CLEAR_OR_TAKE: self._build_v4_clear_or_take(),
            V4Actions.TAKE_PORTION: self._build_v4_take_portion(),
            V4Actions.TAKE: self._build_v4_take(),

            MiscFunctions.EXECUTE: self._build_execute(),
            MiscFunctions.EXECUTE_WITH_DEADLINE: self._build_execute_with_deadline(),
            MiscFunctions.UNLOCK_DATA: self._build_unlock_data(),
            MiscFunctions.V4_POOL_ID: self._build_v4_pool_id(),
            MiscFunctions.STRICT_V4_SWAP_EXACT_IN: self._build_strict_v4_swap_exact_in(),
            MiscFunctions.STRICT_V4_SWAP_EXACT_OUT: self._build_strict_v4_swap_exact_out(),
        }
        return abi_map

    @staticmethod
    def _build_v2_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_IN.name)
        builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_address_array("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_permit2_permit() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PERMIT2_PERMIT.name)
        inner_struct = builder.create_struct("details")
        inner_struct.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
        outer_struct = builder.create_struct("struct")
        outer_struct.add_struct(inner_struct).add_address("spender").add_uint256("sigDeadline")
        return builder.add_struct(outer_struct).add_bytes("data").build()

    @staticmethod
    def _build_unwrap_weth() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.UNWRAP_WETH.name)
        return builder.add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_v3_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_IN.name)
        builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_wrap_eth() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.WRAP_ETH.name)
        return builder.add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_v2_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_OUT.name)
        builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_address_array("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_v3_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_OUT.name)
        builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_sweep() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.SWEEP.name)
        return builder.add_address("token").add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_pay_portion() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PAY_PORTION.name)
        return builder.add_address("token").add_address("recipient").add_uint256("bips").build()

    @staticmethod
    def _build_transfer() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.TRANSFER.name)
        return builder.add_address("token").add_address("recipient").add_uint256("value").build()

    @staticmethod
    def _build_v4_swap() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V4_SWAP.name)
        return builder.add_bytes("actions").add_bytes_array("params").build()

    @staticmethod
    def _v4_pool_key_struct_builder() -> FunctionABIBuilder:
        builder = FunctionABIBuilder.create_struct("PoolKey")
        builder.add_address("currency0").add_address("currency1").add_uint24("fee").add_int24("tickSpacing")
        return builder.add_address("hooks")

    @staticmethod
    def _build_v4_swap_exact_in_single() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN_SINGLE.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        outer_struct = builder.create_struct("exact_in_single_params")
        outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountIn").add_uint128("amountOutMinimum")
        outer_struct.add_bytes("hookData")
        return builder.add_struct(outer_struct).build()

    @staticmethod
    def _build_v4_initialize_pool() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V4_INITIALIZE_POOL.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        return builder.add_struct(pool_key).add_uint256("sqrtPriceX96").build()

    @staticmethod
    def _build_modify_liquidities() -> FunctionABI:
        builder = FunctionABIBuilder("modifyLiquidities")
        return builder.add_bytes("unlockData").add_uint256("deadline").build()

    @staticmethod
    def _build_unlock_data() -> FunctionABI:
        builder = FunctionABIBuilder("unlockData")
        return builder.add_bytes("actions").add_bytes_array("params").build()

    @staticmethod
    def _build_v4_mint_position() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.MINT_POSITION.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper").add_uint256("liquidity")
        builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
        return builder.build()

    @staticmethod
    def _build_v4_settle_pair() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE_PAIR.name)
        return builder.add_address("currency0").add_address("currency1").build()

    @staticmethod
    def _build_v4_settle() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE.name)
        return builder.add_address("currency").add_uint256("amount").add_bool("payerIsUser").build()

    @staticmethod
    def _build_v4_close_currency() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.CLOSE_CURRENCY.name)
        return builder.add_address("currency").build()

    @staticmethod
    def _build_v4_sweep() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWEEP.name)
        return builder.add_address("currency").add_address("to").build()

    @staticmethod
    def _build_permit2_transfer_from() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PERMIT2_TRANSFER_FROM.name)
        return builder.add_address("token").add_address("recipient").add_uint256("amount").build()

    @staticmethod
    def _build_v4_take_all() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_ALL.name)
        return builder.add_address("currency").add_uint256("minAmount").build()

    @staticmethod
    def _build_v4_settle_all() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE_ALL.name)
        return builder.add_address("currency").add_uint256("maxAmount").build()

    @staticmethod
    def _build_execute() -> FunctionABI:
        builder = FunctionABIBuilder("execute")
        return builder.add_bytes("commands").add_bytes_array("inputs").build()

    @staticmethod
    def _build_execute_with_deadline() -> FunctionABI:
        builder = FunctionABIBuilder("execute")
        return builder.add_bytes("commands").add_bytes_array("inputs").add_uint256("deadline").build()

    @staticmethod
    def _build_v4_pool_id() -> FunctionABI:
        builder = FunctionABIBuilder("v4_pool_id")
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        return builder.add_struct(pool_key).build()

    @staticmethod
    def _v4_path_key_struct_array_builder() -> FunctionABIBuilder:
        builder = FunctionABIBuilder.create_struct_array("PathKeys")
        builder.add_address("intermediateCurrency").add_uint24("fee").add_int24("tickSpacing")
        return builder.add_address("hooks").add_bytes("hookData")

    @staticmethod
    def _build_strict_v4_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_IN.name)
        builder.add_address("currencyIn")
        builder.add_struct_array(_ABIBuilder._v4_path_key_struct_array_builder())
        return builder.add_uint128("amountIn").add_uint128("amountOutMinimum").build()

    @staticmethod
    def _build_v4_mint_position_from_deltas() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.MINT_POSITION_FROM_DELTAS.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper")
        builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
        return builder.build()

    @staticmethod
    def _build_v4_wrap_eth() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.WRAP.name)
        return builder.add_uint256("amount").build()

    @staticmethod
    def _build_v4_unwrap_weth() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.UNWRAP.name)
        return builder.add_uint256("amount").build()

    @staticmethod
    def _build_v4_swap_exact_out_single() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT_SINGLE.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        outer_struct = builder.create_struct("exact_out_single_params")
        outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountOut").add_uint128("amountInMaximum")
        outer_struct.add_bytes("hookData")
        return builder.add_struct(outer_struct).build()

    @staticmethod
    def _build_strict_v4_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_OUT.name)
        builder.add_address("currencyOut")
        builder.add_struct_array(_ABIBuilder._v4_path_key_struct_array_builder())
        return builder.add_uint128("amountOut").add_uint128("amountInMaximum").build()

    @staticmethod
    def _build_v4_take_pair() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_PAIR.name)
        return builder.add_address("currency0").add_address("currency1").add_address("recipient").build()

    @staticmethod
    def _build_v4_clear_or_take() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.CLEAR_OR_TAKE.name)
        return builder.add_address("currency").add_uint256("amountMax").build()

    @staticmethod
    def _build_v4_take_portion() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_PORTION.name)
        return builder.add_address("currency").add_address("recipient").add_uint256("bips").build()

    @staticmethod
    def _build_v4_take() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE.name)
        return builder.add_address("currency").add_address("recipient").add_uint256("amount").build()

    @staticmethod
    def _build_v4_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN.name)
        return builder.add_v4_exact_input_params().build()

    def decode_v4_exact_input_params(self, stream: BytesIO) -> Dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.get_full_abi())
        fct_name, decoded_params = sub_contract.decode_function_input(fct_abi.get_selector() + raw_data[32:])
        return cast(Dict[str, Any], decoded_params)

    def encode_v4_exact_input_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.get_abi_types(), args)
        return encoded_data

    @staticmethod
    def _build_v4_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT.name)
        return builder.add_v4_exact_output_params().build()

    def decode_v4_exact_output_params(self, stream: BytesIO) -> Dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.get_full_abi())
        fct_name, decoded_params = sub_contract.decode_function_input(fct_abi.get_selector() + raw_data[32:])
        return cast(Dict[str, Any], decoded_params)

    def encode_v4_exact_output_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.get_abi_types(), args)
        return encoded_data
    
_router_abi = '[{"inputs":[{"components":[{"internalType":"address","name":"permit2","type":"address"},{"internalType":"address","name":"weth9","type":"address"},{"internalType":"address","name":"v2Factory","type":"address"},{"internalType":"address","name":"v3Factory","type":"address"},{"internalType":"bytes32","name":"pairInitCodeHash","type":"bytes32"},{"internalType":"bytes32","name":"poolInitCodeHash","type":"bytes32"},{"internalType":"address","name":"v4PoolManager","type":"address"},{"internalType":"address","name":"v3NFTPositionManager","type":"address"},{"internalType":"address","name":"v4PositionManager","type":"address"}],"internalType":"struct RouterParameters","name":"params","type":"tuple"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"BalanceTooLow","type":"error"},{"inputs":[],"name":"ContractLocked","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotNegative","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotPositive","type":"error"},{"inputs":[],"name":"ETHNotAccepted","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandIndex","type":"uint256"},{"internalType":"bytes","name":"message","type":"bytes"}],"name":"ExecutionFailed","type":"error"},{"inputs":[],"name":"FromAddressIsNotOwner","type":"error"},{"inputs":[],"name":"InputLengthMismatch","type":"error"},{"inputs":[],"name":"InsufficientBalance","type":"error"},{"inputs":[],"name":"InsufficientETH","type":"error"},{"inputs":[],"name":"InsufficientToken","type":"error"},{"inputs":[{"internalType":"bytes4","name":"action","type":"bytes4"}],"name":"InvalidAction","type":"error"},{"inputs":[],"name":"InvalidBips","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandType","type":"uint256"}],"name":"InvalidCommandType","type":"error"},{"inputs":[],"name":"InvalidEthSender","type":"error"},{"inputs":[],"name":"InvalidPath","type":"error"},{"inputs":[],"name":"InvalidReserves","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"NotAuthorizedForToken","type":"error"},{"inputs":[],"name":"NotPoolManager","type":"error"},{"inputs":[],"name":"OnlyMintAllowed","type":"error"},{"inputs":[],"name":"SliceOutOfBounds","type":"error"},{"inputs":[],"name":"TransactionDeadlinePassed","type":"error"},{"inputs":[],"name":"UnsafeCast","type":"error"},{"inputs":[{"internalType":"uint256","name":"action","type":"uint256"}],"name":"UnsupportedAction","type":"error"},{"inputs":[],"name":"V2InvalidPath","type":"error"},{"inputs":[],"name":"V2TooLittleReceived","type":"error"},{"inputs":[],"name":"V2TooMuchRequested","type":"error"},{"inputs":[],"name":"V3InvalidAmountOut","type":"error"},{"inputs":[],"name":"V3InvalidCaller","type":"error"},{"inputs":[],"name":"V3InvalidSwap","type":"error"},{"inputs":[],"name":"V3TooLittleReceived","type":"error"},{"inputs":[],"name":"V3TooMuchRequested","type":"error"},{"inputs":[{"internalType":"uint256","name":"minAmountOutReceived","type":"uint256"},{"internalType":"uint256","name":"amountReceived","type":"uint256"}],"name":"V4TooLittleReceived","type":"error"},{"inputs":[{"internalType":"uint256","name":"maxAmountInRequested","type":"uint256"},{"internalType":"uint256","name":"amountRequested","type":"uint256"}],"name":"V4TooMuchRequested","type":"error"},{"inputs":[],"name":"V3_POSITION_MANAGER","outputs":[{"internalType":"contract INonfungiblePositionManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"V4_POSITION_MANAGER","outputs":[{"internalType":"contract IPositionManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"msgSender","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolManager","outputs":[{"internalType":"contract IPoolManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"int256","name":"amount0Delta","type":"int256"},{"internalType":"int256","name":"amount1Delta","type":"int256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"uniswapV3SwapCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"unlockCallback","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'
_position_manager_abi = '[{"inputs":[{"internalType":"contract IPoolManager","name":"_poolManager","type":"address"},{"internalType":"contract IAllowanceTransfer","name":"_permit2","type":"address"},{"internalType":"uint256","name":"_unsubscribeGasLimit","type":"uint256"},{"internalType":"contract IPositionDescriptor","name":"_tokenDescriptor","type":"address"},{"internalType":"contract IWETH9","name":"_weth9","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address","name":"subscriber","type":"address"}],"name":"AlreadySubscribed","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"BurnNotificationReverted","type":"error"},{"inputs":[],"name":"ContractLocked","type":"error"},{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"DeadlinePassed","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotNegative","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotPositive","type":"error"},{"inputs":[],"name":"GasLimitTooLow","type":"error"},{"inputs":[],"name":"InputLengthMismatch","type":"error"},{"inputs":[],"name":"InsufficientBalance","type":"error"},{"inputs":[],"name":"InvalidContractSignature","type":"error"},{"inputs":[],"name":"InvalidEthSender","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSignatureLength","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[{"internalType":"uint128","name":"maximumAmount","type":"uint128"},{"internalType":"uint128","name":"amountRequested","type":"uint128"}],"name":"MaximumAmountExceeded","type":"error"},{"inputs":[{"internalType":"uint128","name":"minimumAmount","type":"uint128"},{"internalType":"uint128","name":"amountReceived","type":"uint128"}],"name":"MinimumAmountInsufficient","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"ModifyLiquidityNotificationReverted","type":"error"},{"inputs":[],"name":"NoCodeSubscriber","type":"error"},{"inputs":[],"name":"NoSelfPermit","type":"error"},{"inputs":[],"name":"NonceAlreadyUsed","type":"error"},{"inputs":[{"internalType":"address","name":"caller","type":"address"}],"name":"NotApproved","type":"error"},{"inputs":[],"name":"NotPoolManager","type":"error"},{"inputs":[],"name":"NotSubscribed","type":"error"},{"inputs":[],"name":"PoolManagerMustBeLocked","type":"error"},{"inputs":[],"name":"SignatureDeadlineExpired","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"SubscriptionReverted","type":"error"},{"inputs":[],"name":"Unauthorized","type":"error"},{"inputs":[{"internalType":"uint256","name":"action","type":"uint256"}],"name":"UnsupportedAction","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":true,"internalType":"address","name":"subscriber","type":"address"}],"name":"Subscription","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":true,"internalType":"address","name":"subscriber","type":"address"}],"name":"Unsubscription","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WETH9","outputs":[{"internalType":"contract IWETH9","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getPoolAndPositionInfo","outputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"poolKey","type":"tuple"},{"internalType":"PositionInfo","name":"info","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getPositionLiquidity","outputs":[{"internalType":"uint128","name":"liquidity","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"}],"name":"initializePool","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes","name":"unlockData","type":"bytes"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"modifyLiquidities","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"actions","type":"bytes"},{"internalType":"bytes[]","name":"params","type":"bytes[]"}],"name":"modifyLiquiditiesWithoutUnlock","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"msgSender","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes[]","name":"data","type":"bytes[]"}],"name":"multicall","outputs":[{"internalType":"bytes[]","name":"results","type":"bytes[]"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"nextTokenId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"word","type":"uint256"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"bitmap","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"owner","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails","name":"details","type":"tuple"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitSingle","name":"permitSingle","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[{"internalType":"bytes","name":"err","type":"bytes"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"permit2","outputs":[{"internalType":"contract IAllowanceTransfer","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails[]","name":"details","type":"tuple[]"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitBatch","name":"_permitBatch","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitBatch","outputs":[{"internalType":"bytes","name":"err","type":"bytes"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitForAll","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes25","name":"poolId","type":"bytes25"}],"name":"poolKeys","outputs":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolManager","outputs":[{"internalType":"contract IPoolManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"positionInfo","outputs":[{"internalType":"PositionInfo","name":"info","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"nonce","type":"uint256"}],"name":"revokeNonce","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address","name":"newSubscriber","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"subscribe","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"subscriber","outputs":[{"internalType":"contract ISubscriber","name":"subscriber","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"tokenDescriptor","outputs":[{"internalType":"contract IPositionDescriptor","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"unlockCallback","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"unsubscribe","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"unsubscribeGasLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]'
_permit2_abi = '[{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"AllowanceExpired","type":"error"},{"inputs":[],"name":"ExcessiveInvalidation","type":"error"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"InsufficientAllowance","type":"error"},{"inputs":[{"internalType":"uint256","name":"maxAmount","type":"uint256"}],"name":"InvalidAmount","type":"error"},{"inputs":[],"name":"InvalidContractSignature","type":"error"},{"inputs":[],"name":"InvalidNonce","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSignatureLength","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[{"internalType":"uint256","name":"signatureDeadline","type":"uint256"}],"name":"SignatureExpired","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"address","name":"spender","type":"address"}],"name":"Lockdown","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint48","name":"newNonce","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"oldNonce","type":"uint48"}],"name":"NonceInvalidation","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"nonce","type":"uint48"}],"name":"Permit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"word","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"mask","type":"uint256"}],"name":"UnorderedNonceInvalidation","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint48","name":"newNonce","type":"uint48"}],"name":"invalidateNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"wordPos","type":"uint256"},{"internalType":"uint256","name":"mask","type":"uint256"}],"name":"invalidateUnorderedNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"internalType":"struct IAllowanceTransfer.TokenSpenderPair[]","name":"approvals","type":"tuple[]"}],"name":"lockdown","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"nonceBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails[]","name":"details","type":"tuple[]"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitBatch","name":"permitBatch","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails","name":"details","type":"tuple"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitSingle","name":"permitSingle","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"internalType":"struct IAllowanceTransfer.AllowanceTransferDetails[]","name":"transferDetails","type":"tuple[]"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
_pool_manager_abi = '[{"inputs":[{"internalType":"address","name":"initialOwner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"AlreadyUnlocked","type":"error"},{"inputs":[{"internalType":"address","name":"currency0","type":"address"},{"internalType":"address","name":"currency1","type":"address"}],"name":"CurrenciesOutOfOrderOrEqual","type":"error"},{"inputs":[],"name":"CurrencyNotSettled","type":"error"},{"inputs":[],"name":"DelegateCallNotAllowed","type":"error"},{"inputs":[],"name":"InvalidCaller","type":"error"},{"inputs":[],"name":"ManagerLocked","type":"error"},{"inputs":[],"name":"MustClearExactPositiveDelta","type":"error"},{"inputs":[],"name":"NonzeroNativeValue","type":"error"},{"inputs":[],"name":"PoolNotInitialized","type":"error"},{"inputs":[],"name":"ProtocolFeeCurrencySynced","type":"error"},{"inputs":[{"internalType":"uint24","name":"fee","type":"uint24"}],"name":"ProtocolFeeTooLarge","type":"error"},{"inputs":[],"name":"SwapAmountCannotBeZero","type":"error"},{"inputs":[{"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"TickSpacingTooLarge","type":"error"},{"inputs":[{"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"TickSpacingTooSmall","type":"error"},{"inputs":[],"name":"UnauthorizedDynamicLPFeeUpdate","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"id","type":"bytes32"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Donate","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"id","type":"bytes32"},{"indexed":true,"internalType":"Currency","name":"currency0","type":"address"},{"indexed":true,"internalType":"Currency","name":"currency1","type":"address"},{"indexed":false,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":false,"internalType":"int24","name":"tickSpacing","type":"int24"},{"indexed":false,"internalType":"contract IHooks","name":"hooks","type":"address"},{"indexed":false,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":false,"internalType":"int24","name":"tick","type":"int24"}],"name":"Initialize","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"id","type":"bytes32"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":false,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":false,"internalType":"int256","name":"liquidityDelta","type":"int256"},{"indexed":false,"internalType":"bytes32","name":"salt","type":"bytes32"}],"name":"ModifyLiquidity","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"OperatorSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"protocolFeeController","type":"address"}],"name":"ProtocolFeeControllerUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"id","type":"bytes32"},{"indexed":false,"internalType":"uint24","name":"protocolFee","type":"uint24"}],"name":"ProtocolFeeUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"id","type":"bytes32"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"int128","name":"amount0","type":"int128"},{"indexed":false,"internalType":"int128","name":"amount1","type":"int128"},{"indexed":false,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":false,"internalType":"uint128","name":"liquidity","type":"uint128"},{"indexed":false,"internalType":"int24","name":"tick","type":"int24"},{"indexed":false,"internalType":"uint24","name":"fee","type":"uint24"}],"name":"Swap","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"balance","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"clear","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"Currency","name":"currency","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"collectProtocolFees","outputs":[{"internalType":"uint256","name":"amountCollected","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"},{"internalType":"bytes","name":"hookData","type":"bytes"}],"name":"donate","outputs":[{"internalType":"BalanceDelta","name":"delta","type":"int256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"slot","type":"bytes32"}],"name":"extsload","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"startSlot","type":"bytes32"},{"internalType":"uint256","name":"nSlots","type":"uint256"}],"name":"extsload","outputs":[{"internalType":"bytes32[]","name":"","type":"bytes32[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"slots","type":"bytes32[]"}],"name":"extsload","outputs":[{"internalType":"bytes32[]","name":"","type":"bytes32[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"slots","type":"bytes32[]"}],"name":"exttload","outputs":[{"internalType":"bytes32[]","name":"","type":"bytes32[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"slot","type":"bytes32"}],"name":"exttload","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"}],"name":"initialize","outputs":[{"internalType":"int24","name":"tick","type":"int24"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"}],"name":"isOperator","outputs":[{"internalType":"bool","name":"isOperator","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"components":[{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"int256","name":"liquidityDelta","type":"int256"},{"internalType":"bytes32","name":"salt","type":"bytes32"}],"internalType":"struct IPoolManager.ModifyLiquidityParams","name":"params","type":"tuple"},{"internalType":"bytes","name":"hookData","type":"bytes"}],"name":"modifyLiquidity","outputs":[{"internalType":"BalanceDelta","name":"callerDelta","type":"int256"},{"internalType":"BalanceDelta","name":"feesAccrued","type":"int256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"protocolFeeController","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"protocolFeesAccrued","outputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"}],"name":"setOperator","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint24","name":"newProtocolFee","type":"uint24"}],"name":"setProtocolFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"controller","type":"address"}],"name":"setProtocolFeeController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"settle","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"}],"name":"settleFor","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"components":[{"internalType":"bool","name":"zeroForOne","type":"bool"},{"internalType":"int256","name":"amountSpecified","type":"int256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct IPoolManager.SwapParams","name":"params","type":"tuple"},{"internalType":"bytes","name":"hookData","type":"bytes"}],"name":"swap","outputs":[{"internalType":"BalanceDelta","name":"swapDelta","type":"int256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"sync","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"take","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"receiver","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"unlock","outputs":[{"internalType":"bytes","name":"result","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint24","name":"newDynamicLPFee","type":"uint24"}],"name":"updateDynamicLPFee","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501
_position_manager_abi = '[{"inputs":[{"internalType":"contract IPoolManager","name":"_poolManager","type":"address"},{"internalType":"contract IAllowanceTransfer","name":"_permit2","type":"address"},{"internalType":"uint256","name":"_unsubscribeGasLimit","type":"uint256"},{"internalType":"contract IPositionDescriptor","name":"_tokenDescriptor","type":"address"},{"internalType":"contract IWETH9","name":"_weth9","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address","name":"subscriber","type":"address"}],"name":"AlreadySubscribed","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"BurnNotificationReverted","type":"error"},{"inputs":[],"name":"ContractLocked","type":"error"},{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"DeadlinePassed","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotNegative","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"DeltaNotPositive","type":"error"},{"inputs":[],"name":"GasLimitTooLow","type":"error"},{"inputs":[],"name":"InputLengthMismatch","type":"error"},{"inputs":[],"name":"InsufficientBalance","type":"error"},{"inputs":[],"name":"InvalidContractSignature","type":"error"},{"inputs":[],"name":"InvalidEthSender","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSignatureLength","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[{"internalType":"uint128","name":"maximumAmount","type":"uint128"},{"internalType":"uint128","name":"amountRequested","type":"uint128"}],"name":"MaximumAmountExceeded","type":"error"},{"inputs":[{"internalType":"uint128","name":"minimumAmount","type":"uint128"},{"internalType":"uint128","name":"amountReceived","type":"uint128"}],"name":"MinimumAmountInsufficient","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"ModifyLiquidityNotificationReverted","type":"error"},{"inputs":[],"name":"NoCodeSubscriber","type":"error"},{"inputs":[],"name":"NoSelfPermit","type":"error"},{"inputs":[],"name":"NonceAlreadyUsed","type":"error"},{"inputs":[{"internalType":"address","name":"caller","type":"address"}],"name":"NotApproved","type":"error"},{"inputs":[],"name":"NotPoolManager","type":"error"},{"inputs":[],"name":"NotSubscribed","type":"error"},{"inputs":[],"name":"PoolManagerMustBeLocked","type":"error"},{"inputs":[],"name":"SignatureDeadlineExpired","type":"error"},{"inputs":[{"internalType":"address","name":"subscriber","type":"address"},{"internalType":"bytes","name":"reason","type":"bytes"}],"name":"SubscriptionReverted","type":"error"},{"inputs":[],"name":"Unauthorized","type":"error"},{"inputs":[{"internalType":"uint256","name":"action","type":"uint256"}],"name":"UnsupportedAction","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":true,"internalType":"address","name":"subscriber","type":"address"}],"name":"Subscription","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"},{"indexed":true,"internalType":"address","name":"subscriber","type":"address"}],"name":"Unsubscription","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WETH9","outputs":[{"internalType":"contract IWETH9","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getPoolAndPositionInfo","outputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"poolKey","type":"tuple"},{"internalType":"PositionInfo","name":"info","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getPositionLiquidity","outputs":[{"internalType":"uint128","name":"liquidity","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"}],"name":"initializePool","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes","name":"unlockData","type":"bytes"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"modifyLiquidities","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"actions","type":"bytes"},{"internalType":"bytes[]","name":"params","type":"bytes[]"}],"name":"modifyLiquiditiesWithoutUnlock","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"msgSender","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes[]","name":"data","type":"bytes[]"}],"name":"multicall","outputs":[{"internalType":"bytes[]","name":"results","type":"bytes[]"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"nextTokenId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"word","type":"uint256"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"bitmap","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"owner","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails","name":"details","type":"tuple"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitSingle","name":"permitSingle","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[{"internalType":"bytes","name":"err","type":"bytes"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"permit2","outputs":[{"internalType":"contract IAllowanceTransfer","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails[]","name":"details","type":"tuple[]"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitBatch","name":"_permitBatch","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitBatch","outputs":[{"internalType":"bytes","name":"err","type":"bytes"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitForAll","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes25","name":"poolId","type":"bytes25"}],"name":"poolKeys","outputs":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolManager","outputs":[{"internalType":"contract IPoolManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"positionInfo","outputs":[{"internalType":"PositionInfo","name":"info","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"nonce","type":"uint256"}],"name":"revokeNonce","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"address","name":"newSubscriber","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"subscribe","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"subscriber","outputs":[{"internalType":"contract ISubscriber","name":"subscriber","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"tokenDescriptor","outputs":[{"internalType":"contract IPositionDescriptor","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"unlockCallback","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"unsubscribe","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"unsubscribeGasLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]'

class _V4Decoder:
    def __init__(self, w3: Web3, abi_map: ABIMap) -> None:
        self._w3 = w3
        self._abi_map = abi_map
        self._pm_contract = w3.eth.contract(abi=_position_manager_abi)

    def _decode_v4_actions(
            self,
            actions: bytes,
            params: List[bytes]) -> List[Tuple[BaseContractFunction, Dict[str, Any]]]:
        if len(actions) != len(params):
            raise ValueError(f"Number of actions {len(actions)} is different from number of params: {len(params)}")

        decoded_params = []
        for i, action in enumerate(actions):
            try:
                abi_mapping = self._abi_map[V4Actions(action)]
                data = abi_mapping.get_selector() + params[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.get_full_abi())
                decoded_params.append(sub_contract.decode_function_input(data))
            except (ValueError, KeyError, DecodingError):
                decoded_params.append(params[i].hex())
        return decoded_params

    def decode_v4_swap(self, actions: bytes, params: List[bytes]) -> List[Tuple[BaseContractFunction, Dict[str, Any]]]:
        return self._decode_v4_actions(actions, params)

    def decode_v4_pm_call(self, encoded_input: bytes) -> Dict[str, Any]:
        actions, params = decode(["bytes", "bytes[]"], encoded_input)
        return {"actions": actions, "params": self._decode_v4_actions(actions, params)}


class _Decoder:
    def __init__(self, w3: Web3, abi_map: ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self._v4_decoder = _V4Decoder(w3, abi_map)

    def function_input(self, input_data: Union[HexStr, HexBytes]) -> Tuple[BaseContractFunction, Dict[str, Any]]:
        """
        Decode the data sent to an UR function

        :param input_data: the transaction 'input' data
        :return: The decoded data if the function has been implemented.
        """
        fct_name, decoded_input = self._router_contract.decode_function_input(input_data)
        # returns (execute as basecontractfunction, {commands as bytes, inputs as seq of bytes, deadline as int})
        command = decoded_input["commands"]
        command_input = decoded_input["inputs"]
        decoded_command_input = []
        for i, b in enumerate(command):
            # iterating over bytes produces integers
            command_function = b & _RouterConstant.COMMAND_TYPE_MASK.value
            try:
                abi_mapping = self._abi_map[RouterFunction(command_function)]
                if b == RouterFunction.V4_POSITION_MANAGER_CALL.value:
                    data = command_input[i]
                else:
                    data = abi_mapping.get_selector() + command_input[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.get_full_abi())
                revert_on_fail = not bool(b & _RouterConstant.FLAG_ALLOW_REVERT.value)
                decoded_fct_name, decoded_fct_params = sub_contract.decode_function_input(data)
                if b == RouterFunction.V4_SWAP.value:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            {
                                "actions": decoded_fct_params["actions"],
                                "params": self._v4_decoder.decode_v4_swap(
                                    decoded_fct_params["actions"],
                                    decoded_fct_params["params"],
                                ),
                            },
                            {"revert_on_fail": revert_on_fail},
                        )
                    )
                elif b == RouterFunction.V4_POSITION_MANAGER_CALL.value:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            {
                                "unlockData": self._v4_decoder.decode_v4_pm_call(decoded_fct_params["unlockData"]),
                                "deadline": decoded_fct_params["deadline"]
                            },
                            {"revert_on_fail": revert_on_fail},
                        )
                    )
                else:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            decoded_fct_params,
                            {"revert_on_fail": revert_on_fail}
                        )
                    )

            except (ValueError, KeyError, DecodingError):
                decoded_command_input.append(command_input[i].hex())
        decoded_input["inputs"] = decoded_command_input
        return fct_name, decoded_input

    def transaction(self, trx_hash: Union[HexBytes, HexStr]) -> Dict[str, Any]:
        """
        Get transaction details and decode the data used to call a UR function.

        ⚠ To use this method, the decoder must be built with a Web3 instance or a rpc endpoint address.

        :param trx_hash: the hash of the transaction sent to the UR
        :return: the transaction as a dict with the additional 'decoded_input' field
        """
        trx = self._get_transaction(trx_hash)
        fct_name, decoded_input = self.function_input(trx["input"])
        result_trx = dict(trx)
        result_trx["decoded_input"] = decoded_input
        return result_trx

    def _get_transaction(self, trx_hash: Union[HexBytes, HexStr]) -> TxData:
        return self._w3.eth.get_transaction(trx_hash)

    @staticmethod
    def v3_path(v3_fn_name: str, path: Union[bytes, str]) -> Tuple[Union[int, ChecksumAddress], ...]:
        """
        Decode a V3 router path

        :param v3_fn_name: V3_SWAP_EXACT_IN or V3_SWAP_EXACT_OUT only
        :param path: the V3 path as returned by decode_function_input() or decode_transaction()
        :return: a tuple of token addresses separated by the corresponding pool fees, first token being the 'in-token',
        last token being the 'out-token'
        """
        valid_fn_names = ("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_OUT")
        if v3_fn_name.upper() not in valid_fn_names:
            raise ValueError(f"v3_fn_name must be in {valid_fn_names}")
        path_str = path.hex() if isinstance(path, bytes) else str(path)
        path_str = path_str[2:] if path_str.startswith("0x") else path_str
        path_list: List[Union[int, ChecksumAddress]] = [Web3.to_checksum_address(path_str[0:40]), ]
        parsed_remaining_path: List[List[Union[int, ChecksumAddress]]] = [
            [
                int(path_str[40:][i:i + 6], 16),
                Web3.to_checksum_address(path_str[40:][i + 6:i + 46]),
            ]
            for i in range(0, len(path_str[40:]), 46)
        ]
        path_list.extend(list(chain.from_iterable(parsed_remaining_path)))

        if v3_fn_name.upper() == "V3_SWAP_EXACT_OUT":
            path_list.reverse()

        return tuple(path_list)

    def contract_error(
            self,
            contract_error: Union[str, HexStr],
            abis: Sequence[str] = (_permit2_abi, _pool_manager_abi, _position_manager_abi, _router_abi),
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Decode contract custom errors.

        :param contract_error: the hexadecimal error, ex: '0x5d1d0f9f'
        :param abis: override the default abis which are permit2, v4 pool and position managers, and the UR
        :return: the decoded error if it's part of the abis, or 'Unknown error'
        """
        for abi in abis:
            try:
                json_abi = json.loads(abi)
                error_abi = []
                for item in json_abi:
                    if item["type"].lower() == "error":
                        item["type"] = "function"
                        error_abi.append(item)
                contract = self._w3.eth.contract(abi=error_abi)
                error, params = contract.decode_function_input(contract_error)
                return f"{error.fn_name}({','.join(build_abi_type_list(error.abi))})", params
            except (ValueError, Web3Exception):
                """The error is not defined in this ABI"""
        return "Unknown error", {}

class _Encoder:
    def __init__(self, w3: Web3, abi_map: ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map

    @staticmethod
    def v3_path(v3_fn_name: str, path_seq: Sequence[Union[int, ChecksumAddress]]) -> bytes:
        """
        Encode a V3 path
        :param v3_fn_name: 'V3_SWAP_EXACT_IN' or 'V3_SWAP_EXACT_OUT'
        :param path_seq: a sequence of token addresses with the pool fee in between, ex: [tk_in_addr, fee, tk_out_addr]
        :return: the encoded V3 path
        """
        if len(path_seq) < 3:
            raise ValueError("Invalid list to encode a V3 path. Must have at least 3 parameters")
        path_list = list(path_seq)
        if v3_fn_name == "V3_SWAP_EXACT_OUT":
            path_list.reverse()
        elif v3_fn_name != "V3_SWAP_EXACT_IN":
            raise ValueError("v3_fn_name must be in ('V3_SWAP_EXACT_IN', 'V3_SWAP_EXACT_OUT')")
        path = "0x"
        for i, item in enumerate(path_list):
            if i % 2 == 0:
                _item = Web3.to_checksum_address(cast(ChecksumAddress, item))[2:]
            else:
                _item = f"{item:06X}"
            path += _item
        return Web3.to_bytes(hexstr=HexStr(path))

    @staticmethod
    def v4_pool_key(
            currency_0: Union[str, HexStr, ChecksumAddress],
            currency_1: Union[str, HexStr, ChecksumAddress],
            fee: int,
            tick_spacing: int,
            hooks: Union[str, HexStr, ChecksumAddress] = "0x0000000000000000000000000000000000000000") -> PoolKey:
        """
        Make sure currency_0 < currency_1 and returns the v4 pool key

        :param currency_0: the address of one token, or "0x0000000000000000000000000000000000000000" for ETH
        :param currency_1: the address of the other token, or "0x0000000000000000000000000000000000000000" for ETH
        :param fee: pool fee in percentage * 10000 (ex: 3000 for 0.3%)
        :param tick_spacing: granularity of the pool. Lower values are more precise but more expensive to trade
        :param hooks: hook address, default is no hooks, ie "0x0000000000000000000000000000000000000000"
        :return: the v4 pool key
        """
        if int(currency_0, 16) > int(currency_1, 16):
            currency_0, currency_1 = currency_1, currency_0
        return PoolKey(
            currency_0=Web3.to_checksum_address(currency_0),
            currency_1=Web3.to_checksum_address(currency_1),
            fee=int(fee),
            tick_spacing=int(tick_spacing),
            hooks=Web3.to_checksum_address(hooks),
        )

    def v4_pool_id(self, pool_key: PoolKey) -> bytes:
        """
        Encode the pool id

        :param pool_key: the PoolKey (see v4_pool_key() to get it)
        :return: the pool id
        """
        args = (tuple(pool_key.values()), )
        abi = self._abi_map[MiscFunctions.V4_POOL_ID]
        return keccak(abi.encode(args))

    @staticmethod
    def v4_path_key(
            intermediate_currency: ChecksumAddress,
            fee: int,
            tick_spacing: int,
            hooks: Union[str, HexStr, ChecksumAddress] = "0x0000000000000000000000000000000000000000",
            hook_data: bytes = b"") -> PathKey:
        """
        Build a PathKey which is used by multi-hop swap encoding

        :param intermediate_currency: the address of one token of the target pool
        :param fee: pool fee in percentage * 10000 (ex: 3000 for 0.3%)
        :param tick_spacing: granularity of the pool. Lower values are more precise but more expensive to trade
        :param hooks: hook address, default is no hooks, ie "0x0000000000000000000000000000000000000000"
        :param hook_data: encoded hook data
        :return: the corresponding PathKey
        """
        return PathKey(
            intermediate_currency=Web3.to_checksum_address(intermediate_currency),
            fee=int(fee),
            tick_spacing=int(tick_spacing),
            hooks=Web3.to_checksum_address(hooks),
            hook_data=hook_data,
        )

    def chain(self) -> _ChainedFunctionBuilder:
        """
        :return: Initialize the chain of encoded functions
        """
        return _ChainedFunctionBuilder(self._w3, self._abi_map)


class RouterCodec:
    def __init__(self, w3: Optional[Web3] = None, rpc_endpoint: Optional[str] = None) -> None:
        if w3:
            print("❤️")
        elif rpc_endpoint:
            print("❤️❤️")
        else:
            print("❤️❤️❤️")

        if w3:
            self._w3 = w3
        elif rpc_endpoint:
            self._w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        else:
            self._w3 = Web3()
        self._abi_map = _ABIBuilder(self._w3).abi_map
        self.decode = _Decoder(self._w3, self._abi_map)
        self.encode = _Encoder(self._w3, self._abi_map)

    @staticmethod
    def get_default_deadline(valid_duration: int = 180) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 180
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def get_default_expiration(valid_duration: int = 30 * 24 * 3600) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 30 days
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def get_max_expiration() -> int:
        """
        :return: max timestamp allowed for permit expiration
        """
        return 2 ** 48 - 1

    @staticmethod
    def create_permit2_signable_message(
            token_address: ChecksumAddress,
            amount: Wei,
            expiration: int,
            nonce: int,
            spender: ChecksumAddress,
            deadline: int,
            chain_id: int = 8453,
            verifying_contract: ChecksumAddress = _permit2_address) -> Tuple[Dict[str, Any], SignableMessage]:
        """
        Create a eth_account.messages.SignableMessage that will be sent to the UR/Permit2 contracts
        to set token permissions through signature validation.

        See https://docs.uniswap.org/contracts/permit2/reference/allowance-transfer#single-permit

        See https://eips.ethereum.org/EIPS/eip-712 for EIP712 structured data signing.

        In addition to this step, the Permit2 contract has to be approved through the token contract.

        :param token_address: The address of the token for which an allowance will be given to the UR
        :param amount: The allowance amount in Wei. Max = 2 ** 160 - 1
        :param expiration: The Unix timestamp at which a spender's token allowances become invalid
        :param nonce: An incrementing value indexed per owner,token,and spender for each signature
        :param spender: The spender (ie: the UR) address
        :param deadline: The deadline, as a Unix timestamp, on the permit signature
        :param chain_id: What it says on the box. Default to 1.
        :param verifying_contract: the permit2 contract address. Default to uniswap permit2 address.
        :return: A tuple: (PermitSingle, SignableMessage).
            The first element is the first parameter of permit2_permit().
            The second element must be signed with eth_account.signers.local.LocalAccount.sign_message() in your code
            and the resulting SignedMessage is the 2nd parameter of permit2_permit().
        """
        permit_details = {
            "token": token_address,
            "amount": amount,
            "expiration": expiration,
            "nonce": nonce,
        }
        permit_single = {
            "details": permit_details,
            "spender": spender,
            "sigDeadline": deadline,
        }
        domain_data = dict(_permit2_domain_data)
        domain_data["chainId"] = chain_id
        domain_data["verifyingContract"] = verifying_contract
        signable_message = encode_typed_data(
            domain_data=domain_data,
            message_types=_permit2_types,
            message_data=permit_single,
        )
        return permit_single, signable_message

    def fetch_permit2_allowance(
            self,
            wallet: ChecksumAddress,
            token: ChecksumAddress,
            spender: ChecksumAddress = _ur_address,
            permit2: ChecksumAddress = _permit2_address,
            permit2_abi: str = _permit2_abi,
            block_identifier: BlockIdentifier = "latest") -> Tuple[Wei, int, Nonce]:
        """
        Request the permit2 allowance function to know if the UR has enough valid allowance,
        and to get the current permit2 nonce for a given wallet and token.

        :param wallet: the account address to check
        :param token: the address of the token to check
        :param spender: the Universal Router address - Default is its address on Mainnet
        :param permit2: the Permit2 address - Default is its address on Mainnet
        :param permit2_abi: the Permit2 abi - Default is the one deployed on Mainnet
        :param block_identifier: the request will be done for this block - Default is 'latest'
        :return: The current allowed amount in Wei, the timestamp after which the allowance is not valid anymore and
        the current nonce (to be used with the next permit2_permit() request)
        """
        permit2_contract = self._w3.eth.contract(address=permit2, abi=permit2_abi)
        permit2_allowance_fct = permit2_contract.functions.allowance(wallet, token, spender)
        amount, expiration, nonce = permit2_allowance_fct.call(block_identifier=block_identifier)
        return Wei(amount), int(expiration), Nonce(nonce)

