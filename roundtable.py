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
import random
from itertools import cycle

# Roundtable discussion with AI generated images and TTS voiceover

# Load environment variables
dotenv.load_dotenv()

# set up the openai client

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Define a generic function to get json from GPT-4
def get_json_list_from_gpt4(prompt, temperature="1.0"):
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
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
        self.participants=[]

    def get_system_message(self):
        return f"You are {self.name}. You are participating in a roundtable discussion as a {self.role} on the topic of {self.topic}. Your response should be a json object with the keys 'speaker', 'content', 'next_speaker', and 'image_description'. The speaker should be your name. next_speaker should be the name of the person who should speak next. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works in image_description."

    def get_response(self, messages, instruction=""):
        response = openai_client.chat.completions.create(
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
        print(json.dumps(response, indent=4, ensure_ascii=False))
        return response


class Moderator(RoundtableParticipant):
    # The moderator should be a subclass of the roundtable participant
    # The moderator should have a special system message
    # The name of the moderator should be "Moderator"
    # The model will be gpt-4-turbo-preview
    # The temperature will be 1.0
    def __init__(self, topic, participants):
        super().__init__(model="gpt-4-turbo-preview", name="Moderator", role="Moderator", topic=topic, temperature="1.0")
        self.participants = participants

    def get_system_message(self):
        return f"You are the moderator. You are moderating a roundtable discussion on the topic of {self.topic}. The participants are {self.participants}. Your response should be a json object with the keys 'speaker', 'content', 'next_speaker', and 'image_description'. The speaker should be your name. next_speaker should be the name of the person you have decided should speak next. When you have decided the roundtable discussion is over, next_speaker should be 'End'. Each speaker will get to decide who speaks next. When you 'open the floor', next_speaker should still be the name of a participant. Only use 'End' when you are closing the debate. Feel free to carry on for multiple rounds until you feel the topic has been covered sufficiently. When you close out the debate, ask viewers to comment, like, and subscribe. Close out with a reminder that this roundtable discussion was entirely AI generated. The only human input was the topic. The content should be your response. The image_description should be a description of an image to accompany your statement. The image should be related to the topic of the roundtable discussion. Avoid using images of the roundtable discussion setting or the participants. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted in image_description. Do not use the names of any copyrighted works. Kick off each round by asking a question."


class RoundtableDiscussion:
    def __init__(self):
        self.topic = self.prompt_user_for_topic()
        self.participants = self.prompt_user_for_participants()
        self.moderator = Moderator(
            topic=self.topic, participants=self.get_participants_list()
        )
        self.messages = []
        self.roundtable_dir = Path("roundtable")
        self.roundtable_discussion_dir = self.roundtable_dir / f"{slugify.slugify(self.topic)}-{uuid.uuid4()}"
        # Create the roundtable discussion directory if it doesn't exist
        self.create_directory(self.roundtable_discussion_dir)

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
            prompt=f"Make a list of roles that people might have in a roundtable discussion on {self.topic}. use the key 'roles' for the list. Do not include the moderator. Include roles that represent a wide range of opinions, including positive and dissenting voices. Include some silly roles just for fun. Make the list as long as it needs to be."
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
                    choices=["gpt-3.5-turbo-1106", "gpt-4-turbo-preview"],
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


    def get_next_speaker(self, current_speaker, messages):
        """
        Determine the next speaker based on the current speaker's response.
        If the current speaker is the moderator, handle special logic.
        """
        if current_speaker == "Moderator":
            # Handle moderator-specific logic
            message = self.moderator.get_response(messages)
            self.messages.append(message)
            return message["next_speaker"]

        # Handle participant logic
        for participant in self.participants:
            if participant.name == current_speaker:
                message = participant.get_response(messages)
                self.messages.append(message)
                return message["next_speaker"]

        # Fallback in case of unexpected speaker name
        return "Moderator"

    def get_participants_list(self):
        participants_list = []
        # each item of the list should have the keys name and role
        for participant in self.participants:
            participant_dict = {}
            participant_dict["name"] = participant.name
            participant_dict["role"] = participant.role
            participants_list.append(participant_dict)
        return participants_list

    def get_participant_names(self):
        participant_names = ["Moderator"]
        for participant in self.participants:
            participant_names.append(participant.name)
        return participant_names

    def create_directory(self, directory_path):
        """
        Create a directory if it doesn't exist.
        """
        directory_path.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, transcript, file_path):
        """
        Save the roundtable discussion transcript to a file.
        """
        with open(file_path, 'w') as file:
            json.dump(transcript, file, indent=4, ensure_ascii=False)


    def conduct_roundtable_discussion(self):
        """
        Conduct the roundtable discussion with participants and moderator.
        """
        next_speaker = "Moderator"
        start_of_discussion = True
        participant_names = self.get_participant_names()

        while next_speaker != "End":
            if start_of_discussion:
                # Special handling for the start of the discussion
                message = self.moderator.get_response(
                    self.messages,
                    instruction="Introduce the roundtable discussion. Introduce all of the participants. Kick off the conversation by asking a question directed towards one of the participants."
                )
                self.messages.append(message)
                next_speaker = message["next_speaker"]
                start_of_discussion = False
            elif next_speaker in participant_names:
                next_speaker = self.get_next_speaker(next_speaker, self.messages)
            else:
                # If next speaker is not found, select a random participant
                next_speaker = random.choice(participant_names)
        # End of discussion
        # save the transcript
        self.save_transcript(self.messages, self.roundtable_discussion_dir / "transcript.json")


