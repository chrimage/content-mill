from typing import Any
from openai import OpenAI
from pathlib import Path
import os
import sys
import json
import dotenv
import slugify
import requests
import uuid
import pathlib
from video_utils import create_video_from_clips
from abc import ABC
import inquirer

# Roundtable discussion with AI generated images and TTS voiceover

# Load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Define a generic function to get json from GPT-4
def get_json_list_from_gpt4(prompt, temperature="1.0"):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Your response should be a json list of strings.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    response = json.loads(response.choices[0].message.content)

    return response


# Define a class for the roundtable discussion


class RoundtableParticipant:
    def __init__(self, model, name, role, topic, temperature="1.0"):
        self.name = name
        self.model = model
        self.role = role
        self.topic = topic
        self.temperature = temperature
        self.system_message = self.get_system_message()

    def get_system_message(self):
        return f"You are {self.name}. You are participating in a roundtable discussion as a {self.role} on the topic of {self.topic}. Your response should be a json object with the keys 'speaker', 'content', 'next_speaker', and 'image_description'. The speaker should be your name. next_speaker should be the name of the person who should speak next. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works in image_description."

    def get_response(self, messages, instruction=""):
        response = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": self.get_system_message(),
                },
                {
                    "role": "user",
                    "content": json.dumps(messages, ensure_ascii=False),
                },
                {
                    "role": "user",
                    "content": instruction,
                }
            ],
        )

        response = json.loads(response.choices[0].message.content)
        print(json.dumps(response, indent=4, ensure_ascii=False))
        return response


class Moderator(RoundtableParticipant):
    # The moderator should be a subclass of the roundtable participant
    # The moderator should have a special system message
    # The name of the moderator should be "Moderator"
    # The model will be gpt-4-1106-preview
    # The temperature will be 1.0
    def __init__(self, topic, participants):
        self.name = "Moderator"
        self.model = "gpt-4-1106-preview"
        self.role = "Moderator"
        self.topic = topic
        self.participants = participants
        self.temperature = "1.0"
        self.system_message = self.get_system_message()

    def get_system_message(self):
        return f"You are the moderator. You are moderating a roundtable discussion on the topic of {self.topic}. The participants are {self.participants}. Your response should be a json object with the keys 'speaker', 'content', 'next_speaker', and 'image_description'. The speaker should be your name. next_speaker should be the name of the person you have decided should speak next. When you have decided the roundtable discussion is over, next_speaker should be 'End'. Each speaker will get to decide who speaks next. When you 'open the floor', you still have to pick a next_speaker. Only use 'End' when you are closing the debate. Feel free to carry on for multiple rounds until you feel the topic has been covered sufficiently. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works."

