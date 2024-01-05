from openai import OpenAI
from pathlib import Path
import os
import sys
import json
import dotenv
import slugify
import requests

# Load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# prompt the user for the topic
topic = input("What topic should the AI debate?")
proponent_name = input("What is the name of the proponent?")
opponent_name = input("What is the name of the opponent?")

moderator_model="gpt-3.5-turbo-1106"
proponent_model="gpt-4-1106-preview"
opponent_model="gpt-4-1106-preview"

# initialize the list of messages
debate_messages = []


def get_moderator_response(debate_messages, instruction=""):
    response = client.chat.completions.create(
        model=moderator_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": f"You are the moderator. You are moderating the debate between {proponent_name} and {opponent_name} on {topic}. Your response should be a json object with the keys 'speaker' and 'content'",
            },
            {
                "role": "user",
                "content": json.dumps(debate_messages),
            },
            {
                "role": "user",
                "content": instruction,
            },
        ],
    )

    response = json.loads(response.choices[0].message.content)

    debate_messages.append(response)

    return response


def get_proponent_response(debate_messages):
    response = client.chat.completions.create(
        model=proponent_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": f"You are {proponent_name}. You are debating as a proponent of {topic}. Your response should be a json object with the keys 'speaker' and 'content'",
            },
            {
                "role": "user",
                "content": json.dumps(debate_messages),
            },
        ],
    )
    response = json.loads(response.choices[0].message.content)
    debate_messages.append(response)
    return response


def get_opponent_response(debate_messages):
    response = client.chat.completions.create(
        model=opponent_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": f"You are {opponent_name}. You are debating as an opponent of {topic}. Your response should be a json object with the keys 'speaker' and 'content'",
            },
            {
                "role": "user",
                "content": json.dumps(debate_messages),
            },
        ],
    )

    response = json.loads(response.choices[0].message.content)

    debate_messages.append(response)

    return response

def debate_round(debate_messages, moderator_instruction=""):
    moderator_response = get_moderator_response(debate_messages, instruction=moderator_instruction)
    proponent_response = get_proponent_response(debate_messages)
    moderator_response = get_moderator_response(debate_messages)
    opponent_response = get_opponent_response(debate_messages)
    return debate_messages

# Moderator starts the debate and asks for opening statements
debate_messages = debate_round(debate_messages, moderator_instruction=f"Moderator, please introduce the debate on {topic}. Ask {proponent_name} and {opponent_name} for their opening statements.")

# Moderator facilitates cross-examination
debate_messages = debate_round(debate_messages, moderator_instruction=f"Moderator, now facilitate a cross-examination round. First, allow {proponent_name} to question {opponent_name}, then vice versa.")

# Moderator requests closing statements
debate_messages = debate_round(debate_messages, moderator_instruction=f"Moderator, please ask {opponent_name} and {proponent_name} for their closing statements, concluding the debate on {topic}.")

# Moderator gives closing remarks
response = get_moderator_response(debate_messages, instruction=f"Moderator, please give your closing remarks and formally conclude the debate on {topic}.")

# print the debate messages
print(json.dumps(debate_messages, indent=1))

# make transcripts directory if it doesn't exist
if not os.path.exists("transcripts"):
    os.makedirs("transcripts")

topic_slug = slugify.slugify(topic)

# write the transcript to a file
with open(f"transcripts/{proponent_name}-{opponent_name}-{topic_slug}.json", "w") as f:
    json.dump(debate_messages, f, indent=1)

if not os.path.exists("audio"):
    os.makedirs("audio")

if not os.path.exists(f"audio/{topic_slug}"):
    os.makedirs(f"audio/{topic_slug}")

for i, message in enumerate(debate_messages):
    # valid voice names are alloy, echo, fable, onyx, nova, and shimmer
    if message["speaker"] == "moderator":
        voice = "alloy"
    elif message["speaker"] == proponent_name:
        voice = "echo"
    elif message["speaker"] == opponent_name:
        voice = "fable"
    else:
        voice = "alloy"
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=message["content"],
    )
    speech_file_path = Path(f"audio/{topic_slug}/{i}.mp3")
    response.stream_to_file(speech_file_path)

# create image directory if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")
if not os.path.exists(f"images/{topic_slug}"):
    os.makedirs(f"images/{topic_slug}")

# iterate through the conversation and create an image for each message.

for i, message in enumerate(debate_messages):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Image of {message['speaker']} saying: {message['content']}",
            size="1792x1024",
            quality="standard",
            style="natural",
            n=1,
        )
    except:
        print("Image generation failed.")
        continue
    image_url = response.data[0].url
    image = requests.get(image_url)
    with open(f"images/{topic_slug}/{i}.jpg", "wb") as f:
        f.write(image.content)