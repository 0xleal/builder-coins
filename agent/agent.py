from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from typing import List, Dict, Any, Optional
import numpy as np
import json
from datetime import datetime
import uuid
from dataclasses import dataclass
from web3 import Web3
import os
import requests
from dotenv import load_dotenv
from uniswap_universal_router import Uniswap
from uniswap_universal_router import ERC20_ABI

load_dotenv()

@dataclass
class TalentProfile:
    """Represents a Talent Protocol profile with Builder Score"""
    profile_id: str
    name: str
    builder_score: float
    token_address: str
    token_symbol: str
    token_name: str
    deployer_address: str

@dataclass
class FundAllocation:
    """Represents a token allocation in the fund"""
    token_address: str
    token_symbol: str
    builder_name: str
    allocation_percentage: float
    builder_score: float
    reasoning: str

class FundRequest(Model):
    """Request model for creating an index fund"""
    target_count: int = 50
    min_builder_score: float = 0.0  # Lowered to include more realistic builder scores
    max_allocation: float = 5.0
    min_allocation: float = 0.5

class FundResponse(Model):
    """Response model containing fund allocations"""
    fund_id: str
    total_tokens: int
    total_allocation: float
    average_builder_score: float
    allocations: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]
    generated_at: str

class BuilderTokensIndexFundAgent:
    """AI Agent for creating and managing an index fund of Builder Tokens"""
    
    def __init__(self):
        self.api_base_url = "https://builder-coins.vercel.app/api"
        self.talent_api_base_url = "https://api.talentprotocol.com/"
        self.talent_api_key = os.environ.get('TALENT_API_KEY')
        self.talent_profiles = []
        self.fund_allocations = []
        self.talent_token_address = "0x9a33406165f562E16C3abD82fd1185482E01b49a"
        self.wallet_address = os.environ.get('WALLET_ADDRESS')
        self.private_key = os.environ.get('PRIVATE_KEY')
        self.provider = os.environ.get('WEB3_PROVIDER_URL')
        self.web3 = Web3(Web3.HTTPProvider(self.provider))
        self.uniswap = Uniswap(
            wallet_address=self.wallet_address,
            private_key=self.private_key,
            provider=self.provider,
            web3=self.web3
        )
        
    def _fetch_token_deployments(self, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch token deployments from the API"""
        try:
            url = f"{self.api_base_url}/token-deployment"
            params = {"page": page, "limit": limit}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching token deployments: {e}")
            return []
    
    def _fetch_talent_profile(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Fetch a profile from Talent Protocol API using wallet address"""
        try:
            url = f"{self.talent_api_base_url}/profile"
            params = {"id": wallet_address, "account_source": "wallet"}
            
            headers = {}
            if self.talent_api_key:
                headers["X-API-KEY"] = self.talent_api_key
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching talent profile for {wallet_address}: {e}")
            return None
    
    def _fetch_builder_score(self, wallet_address: str) -> Optional[float]:
        """Fetch Builder Score from Talent Protocol API using wallet address"""
        try:
            url = f"{self.talent_api_base_url}/score"
            params = {
                "id": wallet_address,
                "account_source": "wallet"
            }
            
            headers = {}
            if self.talent_api_key:
                headers["X-API-KEY"] = self.talent_api_key
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                score_data = response.json()
                if 'score' in score_data and score_data['score'] is not None:
                    print(f"Builder score for {wallet_address}: {score_data['score']['points']}")
                    return float(score_data['score']['points'])
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching builder score for {wallet_address}: {e}")
            return None
    
    def _convert_to_talent_profiles(self, token_deployments: List[Dict[str, Any]]) -> List[TalentProfile]:
        """Convert token deployment data to TalentProfile objects using Talent Protocol data"""
        profiles = []
        
        for i, token_data in enumerate(token_deployments):
            try:
                deployer_address = token_data.get('deployer_address', '')
                if not deployer_address:
                    continue
                
                # Fetch profile and builder score from Talent Protocol
                talent_profile = self._fetch_talent_profile(deployer_address)
                builder_score = self._fetch_builder_score(deployer_address)
                
                # Only include profiles with valid builder scores
                if builder_score is None:
                    print(f"✗ No builder score found for {deployer_address[:10]}...")
                    continue
                
                # Extract name from profile or use default
                name = f"Builder {deployer_address[:6]}...{deployer_address[-4:]}"
                if talent_profile and 'profile' in talent_profile:
                    tp_data = talent_profile['profile']
                    name = tp_data.get('display_name') or tp_data.get('name') or name
                
                print(f"✓ Found builder score {builder_score} for {name}")
                
                profile = TalentProfile(
                    profile_id=f"builder_{i+1}",
                    name=name,
                    builder_score=builder_score,
                    token_address=token_data.get('token_address', ''),
                    token_symbol=token_data.get('token_symbol', ''),
                    token_name=token_data.get('token_name', ''),
                    deployer_address=deployer_address
                )
                
                profiles.append(profile)
                
            except Exception as e:
                print(f"Error processing token data {i}: {e}")
                continue
        
        return profiles
    
    def _load_talent_profiles(self) -> List[TalentProfile]:
        """Load talent profiles from the API"""
        if not self.talent_profiles:
            print("Fetching token deployments from API...")
            
            # Fetch multiple pages to get more data
            all_deployments = []
            for page in range(1, 4):  # Fetch first 3 pages
                deployments = self._fetch_token_deployments(page=page, limit=100)
                if not deployments:
                    break
                all_deployments.extend(deployments)
            
            print(f"Fetched {len(all_deployments)} token deployments")
            
            # Convert to talent profiles
            self.talent_profiles = self._convert_to_talent_profiles(all_deployments)
            print(f"Created {len(self.talent_profiles)} talent profiles with valid builder scores")
        
        return self.talent_profiles

    def calculate_allocations(self, profiles: List[TalentProfile], target_count: int = 50, 
                            min_score: float = 0.0, max_allocation: float = 5.0, 
                            min_allocation: float = 0.5) -> List[Dict[str, Any]]:
        """Calculate allocations based solely on builder scores"""
        
        # Filter by minimum score and sort by builder score
        qualified_profiles = [p for p in profiles if p.builder_score >= min_score]
        qualified_profiles.sort(key=lambda x: x.builder_score, reverse=True)
        
        # Take top profiles up to target count
        selected_profiles = qualified_profiles[:target_count]
        
        if not selected_profiles:
            return []
        
        # Calculate allocation weights based on builder scores
        scores = np.array([p.builder_score for p in selected_profiles])
        
        # Use softmax to convert scores to weights
        exp_scores = np.exp(scores / 100)  # Scale down for numerical stability
        weights = exp_scores / np.sum(exp_scores)
        
        # Apply allocation constraints (adjust for small fund sizes)
        num_tokens = len(selected_profiles)
        
        # For small funds, increase max allocation to allow meaningful differentiation
        if num_tokens <= 5:
            effective_max_allocation = 90.0  # Allow up to 90% for very small funds
        elif num_tokens <= 10:
            effective_max_allocation = max(max_allocation, 100.0 / num_tokens * 1.5)  # Up to 1.5x equal weight
        else:
            effective_max_allocation = max_allocation
            
        min_weight = min_allocation / 100.0
        max_weight = effective_max_allocation / 100.0
        
        # Constrain weights
        constrained_weights = np.clip(weights, min_weight, max_weight)
        
        # Renormalize to sum to 1
        constrained_weights = constrained_weights / np.sum(constrained_weights)
        
        # Create allocation objects
        allocations = []
        for i, profile in enumerate(selected_profiles):
            allocation_percentage = constrained_weights[i] * 100
            
            allocations.append({
                "token_address": profile.token_address,
                "token_symbol": profile.token_symbol,
                "builder_name": profile.name,
                "allocation_percentage": round(allocation_percentage, 2),
                "builder_score": profile.builder_score,
                "reasoning": f"Allocation based on Talent Protocol Builder Score of {profile.builder_score}"
            })
        
        return allocations

    def create_index_fund(self, request: FundRequest) -> FundResponse:
        """Main method to create the index fund"""
        
        # Load talent profiles
        profiles = self._load_talent_profiles()
        
        if not profiles:
            raise Exception("No profiles with valid builder scores found")
        
        # Calculate allocations
        allocations = self.calculate_allocations(
            profiles,
            target_count=request.target_count,
            min_score=request.min_builder_score,
            max_allocation=request.max_allocation,
            min_allocation=request.min_allocation
        )

        print(f"Allocations: {allocations}")
        print(f"Profiles: {profiles}")
        
        if not allocations:
            raise Exception("No qualified profiles found for fund creation")
        
        # Calculate metrics
        total_allocation = sum(a["allocation_percentage"] for a in allocations)
        avg_builder_score = np.mean([a["builder_score"] for a in allocations])
        max_single_allocation = max(a["allocation_percentage"] for a in allocations)
        
        # Generate fund report
        fund_id = str(uuid.uuid4())
        risk_metrics = {
            "concentration_risk": "Low" if max_single_allocation < 3 else "Medium" if max_single_allocation < 5 else "High",
            "diversification_score": round(len(allocations) / request.target_count, 2),
            "quality_score": round(avg_builder_score / 1000, 2)
        }
        
        # Store allocations
        self.fund_allocations = allocations

        # Execute fund purchases
        self.execute_fund_purchases(allocations)
        
        return FundResponse(
            fund_id=fund_id,
            total_tokens=len(allocations),
            total_allocation=round(total_allocation, 2),
            average_builder_score=round(avg_builder_score, 1),
            allocations=allocations,
            risk_metrics=risk_metrics,
            generated_at=datetime.now().isoformat()
        )

    def execute_fund_purchases(self, allocations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute token purchases using Uniswap V4"""
        if not self.uniswap:
            raise Exception("Uniswap not initialized")
            
        # Get the agent's wallet address
        wallet_address = self.uniswap.wallet_address
        print(f"Wallet address: {wallet_address}")

        # Get the agent's balance for $TALENT token
        token = self.uniswap.w3.eth.contract(address=self.talent_token_address, abi=ERC20_ABI)
        balance = token.functions.balanceOf(wallet_address).call()
        print(f"Balance: {balance}")

        for allocation in allocations:
            token_address = allocation["token_address"]
            
            allocation_amount = allocation["allocation_percentage"] * balance / 100
            print(f"Allocation amount: {allocation_amount}")

            # Round down to 6 decimal places
            rounded_allocation_amount = int(allocation_amount * 10**6) / 10**6

            amount_in_wei = self.web3.to_wei(rounded_allocation_amount, "ether")
            print(f"Amount in wei: {amount_in_wei}")

            try:
                tx_hash = self.uniswap.make_trade(
                    from_token=self.talent_token_address,
                    to_token=token_address,
                    amount=amount_in_wei,
                    fee=2000,         # e.g., 3000 for a 0.3% Uniswap V3 pool
                    slippage=0.5,     # non-functional right now. 0.5% slippage tolerance
                    pool_version="v4"  # can be "v3" or "v4"
                )
                print(f"Swap transaction sent! Tx hash: {tx_hash.hex()}")
            except Exception as e:
                print(f"Swap failed: {e}")

# Create the uAgent
agent = Agent(
    name="builder_tokens_index_fund_agent",
    port=8000,
    seed="builder-tokens-index-fund-seed",
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Fund the agent if needed
fund_agent_if_low(agent.wallet.address())

# Create the fund management protocol
fund_protocol = Protocol("Builder Tokens Index Fund")

# Create the chat protocol
chat_protocol = Protocol(spec=chat_protocol_spec)

# Initialize the fund agent
fund_agent = BuilderTokensIndexFundAgent()

@agent.on_message(model=FundRequest, replies=FundResponse)
async def handle_fund_request(ctx: Context, sender: str, msg: FundRequest):
    """Handle requests to create or update the index fund"""
    ctx.logger.info(f"Received fund request from {sender}")
    ctx.logger.info(f"Target count: {msg.target_count}, Min score: {msg.min_builder_score}")
    
    try:
        # Create the index fund
        fund_response = fund_agent.create_index_fund(msg)
        
        # Log the results
        ctx.logger.info(f"Created fund with {fund_response.total_tokens} tokens")
        ctx.logger.info(f"Average builder score: {fund_response.average_builder_score}")
        ctx.logger.info(f"Total allocation: {fund_response.total_allocation}%")
        
        # Send the response back
        await ctx.send(sender, fund_response)
        
        # Save to file for reference
        with open("fund_report.json", "w") as f:
            json.dump({
                "fund_id": fund_response.fund_id,
                "total_tokens": fund_response.total_tokens,
                "total_allocation": fund_response.total_allocation,
                "average_builder_score": fund_response.average_builder_score,
                "allocations": fund_response.allocations,
                "risk_metrics": fund_response.risk_metrics,
                "generated_at": fund_response.generated_at
            }, f, indent=2)
        
        ctx.logger.info("Fund report saved to fund_report.json")
        
    except Exception as e:
        ctx.logger.error(f"Error creating fund: {str(e)}")
        # Send error response
        error_response = FundResponse(
            fund_id="",
            total_tokens=0,
            total_allocation=0.0,
            average_builder_score=0.0,
            allocations=[],
            risk_metrics={"error": str(e)},
            generated_at=datetime.now().isoformat()
        )
        await ctx.send(sender, error_response)

# Chat protocol handlers
@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle chat messages from the Agent Inspector"""
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
 
    # Collect text content
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
 
    ctx.logger.info(f"Received chat message: {text}")
    
    # Process the message and generate response
    try:
        # Check if it's a fund creation request
        if "create fund" in text.lower() or "generate fund" in text.lower():
            # Create a default fund request
            fund_request = FundRequest()
            fund_response = fund_agent.create_index_fund(fund_request)

            # Format the response
            response_text = f"\n\n\n\n🎯 **Builder Tokens Index Fund Created!**\n\n"
            response_text += f"📊 **Fund Summary:**\n"
            response_text += f"• Total Tokens: {fund_response.total_tokens}\n"
            response_text += f"• Total Allocation: {fund_response.total_allocation}%\n"
            response_text += f"• Average Builder Score: {fund_response.average_builder_score}\n"
            response_text += f"• Risk Level: {fund_response.risk_metrics.get('concentration_risk', 'Unknown')}\n\n"
            
            response_text += f"🏆 **Top 5 Allocations:**\n"
            for i, allocation in enumerate(fund_response.allocations[:5], 1):
                response_text += f"{i}. {allocation['builder_name']} ({allocation['token_symbol']}): {allocation['allocation_percentage']}%\n"
            
            response_text += f"\n📈 **Risk Metrics:**\n"
            response_text += f"• Diversification Score: {fund_response.risk_metrics.get('diversification_score', 0)}\n"
            response_text += f"• Quality Score: {fund_response.risk_metrics.get('quality_score', 0)}\n"
            
            response_text += f"\n💡 **How it works:** This fund selects Builder Tokens from real deployment data on Base network, using authentic Talent Protocol Builder Scores. Allocations are calculated based purely on official Builder Scores from the Talent Protocol API."
            
        elif "help" in text.lower() or "what can you do" in text.lower():
            response_text = """🤖 **Builder Tokens Index Fund Agent**

                                I'm an AI agent that creates index funds of Builder Tokens using real deployment data from Base network and authentic Talent Protocol Builder Scores.

                                **What I can do:**
                                • Create index funds with up to 50 Builder Tokens
                                • Fetch real Talent Protocol profiles and official Builder Scores
                                • Calculate allocation weights based on Builder Scores
                                • Provide risk metrics and diversification analysis

                                **Commands:**
                                • "Create fund" or "Generate fund" - Create a new index fund
                                • "Help" - Show this help message
                                • "Show allocations" - Display current fund allocations

                                **How it works:**
                                1. I fetch real token deployment data from the builder-coins API
                                2. For each token deployer, I query the Talent Protocol API to get their profile
                                3. I fetch official Builder Scores from the Talent Protocol score endpoint
                                4. I calculate allocations based purely on the Builder Scores using softmax distribution
                                5. I apply allocation constraints (0.5% - 5% per token)

                                The fund is optimized for diversification while maintaining quality standards based on Builder Scores.
                            """
            
        elif "show allocations" in text.lower() or "current fund" in text.lower():
            if fund_agent.fund_allocations:
                response_text = f"📊 **Current Fund Allocations:**\n\n"
                for i, allocation in enumerate(fund_agent.fund_allocations[:10], 1):
                    response_text += f"{i}. {allocation['builder_name']} ({allocation['token_symbol']}): {allocation['allocation_percentage']}% (Builder Score: {allocation['builder_score']:.1f})\n"
                if len(fund_agent.fund_allocations) > 10:
                    response_text += f"\n... and {len(fund_agent.fund_allocations) - 10} more tokens"
            else:
                response_text = "No fund has been created yet. Use 'Create fund' to generate a new index fund."

        else:
            response_text = "I'm the Builder Tokens Index Fund Agent! I can help you create optimized index funds of Builder Tokens. Try saying 'Create fund' or 'Help' to get started."
        
    except Exception as e:
        ctx.logger.error(f"Error processing chat message: {str(e)}")
        response_text = f"Sorry, I encountered an error: {str(e)}"
    
    # Send the response
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid.uuid4(),
        content=[
            TextContent(type="text", text=response_text),
            EndSessionContent(type="end-session"),
        ]
    ))
 
@chat_protocol.on_message(ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    pass

# Include both protocols
agent.include(fund_protocol, publish_manifest=True)
agent.include(chat_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()