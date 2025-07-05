# Builder Coins Agent

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

## Builders Fund - Permissionless Index Fund for Web3 Builders

A decentralized index fund that invests in the most promising builders in the Web3 ecosystem. Built for ETHGlobal Cannes hackathon.

## 🚀 Project Overview

Builders Fund is a permissionless index fund that supports builders in the Web3 ecosystem through a tokenized investment strategy. The fund's value is represented by a token that provides diversified exposure to builder tokens selected by AI agents.

### Key Features

- **Permissionless Builder Economy**: Any builder can launch their personal token with minimum liquidity requirements
- **AI-Powered Fund Management**: Advanced AI agents analyze and select the most promising builder tokens
- **Diversified Investment**: Spread risk across multiple builder tokens while supporting the Web3 ecosystem
- **Transparent Operations**: All fund decisions and holdings are transparent and verifiable on-chain

## 📊 Fund Mechanics

### How It Works

1. **Builders Launch Tokens**: Builders create personal tokens with minimum liquidity
2. **AI Agent Selection**: AI fund manager analyzes and selects promising builder tokens using real Talent Protocol data
3. **Investor Participation**: Buy fund tokens to gain diversified exposure

## ⚙️ Setup & Configuration

### Environment Variables

Create a `.env` file in the agent directory with the following variables:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - for enhanced profile data
TALENT_API_KEY=your_talent_protocol_api_key_here
```

### Installation

1. Install dependencies:

```bash
cd agent
poetry install
```

2. Set up environment variables in `.env` file

3. Run the agent:

```bash
poetry run python agent.py
```

## 🔍 Data Sources & AI Evaluation

The agent fetches real data from:

- **Builder Coins API**: Real token deployment data from Base network
- **Talent Protocol Profile API**: Authentic builder profiles (bio, tags, verification, on-chain history)
- **Talent Protocol Score API**: Official Builder Scores from the separate score endpoint
- **AI Evaluation**: Advanced LLM analysis of profile content across 5 dimensions:
  - Technical Expertise (bio & tags analysis)
  - Experience Level (on-chain history evaluation)
  - Reputation & Credibility (verification status)
  - Innovation Potential (profile content analysis)
  - Community Engagement (profile quality assessment)

## 🧠 Scoring Methodology

The agent uses a sophisticated scoring system:

1. **Official Builder Score (70% weight)**: Direct from Talent Protocol API
2. **AI-Enhanced Evaluation (30% weight)**: Multi-dimensional analysis of profile data
3. **Bonus Factors**: Human verification, ENS name, bio quality, tags diversity, on-chain experience
4. **Fallback Scoring**: Token-based scoring when Talent profiles aren't available

---

**Built with ❤️ for the Web3 community at ETHGlobal Cannes!**
