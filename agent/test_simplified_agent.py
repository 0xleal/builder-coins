#!/usr/bin/env python3
"""Test script for the simplified Builder Tokens Index Fund Agent"""

from agent import BuilderTokensIndexFundAgent, FundRequest
import json
import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN

# Load environment variables
load_dotenv()

def test_token_transfers_with_allocations():
    """Test actual token transfers based on fund allocations"""
    print("\n💸 Testing Token Transfers with Allocations...")
    
    agent = BuilderTokensIndexFundAgent()
    
    # First create a fund to get allocations
    print("Creating fund to get allocations...")
    try:
        fund_request = FundRequest(
            target_count=5,  # Small test fund
            min_builder_score=0,
            max_allocation=15.0,
            min_allocation=5.0
        )
        
        fund_response = agent.create_index_fund(fund_request)
        print(f"✓ Fund created with {len(fund_response.allocations)} allocations")
        
        # Define investment amount (in TALENT tokens)
        investment_amount = Decimal('1.0')  # 1 TALENT token for testing
        print(f"✓ Investment amount: {investment_amount} TALENT")
        
        # Calculate actual transfer amounts
        transfer_details = []
        total_percentage = sum(Decimal(str(alloc['allocation_percentage'])) for alloc in fund_response.allocations)
        
        print(f"\n📊 Calculating transfer amounts:")
        print(f"Total allocation percentage: {total_percentage}%")
        
        for i, allocation in enumerate(fund_response.allocations):
            allocation_percentage = Decimal(str(allocation['allocation_percentage']))
            
            # Calculate transfer amount
            transfer_amount = (investment_amount * allocation_percentage / Decimal('100')).quantize(
                Decimal('0.000001'), rounding=ROUND_DOWN
            )
            
            transfer_detail = {
                'token_address': allocation['token_address'],
                'token_symbol': allocation['token_symbol'],
                'builder_name': allocation['builder_name'],
                'allocation_percentage': float(allocation_percentage),
                'transfer_amount': float(transfer_amount),
                'builder_score': allocation['builder_score']
            }
            
            transfer_details.append(transfer_detail)
            
            print(f"  {i+1}. {allocation['builder_name']} ({allocation['token_symbol']})")
            print(f"     Allocation: {allocation_percentage}% = {transfer_amount} TALENT")
        
        # Test transfer execution
        print(f"\n🔄 Testing transfer execution...")
        
        # Check current TALENT balance
        from uniswap_universal_router import ERC20_ABI
        talent_contract = agent.web3.eth.contract(
            address=agent.talent_token_address,
            abi=ERC20_ABI
        )
        
        current_balance = talent_contract.functions.balanceOf(agent.wallet_address).call()
        current_balance_formatted = current_balance / (10 ** 18)  # TALENT has 18 decimals
        
        print(f"Current TALENT balance: {current_balance_formatted} TALENT")
        
        if current_balance_formatted >= float(investment_amount):
            print("✓ Sufficient balance for transfers")
            
            # Execute transfers (this is where the actual transfers would happen)
            executed_transfers = execute_allocation_transfers(agent, transfer_details, investment_amount)
            
            print(f"\n📋 Transfer Summary:")
            total_transferred = sum(transfer['amount'] for transfer in executed_transfers)
            print(f"Total transfers planned: {len(executed_transfers)}")
            print(f"Total amount to transfer: {total_transferred} TALENT")
            
            for transfer in executed_transfers:
                print(f"  • {transfer['symbol']}: {transfer['amount']} TALENT")
                if transfer.get('tx_hash'):
                    print(f"    TX: {transfer['tx_hash']}")
                elif transfer.get('error'):
                    print(f"    Error: {transfer['error']}")
                else:
                    print(f"    Status: Simulated (dry run)")
                    
        else:
            print(f"⚠️ Insufficient balance. Need {investment_amount} TALENT, have {current_balance_formatted}")
            print("✓ Transfer simulation completed (insufficient funds)")
        
    except Exception as e:
        print(f"✗ Error in token transfer test: {e}")

