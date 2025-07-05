from uagents import Context
from web3 import Web3
from datetime import datetime
from uuid import uuid4
from openai import OpenAI
from uagents import Context, Protocol, Agent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

WEB3_PROVIDER_URL = f"https://sepolia.base.org"
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

@agent.on_event("startup")
async def fetch_eth_balance(ctx: Context):
    """
    Retrieves ETH balance from Web3 wallet on startup:
    1. Validates the address.
    2. Fetches and logs the balance.
    3. Handles any errors.
    """
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




### Example Expert Assistant
 
## This chat example is a barebones example of how you can create a simple chat agent
## and connect to agentverse. In this example we will be prompting the ASI-1 model to
## answer questions on a specific subject only. This acts as a simple placeholder for
## a more complete agentic system.
 
 
# the subject that this assistant is an expert in
subject_matter = "the sun"
 
client = OpenAI(
    # By default, we are using the ASI-1 LLM endpoint and model
    base_url='https://api.asi1.ai/v1',
 
    # You can get an ASI-1 api key by creating an account at https://asi1.ai/dashboard/api-keys
    api_key='sk_896a5a930d2e4a2c8ed549f6fc53d9c509d24d29d7164838b3e855457f45e19f',
)
 
agent = Agent()
 
# We create a new protocol which is compatible with the chat protocol spec. This ensures
# compatibility between agents
protocol = Protocol(spec=chat_protocol_spec)
 
 
# We define the handler for the chat messages that are sent to your agent
@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # send the acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
 
    # collect up all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
 
    # query the model based on the user question
    response = 'I am afraid something went wrong and I am unable to answer your question at the moment'
    try:
        r = client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": f"""
        You are a helpful assistant who only answers questions about {subject_matter}. If the user asks 
        about any other topics, you should politely say that you do not know about them.
                """},
                {"role": "user", "content": text},
            ],
            max_tokens=2048,
        )
 
        response = str(r.choices[0].message.content)
    except:
        ctx.logger.exception('Error querying model')
 
    # send the response back to the user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            # we send the contents back in the chat message
            TextContent(type="text", text=response),
            # we also signal that the session is over, this also informs the user that we are not recording any of the
            # previous history of messages.
            EndSessionContent(type="end-session"),
        ]
    ))
 
 
@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    # we are not interested in the acknowledgements for this example, but they can be useful to
    # implement read receipts, for example.
    pass
 
 
# attach the protocol to the agent
agent.include(protocol, publish_manifest=True)