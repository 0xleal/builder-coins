#!/usr/bin/env python3
"""Test script for the simplified Builder Tokens Index Fund Agent"""

from agent import BuilderTokensIndexFundAgent, FundRequest
import json

def test_simplified_agent():
    """Test the simplified agent functionality"""
    print("🧪 Testing Simplified Builder Tokens Index Fund Agent...")
    
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
    
    print("\n✅ Simplified agent test completed!")

if __name__ == "__main__":
    test_simplified_agent() 