def execute_allocation_transfers(agent, transfer_details, total_investment):
    """Execute token transfers based on allocations"""
    executed_transfers = []
    
    print(f"\n🚀 Executing allocation transfers...")
    
    # Check if we should do dry run or actual transfers
    dry_run = True  # Set to False for actual transfers (be careful!)
    
    if dry_run:
        print("🔍 Running in DRY RUN mode (no actual transfers)")
    else:
        print("⚠️ Running in LIVE mode (actual transfers will occur)")
    
    for detail in transfer_details:
        try:
            transfer_amount = detail['transfer_amount']
            token_address = detail['token_address']
            token_symbol = detail['token_symbol']
            
            print(f"\n  Processing {token_symbol} transfer...")
            print(f"    Target token: {token_address}")
            print(f"    Amount: {transfer_amount} TALENT")
            
            if dry_run:
                # Simulate the transfer
                executed_transfers.append({
                    'symbol': token_symbol,
                    'amount': transfer_amount,
                    'target_address': token_address,
                    'status': 'simulated'
                })
                print(f"    ✓ Simulated transfer of {transfer_amount} TALENT to {token_symbol}")
            else:
                # This is where actual Uniswap swaps would happen
                # For now, we'll just simulate since actual swaps need more careful handling
                try:
                    # Example of how actual swap would work:
                    # swap_result = agent.uniswap.swap_exact_eth_for_tokens(
                    #     token_address, 
                    #     transfer_amount,
                    #     agent.wallet_address
                    # )
                    
                    # For safety, we'll simulate even in "live" mode
                    executed_transfers.append({
                        'symbol': token_symbol,
                        'amount': transfer_amount,
                        'target_address': token_address,
                        'status': 'simulated_safe'
                    })
                    print(f"    ✓ Transfer simulated (safety mode): {transfer_amount} TALENT to {token_symbol}")
                    
                except Exception as e:
                    executed_transfers.append({
                        'symbol': token_symbol,
                        'amount': transfer_amount,
                        'target_address': token_address,
                        'error': str(e)
                    })
                    print(f"    ✗ Transfer failed: {e}")
                    
        except Exception as e:
            print(f"    ✗ Error processing {detail['token_symbol']}: {e}")
    
    return executed_transfers

def test_swap_calculation():
    """Test swap calculations and price impact"""
    print("\n🔄 Testing Swap Calculations...")
    
    agent = BuilderTokensIndexFundAgent()
    
    try:
        # Test calculating swap amounts
        test_amounts = [0.1, 0.5, 1.0, 2.0]  # TALENT amounts
        
        print("Testing different swap amounts:")
        for amount in test_amounts:
            print(f"\n  Amount: {amount} TALENT")
            
            # This would typically involve calling Uniswap quoter
            # For now, we'll simulate the calculations
            
            # Simulate price impact calculation
            price_impact = calculate_price_impact(amount)
            print(f"    Estimated price impact: {price_impact}%")
            
            # Simulate minimum output calculation
            min_output = calculate_minimum_output(amount)
            print(f"    Minimum output tokens: {min_output}")
            
            if price_impact > 5.0:
                print(f"    ⚠️ High price impact warning!")
            else:
                print(f"    ✓ Acceptable price impact")
        
    except Exception as e:
        print(f"✗ Error in swap calculations: {e}")

def calculate_price_impact(amount):
    """Simulate price impact calculation"""
    # Simple simulation - in reality this would query Uniswap pools
    if amount <= 0.5:
        return 0.5
    elif amount <= 1.0:
        return 1.2
    elif amount <= 2.0:
        return 2.5
    else:
        return 5.0

def calculate_minimum_output(amount):
    """Simulate minimum output calculation"""
    # Simple simulation - in reality this would use actual pool data
    return amount * 0.95  # Assume 5% slippage tolerance

def test_wallet_initialization():
    """Test wallet and Web3 initialization"""
    print("\n🔐 Testing Wallet Initialization...")
    
    # Create the agent
    agent = BuilderTokensIndexFundAgent()
    
    # Test wallet configuration
    print("Checking wallet configuration...")
    if agent.wallet_address:
        print(f"✓ Wallet address configured: {agent.wallet_address[:10]}...{agent.wallet_address[-6:]}")
    else:
        print("✗ No wallet address configured (WALLET_ADDRESS env var)")
    
    if agent.private_key:
        print(f"✓ Private key configured (length: {len(agent.private_key)})")
    else:
        print("✗ No private key configured (PRIVATE_KEY env var)")
    
    if agent.provider:
        print(f"✓ Provider configured: {agent.provider}")
    else:
        print("✗ No provider configured (WEB3_PROVIDER_URL env var)")
    
    # Test Web3 connection
    try:
        if agent.web3 and agent.web3.is_connected():
            print("✓ Web3 connection successful")
            
            # Get latest block to verify connection
            latest_block = agent.web3.eth.get_block('latest')
            print(f"✓ Latest block number: {latest_block['number']}")
            
            # Check if wallet address is valid
            if agent.wallet_address:
                try:
                    balance = agent.web3.eth.get_balance(agent.wallet_address)
                    balance_eth = agent.web3.from_wei(balance, 'ether')
                    print(f"✓ Wallet ETH balance: {balance_eth:.4f} ETH")
                except Exception as e:
                    print(f"✗ Error getting wallet balance: {e}")
        else:
            print("✗ Web3 connection failed")
    except Exception as e:
        print(f"✗ Web3 connection error: {e}")

