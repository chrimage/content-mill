from openai import OpenAI
import os
import sys
import json
import dotenv

# Load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# prompt the user for the topic
topic = input("What topic should the AI debate?")
proponent_name = input("What is the name of the proponent?")
opponent_name = input("What is the name of the opponent?")

# initialize the list of messages
debate_messages = []

def get_moderator_response(debate_messages):
    """
    Generate a response for the moderator using OpenAI's GPT-4 model.

    Parameters:
    debate_messages (list): The list of debate messages

    Returns:
    str: The generated response
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "system",
                "content": f"You are the moderator. You are moderating the debate between {proponent_name} and {opponent_name} on {topic}. When the debate is over, say 'Thank you for participating in this debate.'"
            },
            {
                "role": "user",
                "content": "\n".join([message[1] for message in debate_messages]),
            },
        ],
    )

    debate_messages.append(("moderator", response.choices[0].message.content))

    return response.choices[0].message.content

def get_proponent_response(debate_messages):
    """
    Generate a response for the proponent using OpenAI's GPT-4 model.

    Parameters:
    debate_messages (list): The list of debate messages

    Returns:
    str: The generated response
    """
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": f"You are {proponent_name}. You are debating as a proponent of {topic}."
            },
            {
                "role": "user",
                "content": "\n".join([message[1] for message in debate_messages]),
            },
        ],
    )

    debate_messages.append((proponent_name, response.choices[0].message.content))

    return response.choices[0].message.content

def get_opponent_response(debate_messages):
    """
    Generate a response for the opponent using OpenAI's GPT-4 model.

    Parameters:
    debate_messages (list): The list of debate messages

    Returns:
    str: The generated response
    """
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": f"You are {opponent_name}. You are debating as an opponent of {topic}."
            },
            {
                "role": "user",
                "content": "\n".join([message[1] for message in debate_messages]),
            },
        ],
    )

    debate_messages.append((opponent_name, response.choices[0].message.content))

    return response.choices[0].message.content

moderator_response = get_moderator_response(debate_messages)
print(f"Moderator: {moderator_response}")

# start the debate
while True:

    # get the proponent response
    proponent_response = get_proponent_response(debate_messages)
    print(f"{proponent_name}: {proponent_response}")

    # get the opponent response
    opponent_response = get_opponent_response(debate_messages)
    print(f"{opponent_name}: {opponent_response}")

    # get the moderator response
    moderator_response = get_moderator_response(debate_messages)
    print(f"Moderator: {moderator_response}")

    # check if the debate is over
    if moderator_response.endswith("Thank you for participating in this debate."):
        break