def generate_image(openai_client, description, directory, image_number, image_size="1024x1024"):
    """
    Generate an image using the DALL-E model and save it to a specified directory.

    :param openai_client: The OpenAI client object.
    :param description: The description to generate the image.
    :param directory: The directory where the image will be saved.
    :param image_number: The sequential number of the image for file naming.
    :param image_size: The size of the image. Defaults to "1024x1024".
    :return: None
    """
    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=description,
            size=image_size,
            quality="standard",
            style="vivid",
            n=1,
        )
        image_url = response.data[0].url
        image_content = requests.get(image_url).content
        with open(f"{directory}/{image_number:03}.png", "wb") as f:
            f.write(image_content)
    except Exception as e:
        print(f"Image generation failed: {e}")

def generate_voice_clip(openai_client, speaker, voice, content, output_directory, clip_number):
    """
    Generate a voice clip using the specified voice and save it to the specified directory.

    :param openai_client: The OpenAI client object.
    :param speaker: The name of the speaker.
    :param voice: The voice to be used for text-to-speech.
    :param content: The content to be converted into speech.
    :param output_directory: The directory where the voice clip will be saved.
    :param clip_number: The sequential number of the clip for file naming.
    :return: None
    """
    try:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=content,
        )
        # Save the audio to a file in the specified directory
        speech_file_path = Path(output_directory, f"{clip_number:03}_{speaker}.mp3")
        response.stream_to_file(speech_file_path)
    except Exception as e:
        print(f"Voice clip generation failed for {speaker}: {e}")


roundtable = RoundtableDiscussion()
roundtable.conduct_roundtable_discussion()
roundtable_discussion_dir = roundtable.roundtable_discussion_dir

# Choose a unique voice for each participant
# valid voice names are alloy, echo, fable, onyx, nova, and shimmer

participants_list = roundtable.get_participants_list()
# make a list of participant names
participant_names = ["Moderator"] + [participant["name"] for participant in participants_list]

voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

voice_cycle = cycle(voices)

# Assign a voice to each participant using the cycling iterator
participant_voices = {name: next(voice_cycle) for name in participant_names}

# Generate a voice clip for each message

for i, message in enumerate(roundtable.messages):
    speaker = message["speaker"]
    voice = participant_voices[speaker]
    content = message["content"]
    generate_voice_clip(openai_client, speaker, voice, content, roundtable_discussion_dir, i)


# iterate through the conversation and create an image for each message.

for i, message in enumerate(roundtable.messages):
    image_description = message["image_description"]
    print(image_description)
    generate_image(openai_client, image_description, roundtable_discussion_dir, i)

# Create a video from the images and audio
video_output_path = f"{roundtable_discussion_dir}/roundtable.mp4"
create_video_from_clips(roundtable_discussion_dir, video_output_path)