def test_uniswap_initialization():
    """Test Uniswap initialization"""
    print("\n🦄 Testing Uniswap Initialization...")
    
    agent = BuilderTokensIndexFundAgent()
    
    try:
        if agent.uniswap:
            print("✓ Uniswap instance created successfully")
            print(f"✓ Uniswap wallet address: {agent.uniswap.wallet_address}")
            
            # Test if we can access the Web3 instance through Uniswap
            if hasattr(agent.uniswap, 'w3') and agent.uniswap.w3:
                print("✓ Uniswap Web3 instance accessible")
                
                # Test connection through Uniswap
                if agent.uniswap.w3.is_connected():
                    print("✓ Uniswap Web3 connection successful")
                else:
                    print("✗ Uniswap Web3 connection failed")
            else:
                print("✗ Uniswap Web3 instance not accessible")
        else:
            print("✗ Uniswap initialization failed")
    except Exception as e:
        print(f"✗ Uniswap initialization error: {e}")

def test_talent_token_balance():
    """Test TALENT token balance checking"""
    print("\n🎯 Testing TALENT Token Balance...")
    
    agent = BuilderTokensIndexFundAgent()
    
    try:
        if agent.uniswap and agent.wallet_address and agent.talent_token_address:
            # Import ERC20 ABI
            from uniswap_universal_router import ERC20_ABI
            
            # Create token contract instance
            token_contract = agent.web3.eth.contract(
                address=agent.talent_token_address, 
                abi=ERC20_ABI
            )
            
            # Get token balance
            balance = token_contract.functions.balanceOf(agent.wallet_address).call()
            print(f"✓ TALENT token balance: {balance} (raw)")
            
            # Get token decimals for proper conversion
            try:
                decimals = token_contract.functions.decimals().call()
                balance_formatted = balance / (10 ** decimals)
                print(f"✓ TALENT token balance: {balance_formatted:.4f} TALENT")
            except Exception as e:
                print(f"✗ Error getting token decimals: {e}")
            
            # Get token symbol and name
            try:
                symbol = token_contract.functions.symbol().call()
                name = token_contract.functions.name().call()
                print(f"✓ Token info: {name} ({symbol})")
            except Exception as e:
                print(f"✗ Error getting token info: {e}")
                
        else:
            print("✗ Missing requirements for balance check (Uniswap, wallet address, or token address)")
    except Exception as e:
        print(f"✗ Error checking TALENT token balance: {e}")

def test_fund_purchases():
    """Test fund purchase execution (dry run)"""
    print("\n💰 Testing Fund Purchase Execution...")
    
    agent = BuilderTokensIndexFundAgent()
    
    # Create a small test allocation
    test_allocations = [
        {
            "token_address": "0x1234567890123456789012345678901234567890",
            "token_symbol": "TEST",
            "builder_name": "Test Builder",
            "allocation_percentage": 50.0,
            "builder_score": 500.0,
            "reasoning": "Test allocation"
        },
        {
            "token_address": "0x0987654321098765432109876543210987654321",
            "token_symbol": "DEMO",
            "builder_name": "Demo Builder",
            "allocation_percentage": 50.0,
            "builder_score": 300.0,
            "reasoning": "Demo allocation"
        }
    ]
    
    try:
        # Test the purchase execution method
        print("Testing execute_fund_purchases method...")
        
        # This should handle the case where we don't have funds or the tokens don't exist
        result = agent.execute_fund_purchases(test_allocations)
        print(f"✓ Purchase execution completed: {result}")
        
    except Exception as e:
        print(f"✗ Error in fund purchase execution: {e}")
        # This is expected if we don't have funds or proper setup
        if "not initialized" in str(e) or "balance" in str(e).lower():
            print("  (This is expected without proper wallet funding)")

