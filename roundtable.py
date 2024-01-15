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
            }
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
        return f"You are {self.name}. You are participating in a roundtable discussion as a {self.role} on the topic of {self.topic}. Your response should be a json object with the keys 'speaker', 'content', and 'image_description'. The speaker should be your name. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works in image_description."

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
                },
            ],
        )

        response = json.loads(response.choices[0].message.content)

        messages.append(response)

        return response

class Moderator(RoundtableParticipant):
    def __init__(self, model, name, role, topic, participants, temperature="1.0"):
        super().__init__(model, name, role, topic, temperature)
        self.model = model
        self.name = "Moderator"
        self.topic = topic
        self.system_message = self.get_system_message()
        self.participants = participants

    def get_system_message(self):
        return f"You are the moderator. You are moderating a roundtable discussion on the topic of {self.topic}. Your response should be a json object with the keys 'speaker', 'content', and 'image_description'. The speaker should be your name. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works."

class RoundtableDiscussion:
    def __init__(self, participants=None):
        self.topic = self.prompt_user_for_topic()
        self.participants = self.prompt_user_for_participants()

    def add_participant(self, participant):
        self.participants.append(participant)

    def prompt_user_for_topic(self):
        topic = input("What topic should the AI make a roundtable discussion about?")
        return topic

    def prompt_user_for_participants(self):
        num_participants = input("How many participants should the roundtable discussion have?")
        num_participants = int(num_participants)
        participants = []
        name_choices = get_json_list_from_gpt4(prompt=f"Make a list of gender neutral names of people who might participate in a roundtable discussion on {self.topic}. use the key 'names' for the list.")
        name_choices = name_choices['names']
        role_choices = get_json_list_from_gpt4(prompt=f"Make a list of roles that people might have in a roundtable discussion on {self.topic}. use the key 'roles' for the list.")
        role_choices = role_choices['roles']
        for i in range(num_participants):
            questions = [
                inquirer.List('name',
                              message=f"Choose a name for participant {i+1}",
                              choices=name_choices,
                              ),
                inquirer.List('role',
                              message=f"Choose a role for participant {i+1}",
                              choices=role_choices,
                              ),
                inquirer.List('model',
                              message=f"What is the model of participant {i+1}?",
                              choices=['gpt-3.5-turbo-1106', 'gpt-4-1106-preview'],
                ),
                inquirer.List('temperature',
                              message=f"What is the temperature of participant {i+1}?",
                              choices=['0.5', '0.7', '0.9', '1.0', '1.1', '1.3', '1.5'],
                ),
            ]
            answers = inquirer.prompt(questions)
            name = answers['name']
            # remove the name from the list of choices
            name_choices.remove(name)
            role = answers['role']
            # remove the role from the list of choices
            role_choices.remove(role)
            model = answers['model']
            temperature = answers['temperature']
            topic = self.topic
            participant = RoundtableParticipant(model, name, role, topic, temperature)
            participants.append(participant)
        return participants

    def get_participants_list(self):
        participants_list = []
        # each item of the list should have the keys name and role
        for participant in self.participants:
            participant_dict = {}
            participant_dict['name'] = participant.name
            participant_dict['role'] = participant.role
            participants_list.append(participant_dict)
        return participants_list

roundtable = RoundtableDiscussion()
participants_list = roundtable.get_participants_list()
print(participants_list)