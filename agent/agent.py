from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, Optional
import numpy as np
import json
from datetime import datetime
import uuid
from dataclasses import dataclass
from web3 import Web3
import os

# Web3 setup for Base network
WEB3_PROVIDER_URL = "https://sepolia.base.org"
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

@dataclass
class TalentProfile:
    """Represents a Talent Protocol profile with Builder Score"""
    profile_id: str
    name: str
    builder_score: float
    summary: str
    skills: List[str]
    projects: List[str]
    experience_years: int
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None

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
    min_builder_score: float = 75.0
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
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=os.environ.get('OPENAI_API_KEY')
        )
        self.talent_profiles = self._generate_simulated_talent_profiles()
        self.fund_allocations = []
        
    def _generate_simulated_talent_profiles(self) -> List[TalentProfile]:
        """Generate simulated Talent Protocol profiles with Builder Scores"""
        
        # Simulated data representing diverse builders
        profiles_data = [
            {
                "name": "Alex Chen",
                "builder_score": 94.5,
                "summary": "Full-stack developer specializing in DeFi protocols. Built multiple successful DEX platforms with over $50M in TVL. Expert in Solidity, React, and smart contract security.",
                "skills": ["Solidity", "React", "DeFi", "Smart Contracts", "TypeScript"],
                "projects": ["DeFiSwap", "YieldFarm Pro", "Liquidity Aggregator"],
                "experience_years": 6,
                "token_symbol": "ALEX"
            },
            {
                "name": "Sarah Kim",
                "builder_score": 92.3,
                "summary": "Smart contract auditor and security researcher. Conducted audits for over 100 protocols with zero critical vulnerabilities missed. Specializes in formal verification.",
                "skills": ["Security", "Auditing", "Formal Verification", "Rust", "Solidity"],
                "projects": ["SecureAudit", "ChainGuard", "Vulnerability Scanner"],
                "experience_years": 8,
                "token_symbol": "SARAH"
            },
            {
                "name": "Marcus Johnson",
                "builder_score": 89.7,
                "summary": "NFT marketplace creator and digital artist. Built one of the largest NFT platforms with 1M+ users. Pioneer in NFT standards and cross-chain interoperability.",
                "skills": ["NFT", "Digital Art", "Marketplace", "Ethereum", "IPFS"],
                "projects": ["ArtChain", "NFTLaunch", "CrossChain Bridge"],
                "experience_years": 5,
                "token_symbol": "MARC"
            },
            {
                "name": "Emily Rodriguez",
                "builder_score": 87.2,
                "summary": "Layer 2 scaling solutions architect. Designed and implemented multiple L2 solutions reducing gas costs by 90%. Expert in ZK-proofs and optimistic rollups.",
                "skills": ["Layer 2", "ZK-Proofs", "Optimistic Rollups", "Scalability", "Cryptography"],
                "projects": ["FastChain", "ScaleUp", "ZK-Rollup"],
                "experience_years": 7,
                "token_symbol": "EMILY"
            },
            {
                "name": "David Park",
                "builder_score": 91.8,
                "summary": "DAO governance and treasury management expert. Built governance systems for protocols managing $200M+ in assets. Specialist in tokenomics and incentive design.",
                "skills": ["DAO", "Governance", "Treasury", "Tokenomics", "Economics"],
                "projects": ["GovernanceDAO", "TreasuryManager", "IncentiveDesign"],
                "experience_years": 9,
                "token_symbol": "DAVID"
            },
            {
                "name": "Lisa Wang",
                "builder_score": 88.9,
                "summary": "Cross-chain bridge and interoperability developer. Created bridges connecting 15+ blockchains with $100M+ in daily volume. Expert in atomic swaps and liquidity pools.",
                "skills": ["Cross-chain", "Bridges", "Interoperability", "Atomic Swaps", "Liquidity"],
                "projects": ["BridgeChain", "CrossSwap", "LiquidityPool"],
                "experience_years": 6,
                "token_symbol": "LISA"
            },
            {
                "name": "James Wilson",
                "builder_score": 86.4,
                "summary": "GameFi and metaverse developer. Built successful play-to-earn games with 500K+ active users. Specialist in 3D graphics and blockchain gaming integration.",
                "skills": ["GameFi", "Metaverse", "Unity", "3D Graphics", "Gaming"],
                "projects": ["MetaGame", "PlayToEarn", "VirtualWorld"],
                "experience_years": 4,
                "token_symbol": "JAMES"
            },
            {
                "name": "Maria Garcia",
                "builder_score": 90.1,
                "summary": "Privacy and zero-knowledge proof researcher. Developed privacy-preserving DeFi protocols using advanced cryptographic techniques. Expert in zk-SNARKs and confidential transactions.",
                "skills": ["Privacy", "Zero-Knowledge", "Cryptography", "zk-SNARKs", "Confidential"],
                "projects": ["PrivacyDeFi", "ConfidentialSwap", "ZK-Protocol"],
                "experience_years": 8,
                "token_symbol": "MARIA"
            },
            {
                "name": "Robert Taylor",
                "builder_score": 85.7,
                "summary": "Oracle and data feed developer. Built decentralized oracle networks providing data to 1000+ smart contracts. Specialist in data validation and consensus mechanisms.",
                "skills": ["Oracles", "Data Feeds", "Consensus", "Validation", "Networks"],
                "projects": ["DataOracle", "FeedNetwork", "ConsensusChain"],
                "experience_years": 7,
                "token_symbol": "ROBERT"
            },
            {
                "name": "Anna Thompson",
                "builder_score": 93.2,
                "summary": "DeFi yield optimization and strategy developer. Created automated yield farming strategies generating 25%+ APY. Expert in MEV protection and gas optimization.",
                "skills": ["Yield Farming", "MEV", "Gas Optimization", "Strategies", "Automation"],
                "projects": ["YieldOptimizer", "MEVProtector", "GasSaver"],
                "experience_years": 5,
                "token_symbol": "ANNA"
            }
        ]
        
        # Generate 50 profiles by expanding the base data
        all_profiles = []
        for i, base_profile in enumerate(profiles_data):
            # Create variations of each base profile
            for j in range(5):  # 5 variations per base profile = 50 total
                profile_id = f"talent_{i*5 + j + 1}"
                
                # Add some variation to scores and details
                score_variation = np.random.normal(0, 2)  # ±2 points variation
                adjusted_score = max(70, min(100, base_profile["builder_score"] + score_variation))
                
                # Generate token address (simulated)
                token_address = f"0x{''.join([str(np.random.randint(0, 16)) for _ in range(40)])}"
                
                profile = TalentProfile(
                    profile_id=profile_id,
                    name=f"{base_profile['name']} {chr(65+j)}" if j > 0 else base_profile['name'],
                    builder_score=adjusted_score,
                    summary=base_profile['summary'],
                    skills=base_profile['skills'],
                    projects=base_profile['projects'],
                    experience_years=base_profile['experience_years'],
                    token_address=token_address,
                    token_symbol=f"{base_profile['token_symbol']}{j+1}" if j > 0 else base_profile['token_symbol']
                )
                all_profiles.append(profile)
        
        return all_profiles

    def fetch_talent_profiles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch Talent Protocol profiles with Builder Scores"""
        profiles = self.talent_profiles[:limit]
        return [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "builder_score": p.builder_score,
                "summary": p.summary,
                "skills": p.skills,
                "projects": p.projects,
                "experience_years": p.experience_years,
                "token_address": p.token_address,
                "token_symbol": p.token_symbol
            }
            for p in profiles
        ]

    def analyze_builder_scores(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Builder Scores and provide statistical insights"""
        scores = [p["builder_score"] for p in profiles]
        
        return {
            "total_profiles": len(profiles),
            "average_score": np.mean(scores),
            "median_score": np.median(scores),
            "score_std": np.std(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "score_distribution": {
                "90+": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "70-79": len([s for s in scores if 70 <= s < 80]),
                "<70": len([s for s in scores if s < 70])
            }
        }

    def select_top_builders(self, profiles: List[Dict[str, Any]], target_count: int = 50, min_score: float = 75.0) -> List[Dict[str, Any]]:
        """Select top builders based on Builder Score and profile quality"""
        # Filter by minimum score
        qualified_profiles = [p for p in profiles if p["builder_score"] >= min_score]
        
        # Sort by builder score (descending)
        sorted_profiles = sorted(qualified_profiles, key=lambda x: x["builder_score"], reverse=True)
        
        # Apply additional filters for quality
        final_profiles = []
        for profile in sorted_profiles:
            # Must have token address (simulated deployment)
            if not profile.get("token_address"):
                continue
                
            # Must have meaningful summary
            if len(profile["summary"]) < 50:
                continue
                
            final_profiles.append(profile)
            
            if len(final_profiles) >= target_count:
                break
        
        return final_profiles

    def calculate_optimal_weights(self, selected_builders: List[Dict[str, Any]], max_allocation: float = 5.0, min_allocation: float = 0.5) -> List[Dict[str, Any]]:
        """Calculate optimal allocation weights for selected builders"""
        
        # Multi-factor scoring model
        def calculate_composite_score(profile: Dict[str, Any]) -> float:
            builder_score = profile["builder_score"] / 100.0  # Normalize to 0-1
            
            # Profile quality score (based on summary length and skills)
            summary_quality = min(1.0, len(profile["summary"]) / 200.0)
            skills_diversity = min(1.0, len(profile["skills"]) / 8.0)
            experience_bonus = min(1.0, profile["experience_years"] / 10.0)
            
            # Composite score calculation
            composite_score = (
                builder_score * 0.4 +  # Builder Score (40% weight)
                summary_quality * 0.25 +  # Profile Quality (25% weight)
                skills_diversity * 0.2 +  # Skills Diversity (20% weight)
                experience_bonus * 0.15  # Experience (15% weight)
            )
            
            return composite_score
        
        # Calculate composite scores
        builders_with_scores = []
        for builder in selected_builders:
            composite_score = calculate_composite_score(builder)
            builders_with_scores.append({
                **builder,
                "composite_score": composite_score
            })
        
        # Sort by composite score
        builders_with_scores.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Calculate weights using softmax-like distribution
        scores = np.array([b["composite_score"] for b in builders_with_scores])
        exp_scores = np.exp(scores * 2)  # Temperature parameter
        weights = exp_scores / np.sum(exp_scores)
        
        # Apply constraints
        min_weight = min_allocation / 100.0
        max_weight = max_allocation / 100.0
        
        # Normalize weights to meet constraints
        normalized_weights = []
        for i, weight in enumerate(weights):
            constrained_weight = max(min_weight, min(max_weight, weight))
            normalized_weights.append(constrained_weight)
        
        # Renormalize to sum to 1
        total_weight = sum(normalized_weights)
        final_weights = [w / total_weight for w in normalized_weights]
        
        # Create allocation objects
        allocations = []
        for i, builder in enumerate(builders_with_scores):
            allocation_percentage = final_weights[i] * 100
            
            # Generate reasoning
            reasoning = f"Selected based on high Builder Score ({builder['builder_score']:.1f}), " \
                       f"strong profile quality, diverse skills ({len(builder['skills'])} areas), " \
                       f"and {builder['experience_years']} years of experience. " \
                       f"Composite score: {builder['composite_score']:.3f}"
            
            allocations.append({
                "token_address": builder["token_address"],
                "token_symbol": builder["token_symbol"],
                "builder_name": builder["name"],
                "allocation_percentage": round(allocation_percentage, 2),
                "builder_score": builder["builder_score"],
                "composite_score": builder["composite_score"],
                "reasoning": reasoning
            })
        
        return allocations

    def generate_fund_report(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive fund report with analysis"""
        
        total_allocation = sum(a["allocation_percentage"] for a in allocations)
        avg_builder_score = np.mean([a["builder_score"] for a in allocations])
        
        # Calculate diversity metrics
        skills_set = set()
        for allocation in allocations:
            # Find corresponding profile
            profile = next((p for p in self.talent_profiles if p.token_address == allocation["token_address"]), None)
            if profile:
                skills_set.update(profile.skills)
        
        # Risk analysis
        allocations_sorted = sorted(allocations, key=lambda x: x["allocation_percentage"], reverse=True)
        concentration_risk = allocations_sorted[0]["allocation_percentage"]  # Largest allocation
        
        report = {
            "fund_summary": {
                "total_tokens": len(allocations),
                "total_allocation": round(total_allocation, 2),
                "average_builder_score": round(avg_builder_score, 1),
                "unique_skills": len(skills_set),
                "concentration_risk": round(concentration_risk, 2)
            },
            "top_allocations": allocations_sorted[:10],
            "risk_metrics": {
                "concentration_risk": "Low" if concentration_risk < 3 else "Medium" if concentration_risk < 5 else "High",
                "diversification_score": round(len(skills_set) / len(allocations), 2),
                "quality_score": round(avg_builder_score / 100, 2)
            },
            "generated_at": datetime.now().isoformat(),
            "fund_id": str(uuid.uuid4())
        }
        
        return report

    def create_index_fund(self, request: FundRequest) -> FundResponse:
        """Main method to create the index fund"""
        
        # Step 1: Fetch talent profiles
        profiles = self.fetch_talent_profiles(limit=100)
        
        # Step 2: Analyze builder scores
        score_analysis = self.analyze_builder_scores(profiles)
        
        # Step 3: Select top builders
        selected_builders = self.select_top_builders(
            profiles, 
            target_count=request.target_count,
            min_score=request.min_builder_score
        )
        
        # Step 4: Calculate optimal weights
        allocations = self.calculate_optimal_weights(
            selected_builders,
            max_allocation=request.max_allocation,
            min_allocation=request.min_allocation
        )
        
        # Step 5: Generate fund report
        fund_report = self.generate_fund_report(allocations)
        
        # Store allocations
        self.fund_allocations = allocations
        
        return FundResponse(
            fund_id=fund_report["fund_id"],
            total_tokens=fund_report["fund_summary"]["total_tokens"],
            total_allocation=fund_report["fund_summary"]["total_allocation"],
            average_builder_score=fund_report["fund_summary"]["average_builder_score"],
            allocations=allocations,
            risk_metrics=fund_report["risk_metrics"],
            generated_at=fund_report["generated_at"]
        )

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

print(f"uAgent address: {agent.address}")

@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Agent startup event - fetch ETH balance"""
    wallet_address = "0x81bdC30E4f639BC46963Bb12A1C967dE947ED00f"
    if w3.is_address(wallet_address):
        try:
            balance_wei = w3.eth.get_balance(wallet_address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            ctx.logger.info(f"ETH Balance: {balance_eth} ETH")
        except Exception as e:
            ctx.logger.error(f"Error fetching balance: {str(e)}")
    else:
        ctx.logger.error("Invalid Ethereum wallet address.")

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
            response_text = json.dumps({
                "fund_id": fund_response.fund_id,
                "total_tokens": fund_response.total_tokens,
                "total_allocation": fund_response.total_allocation,
                "average_builder_score": fund_response.average_builder_score,
                "allocations": fund_response.allocations,
                "risk_metrics": fund_response.risk_metrics,
                "generated_at": fund_response.generated_at
            }, indent=2)

            # Format the response
            response_text += f"\n\n\n\n🎯 **Builder Tokens Index Fund Created!**\n\n"
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
            
            response_text += f"\n💡 **How it works:** This fund selects the top 50 Builder Tokens based on Talent Protocol Builder Scores, profile quality, skills diversity, and experience. Each allocation is optimized for maximum diversification while maintaining quality standards."
            
        elif "help" in text.lower() or "what can you do" in text.lower():
            response_text = """🤖 **Builder Tokens Index Fund Agent**

                                I'm an AI agent that creates optimized index funds of Builder Tokens based on Talent Protocol data.

                                **What I can do:**
                                • Create index funds with 50 Builder Tokens
                                • Analyze Builder Scores and profile quality
                                • Calculate optimal allocation weights
                                • Provide risk metrics and diversification analysis

                                **Commands:**
                                • "Create fund" or "Generate fund" - Create a new index fund
                                • "Help" - Show this help message
                                • "Show allocations" - Display current fund allocations

                                **How it works:**
                                I use simulated Talent Protocol profiles with Builder Scores to select the most promising builders. The selection process considers:
                                - Builder Score (40% weight)
                                - Profile Quality (25% weight)  
                                - Skills Diversity (20% weight)
                                - Experience (15% weight)

                                Each fund is optimized for diversification with allocation constraints (0.5% - 5% per token)
                            """
            
        elif "show allocations" in text.lower() or "current fund" in text.lower():
            if fund_agent.fund_allocations:
                response_text = f"📊 **Current Fund Allocations:**\n\n"
                for i, allocation in enumerate(fund_agent.fund_allocations[:10], 1):
                    response_text += f"{i}. {allocation['builder_name']} ({allocation['token_symbol']}): {allocation['allocation_percentage']}% (Score: {allocation['builder_score']:.1f})\n"
                response_text += f"\n... and {len(fund_agent.fund_allocations) - 10} more tokens"
            else:
                response_text = "No fund has been created yet. Use 'Create fund' to generate a new index fund."
        
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