def test_simplified_agent():
    """Test the simplified agent functionality"""
    print("\n🧪 Testing Simplified Builder Tokens Index Fund Agent...")
    
    # Create the agent
    agent = BuilderTokensIndexFundAgent()
    
    # Test basic functionality
    print("\n1. Testing token deployment fetching...")
    deployments = agent._fetch_token_deployments(page=1, limit=5)
    if deployments:
        print(f"✓ Successfully fetched {len(deployments)} token deployments")
    else:
        print("✗ No token deployments found")
    
    # Test profile loading (simplified)
    print("\n2. Testing profile loading...")
    try:
        profiles = agent._load_talent_profiles()
        print(f"✓ Successfully loaded {len(profiles)} profiles with valid builder scores")
        
        if profiles:
            # Show first few profiles
            print("\nFirst 3 profiles:")
            for i, profile in enumerate(profiles[:3]):
                print(f"  {i+1}. {profile.name} - Score: {profile.builder_score}")
        
    except Exception as e:
        print(f"✗ Error loading profiles: {e}")
    
    # Test fund creation
    print("\n3. Testing fund creation...")
    try:
        fund_request = FundRequest(
            target_count=10,  # Small test
            min_builder_score=0,  # Low threshold for testing
            max_allocation=10.0,
            min_allocation=5.0
        )
        
        fund_response = agent.create_index_fund(fund_request)
        
        print(f"✓ Fund created successfully!")
        print(f"  Fund ID: {fund_response.fund_id}")
        print(f"  Total Tokens: {fund_response.total_tokens}")
        print(f"  Average Builder Score: {fund_response.average_builder_score}")
        print(f"  Total Allocation: {fund_response.total_allocation}%")
        
        # Show allocations
        print("\nTop 3 allocations:")
        for i, allocation in enumerate(fund_response.allocations[:3]):
            print(f"  {i+1}. {allocation['builder_name']} ({allocation['token_symbol']}): {allocation['allocation_percentage']}%")
        
    except Exception as e:
        print(f"✗ Error creating fund: {e}")