class RoundtableDiscussion:
    def __init__(self):
        self.topic = self.prompt_user_for_topic()
        self.participants = self.prompt_user_for_participants()
        self.moderator = Moderator(topic=self.topic, participants=self.get_participants_list())
        self.messages = []

    def add_participant(self, participant):
        self.participants.append(participant)

    def prompt_user_for_topic(self):
        topic = input("What topic should the AI make a roundtable discussion about?")
        return topic

    def prompt_user_for_participants(self):
        num_participants = input(
            "How many participants should the roundtable discussion have?"
        )
        num_participants = int(num_participants)
        participants = []
        name_choices = get_json_list_from_gpt4(
            prompt=f"Make a list of gender neutral names of people who might participate in a roundtable discussion on {self.topic}. use the key 'names' for the list."
        )
        name_choices = name_choices["names"]
        role_choices = get_json_list_from_gpt4(
            prompt=f"Make a list of roles that people might have in a roundtable discussion on {self.topic}. use the key 'roles' for the list. Do not include the moderator."
        )
        role_choices = role_choices["roles"]
        for i in range(num_participants):
            questions = [
                inquirer.List(
                    "name",
                    message=f"Choose a name for participant {i+1}",
                    choices=name_choices,
                ),
                inquirer.List(
                    "role",
                    message=f"Choose a role for participant {i+1}",
                    choices=role_choices,
                ),
                inquirer.List(
                    "model",
                    message=f"What is the model of participant {i+1}?",
                    choices=["gpt-3.5-turbo-1106", "gpt-4-1106-preview"],
                ),
                inquirer.List(
                    "temperature",
                    message=f"What is the temperature of participant {i+1}?",
                    choices=["0.5", "0.7", "0.9", "1.0", "1.1", "1.3", "1.5"],
                ),
            ]
            answers = inquirer.prompt(questions)
            name = answers["name"]
            # remove the name from the list of choices
            name_choices.remove(name)
            role = answers["role"]
            # remove the role from the list of choices
            role_choices.remove(role)
            model = answers["model"]
            temperature = answers["temperature"]
            topic = self.topic
            participant = RoundtableParticipant(model, name, role, topic, temperature)
            participants.append(participant)
        return participants

    def get_participants_list(self):
        participants_list = []
        # each item of the list should have the keys name and role
        for participant in self.participants:
            participant_dict = {}
            participant_dict["name"] = participant.name
            participant_dict["role"] = participant.role
            participants_list.append(participant_dict)
        return participants_list

    def conduct_roundtable_discussion(self):
        # Conduct the roundtable discussion
        # The moderator should start the discussion
        messages = self.messages
        next_speaker = "Moderator"
        start_of_discussion = True
        while next_speaker != "End":
            if next_speaker == "Moderator":
                # The moderator should speak
                if start_of_discussion:
                    message = self.moderator.get_response(messages, instruction="Introduce the roundtable discussion. Introduce all of the participants. Kick off the conversation by asking a question directed towards one of the participants.")
                    messages.append(message)
                    next_speaker = message["next_speaker"]
                    start_of_discussion = False
                else:
                    message = self.moderator.get_response(messages)
                    messages.append(message)
                    next_speaker = message["next_speaker"]
            else:
                # A participant should speak
                for participant in self.participants:
                    if participant.name == next_speaker:
                        message = participant.get_response(messages)
                        messages.append(message)
                        next_speaker = message["next_speaker"]
                        break


roundtable = RoundtableDiscussion()
roundtable.conduct_roundtable_discussion()

# Create the roundtable directory if it doesn't exist
roundtable_dir = Path("roundtable")
if not roundtable_dir.exists():
    roundtable_dir.mkdir()

# Create a directory for the roundtable discussion
roundtable_discussion_dir = f"roundtable/{slugify.slugify(roundtable.topic)}-{uuid.uuid4()}"

# Create the roundtable discussion directory if it doesn't exist
if not os.path.exists(roundtable_discussion_dir):
    os.mkdir(roundtable_discussion_dir)

# Save the roundtable discussion transcript
transcript_file_path = os.path.join(roundtable_discussion_dir, "transcript.json")

# Choose a unique voice for each participant
# valid voice names are alloy, echo, fable, onyx, nova, and shimmer

participants_list = roundtable.get_participants_list()
# make a list of participant names
participant_names = ["Moderator"]
for participant in participants_list:
    participant_names.append(participant["name"])

voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# assign a voice to each participant
participant_voices = {}
for participant_name in participant_names:
    voice = voices.pop()
    participant_voices[participant_name] = voice

# Create voice clips for the messages, numbered sequentially
for i, message in enumerate(roundtable.messages):
    # get the voice for the speaker
    voice = participant_voices[message["speaker"]]
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=message["content"],
    )
    # save the audio to a file in the debate folder
    speech_file_path = Path(f"{roundtable_discussion_dir}/{i:03}.mp3")
    response.stream_to_file(speech_file_path)

## iterate through the conversation and create an image for each message.

image_size="1024x1024"

for i, message in enumerate(roundtable.messages):
    image_description = message["image_description"]
    print(image_description)
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"{image_description}",
            size=image_size,
            quality="standard",
            style="vivid",
            n=1,
        )
    except:
        print("Image generation failed.")
        continue
    image_url = response.data[0].url
    image = requests.get(image_url)
    with open(f"{roundtable_discussion_dir}/{i:03}.png", "wb") as f:
        f.write(image.content)

# Create a video from the images and audio
video_output_path = f"{roundtable_discussion_dir}/roundtable.mp4"
create_video_from_clips(roundtable_discussion_dir, video_output_path)