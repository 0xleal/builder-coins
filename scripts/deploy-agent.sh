# Define the function
get_agent_address() {
  local file=".avctl/config.toml "

  # Check if the file exists
  if [ -f "$file" ]; then
    # Extract the address value
    agent_address=$(grep 'address =' "$file" | sed -E 's/.*= "(.*)"/\1/')

    # Check if the address is not empty
    if [ -n "$agent_address" ]; then
      echo $agent_address
    else
      echo ""
    fi
  else
    echo ""
  fi
}

# Define the specific directory to work on
defined_directory="agent/"

# Change to the specified agent directory
cd "$defined_directory"

# Create a .staging.avctl folder for new agents if it doesn't exist
avctl hosting init

# get the agent address if it exists
agent_address=$(get_agent_address)

# Get the agent's name from the README.md top line header
agent_name=$(head -n 1 README.md | sed -e 's/#//g' | xargs)


# If the address exists...
if [ -n "$agent_address" ]; then
  avctl hosting get agent -a "$agent_address"
  response=$(avctl hosting get agent -a "$agent_address")\

  # Check if the agent is already in existence, if it isn't, deploy as new, else sync.
  if [ $? -eq 0 ]; then
    avctl hosting stop -a "$agent_address"
    avctl hosting sync -a "$agent_address"
  else
    avctl hosting deploy -n "$agent_name" --no-dependency-check || true
  fi
# Agent doesn't exist, so let's deploy
else
  avctl hosting deploy -n "$agent_name" --no-dependency-check || true
fi