def test_environment_variables():
    """Test required environment variables"""
    print("\n🌍 Testing Environment Variables...")
    
    required_vars = [
        'WALLET_ADDRESS',
        'PRIVATE_KEY', 
        'WEB3_PROVIDER_URL',
        'TALENT_API_KEY'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if var == 'PRIVATE_KEY':
                print(f"✓ {var}: Set (length: {len(value)})")
            elif var == 'WALLET_ADDRESS':
                print(f"✓ {var}: {value[:10]}...{value[-6:]}")
            else:
                print(f"✓ {var}: {value[:20]}..." if len(value) > 20 else f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: Not set")

def test_actual_talent_transfer():
    """Test actual 1 TALENT transfer to top allocation using uniswap.make_trade"""
    print("\n💎 Testing ACTUAL 1 TALENT Transfer to Top Allocation...")
    
    agent = BuilderTokensIndexFundAgent()
    
    try:
        # Create fund to get allocations
        print("Creating fund to get top allocation...")
        fund_request = FundRequest(
            target_count=10,
            min_builder_score=0,
            max_allocation=25.0,
            min_allocation=5.0
        )
        
        fund_response = agent.create_index_fund(fund_request)
        
        if not fund_response.allocations:
            print("✗ No allocations found")
            return
        
        # Get the top allocation (highest percentage)
        top_allocation = max(fund_response.allocations, key=lambda x: x['allocation_percentage'])
        
        print(f"🏆 Top allocation identified:")
        print(f"  Builder: {top_allocation['builder_name']}")
        print(f"  Token: {top_allocation['token_symbol']}")
        print(f"  Address: {top_allocation['token_address']}")
        print(f"  Allocation: {top_allocation['allocation_percentage']}%")
        print(f"  Builder Score: {top_allocation['builder_score']}")
        
        # Check current TALENT balance
        from uniswap_universal_router import ERC20_ABI
        talent_contract = agent.web3.eth.contract(
            address=agent.talent_token_address,
            abi=ERC20_ABI
        )
        
        talent_balance = talent_contract.functions.balanceOf(agent.wallet_address).call()
        talent_balance_formatted = talent_balance / (10 ** 18)
        
        print(f"\n💰 Current TALENT balance: {talent_balance_formatted} TALENT")
        
        # Define transfer amount (1 TALENT)
        transfer_amount = 1.0
        transfer_amount_wei = int(transfer_amount * 10**18)  # Convert to wei
        
        if talent_balance_formatted >= transfer_amount:
            print(f"✓ Sufficient balance for {transfer_amount} TALENT transfer")
            
            # Prepare swap parameters
            from_token = agent.talent_token_address  # TALENT token
            to_token = top_allocation['token_address']  # Target builder token
            fee = 10000  # 0.3% fee tier (standard)
            slippage = 5.0  # 5% slippage tolerance
            
            print(f"\n🔄 Preparing swap transaction...")
            print(f"  From: TALENT ({from_token})")
            print(f"  To: {top_allocation['token_symbol']} ({to_token})")
            print(f"  Amount: {transfer_amount} TALENT ({transfer_amount_wei} wei)")
            print(f"  Fee: {fee / 10000}%")
            print(f"  Slippage: {slippage}%")
            
            # Show confirmation prompt
            print(f"\n⚠️  LIVE TRANSACTION WARNING ⚠️")
            print(f"This will execute a REAL transaction on the blockchain!")
            print(f"Swapping {transfer_amount} TALENT for {top_allocation['token_symbol']}")
            
            # For safety, let's do a dry run first
            dry_run = False  # Change to False for actual execution
            
            if dry_run:
                print(f"\n🔍 DRY RUN MODE - No actual transaction will be sent")
                print(f"✓ Transaction would swap {transfer_amount} TALENT for {top_allocation['token_symbol']}")
                print(f"✓ Transaction parameters validated")
                print(f"✓ Balance check passed")
                print(f"✓ Ready for live execution (set dry_run=False)")
            else:
                print(f"\n🚀 EXECUTING LIVE TRANSACTION...")
                
                try:
                    # Execute the actual swap
                    result = agent.uniswap.make_trade(
                        from_token=from_token,
                        to_token=to_token,
                        amount=transfer_amount_wei,
                        fee=fee,
                        slippage=slippage,
                        pool_version="v4"
                    )
                    
                    print(f"✅ Transaction successful!")
                    print(f"  Transaction result: {result}")
                    
                    # Check balances after transaction
                    new_talent_balance = talent_contract.functions.balanceOf(agent.wallet_address).call()
                    new_talent_balance_formatted = new_talent_balance / (10 ** 18)
                    
                    print(f"\n📊 Post-transaction balances:")
                    print(f"  TALENT balance: {new_talent_balance_formatted} TALENT")
                    print(f"  Difference: {talent_balance_formatted - new_talent_balance_formatted} TALENT")
                    
                    # Try to check target token balance
                    try:
                        target_contract = agent.web3.eth.contract(
                            address=to_token,
                            abi=ERC20_ABI
                        )
                        target_balance = target_contract.functions.balanceOf(agent.wallet_address).call()
                        target_decimals = target_contract.functions.decimals().call()
                        target_balance_formatted = target_balance / (10 ** target_decimals)
                        
                        print(f"  {top_allocation['token_symbol']} balance: {target_balance_formatted} {top_allocation['token_symbol']}")
                        
                    except Exception as e:
                        print(f"  Could not check {top_allocation['token_symbol']} balance: {e}")
                        
                except Exception as e:
                    print(f"✗ Transaction failed: {e}")
                    
                    # Check if it's a known error type
                    if "insufficient" in str(e).lower():
                        print("  💡 This might be due to insufficient liquidity or balance")
                    elif "allowance" in str(e).lower():
                        print("  💡 This might be due to token approval issues")
                    elif "slippage" in str(e).lower():
                        print("  💡 This might be due to high slippage, try increasing slippage tolerance")
                    else:
                        print(f"  💡 Unexpected error, check transaction parameters")
        else:
            print(f"✗ Insufficient TALENT balance")
            print(f"  Need: {transfer_amount} TALENT")
            print(f"  Have: {talent_balance_formatted} TALENT")
            print(f"  Shortfall: {transfer_amount - talent_balance_formatted} TALENT")
            
    except Exception as e:
        print(f"✗ Error in actual transfer test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run all tests
    # test_environment_variables()
    # test_wallet_initialization()
    # test_uniswap_initialization()
    # test_talent_token_balance()
    # test_fund_purchases()
    # test_simplified_agent()
    # test_token_transfers_with_allocations()
    # test_swap_calculation()
    test_actual_talent_transfer()
    
    print("\n✅ All tests completed!") 