[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Wait for User Confirmation Example

This example demonstrates how to use Acontext's experience confirmation feature to allow users to review and approve AI-learned experiences before they are saved to the knowledge base.

## What This Example Does

This example simulates a flight booking conversation where:

1. **Creates a conversation**: Sends a series of messages between a user and an assistant about booking a flight to Tokyo
2. **Waits for learning**: Monitors the Acontext learning process as it analyzes the conversation
3. **Retrieves unconfirmed experiences**: Gets experiences that need user approval (e.g., the user's preference for the cheapest flight)
4. **User review**: Prompts the user to approve or reject each experience before it's saved

## Key Features

- **Experience Confirmation**: Review AI-learned patterns before they become part of the agent's memory
- **Learning Status Monitoring**: Track when Acontext has finished processing conversations
- **Interactive CLI**: User-friendly command-line interface using Rich for colored output
- **Quality Control**: Ensures only approved experiences are saved to the knowledge base

## Prerequisites

- Python 3.13 or higher
- An Acontext API key
- Access to an Acontext instance (local or cloud)

Detail doc is here: https://docs.acontext.io/learn/advance/wait-user.

## Installation

1. Install dependencies using `uv`:

```bash
uv sync
```

2. Set up your environment variables:

Create a `.env` file in the project root:

```env
ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
ACONTEXT_BASE_URL=http://localhost:8029/api/v1
```

Or export them directly:

```bash
export ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
export ACONTEXT_BASE_URL=http://localhost:8029/api/v1
```

## Running the Example

Execute the example:

```bash
uv run main.py
```

### Expected Output

The example will:

1. Display the simulated conversation messages
2. Wait for Acontext to learn from the conversation
3. Show any unconfirmed experiences (e.g., "I only want the cheapest flight")
4. Prompt you to approve (y) or reject (n) each experience

Example interaction:

```
━━━━━━━━━━━━━━━━ Sending Messages ━━━━━━━━━━━━━━━━
user: I want to book a flight to Tokyo. Please help me to book the flight.
assistant: My task is to book the flight to Tokyo. I will start now.
assistant: I have searched the flights
assistant: Done, I have selected the flight
user: You must remember: I only want the cheapest flight
assistant: Done, I have booked the flight
user: Yes, great job!
━━━━━━━━━━━━━━━━ Wait for Task Agent ━━━━━━━━━━━━━━━━
Waiting for the agent learning .....
━━━━━━━━━━━━━━━━ New Experience ━━━━━━━━━━━━━━━━
{
    'data': {
        'preferences': 'Always pick the cheapest flight.', 
        'tool_sops': [], 
        'use_when': 'Flight booking'}, 
    'type': 'sop'
}
Do you approve this experience? (y/n): y
Approved this experience
```

## How It Works

### 1. Space and Session Creation

```python
space = acontext_client.spaces.create()
session = acontext_client.sessions.create(space_id=space.id)
```

Creates a new space (knowledge container) and session (conversation thread).

### 2. Sending Messages

```python
for m in messages:
    acontext_client.sessions.store_message(session_id=session.id, blob=m)
```

Sends each message in the conversation to Acontext for processing.

### 3. Waiting for Learning

```python
acontext_client.sessions.flush(session.id)
while True:
    status = acontext_client.sessions.get_learning_status(session.id)
    if status.not_space_digested_count == 0:
        break
```

Waits for Acontext to finish analyzing and learning from the conversation.

### 4. Reviewing Unconfirmed Experiences

```python
unconfirmed_experiences = acontext_client.spaces.get_unconfirmed_experiences(
    space_id=space.id,
)
```

Retrieves experiences that need user approval.

### 5. Confirming or Rejecting

```python
acontext_client.spaces.confirm_experience(
    space_id=space.id, 
    experience_id=m.id, 
    save=(approve == "y")
)
```

Saves the experience if approved (`y`) or discards it if rejected (`n`).

## Use Cases

This pattern is particularly useful for:

- **Human-in-the-loop AI**: Ensuring AI agents learn appropriate behaviors
- **Quality control**: Reviewing learned patterns before deployment
- **Privacy compliance**: Allowing users to control what information is stored
- **Training supervision**: Curating high-quality training data
- **Error prevention**: Catching and preventing incorrect learnings

## Customization

You can modify the example to:

- Use real conversations instead of mock messages
- Add more sophisticated approval logic
- Integrate with your own workflow systems
- Implement automatic approval based on confidence scores
- Add experience categorization and filtering

## Troubleshooting

### No experiences are generated

If you see "No new experiences, maybe you should adjust the mock messages or just try again":

- The conversation may not contain clear patterns to learn
- Try adding more explicit user preferences or instructions
- Ensure messages contain actionable information

### Learning takes too long

- Check your Acontext instance is running properly
- Verify network connectivity to the Acontext API
- Consider adjusting the polling interval in the `sleep()` call

