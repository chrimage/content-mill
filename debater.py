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
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from abc import ABC, abstractmethod

# Load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

image_size = "1024x1024"

class DebateParticipant(ABC):
    def __init__(self, model, name, role, topic, temperature="1.0"):
        self.name = name
        self.model = model
        self.role = role
        self.topic = topic
        self.temperature = temperature

    def get_system_message(self):
        return f"You are {self.name}. You are debating as a {self.role} of {self.topic}. Your response should be a json object with the keys 'speaker', 'content', and 'image_description'. The speaker should be your name. The content should be your response. The image_description should be a description of an image to accompany your statement. Avoid using images of the debate setting or the debaters. Avoid using images of celebrities or public figures. Our text to image system uses a content filter, so avoid anything inappropriate. Avoid anything offensive. Avoid directly mentioning anything that is copyrighted."

    def get_response(self, debate_messages, instruction=""):
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
                    "content": json.dumps(debate_messages, ensure_ascii=False),
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

class DebateManager:
    def __init__(self, debate_config):
        self.debate_config = debate_config
        self.topic = debate_config["topic"]
        self.participants = self.initialize_participants(debate_config["participants"])
        self.debate_messages = []

    def initialize_participants(self, participants_config):
        participants = {}
        for participant in participants_config:
            role = participant["role"].lower()  # Using role as the key
            participant_obj = DebateParticipant(participant["model"],
                                                participant["name"],
                                                role,
                                                self.topic,
                                                participant.get("temperature", "1.0"))
            participants[role] = participant_obj
        return participants

    def conduct_debate(self):
        for round_info in self.debate_config["rounds"]:
            print(f"\n--- {round_info['name']} ---")
            for step_info in round_info["steps"]:
                if isinstance(step_info, list) and len(step_info) == 2:
                    role, instruction = step_info
                else:
                    role = step_info
                    instruction = ""
                participant = self.participants[role.lower()]
                response = participant.get_response(self.debate_messages, instruction)
                print(f"{response['speaker']}: {response['content']}\n\nimage_description: {response['image_description']}\n\n\n")
        return self.debate_messages

def load_debate_config(file_path):
    with open(file_path, "r") as file:
        debate_config = json.load(file)
    return debate_config

debate_config = load_debate_config("debate_config.json")

# input the debate topic

topic = input("What is the topic of the debate? ")


debate_config["topic"] = topic

# Instantiate DebateManager
debate_manager = DebateManager(debate_config)

# Conduct the debate
debate_messages = debate_manager.conduct_debate()

# create a unique name for the debate
topic_slug = slugify.slugify(topic)
debate_id = str(uuid.uuid4())
debate_folder = f"debates/{topic_slug}-{debate_id}"

# create the debates folder if it doesn't exist
if not os.path.exists("debates"):
    os.makedirs("debates")

# create the debate folder if it doesn't exist
if not os.path.exists(f"{debate_folder}"):
    os.makedirs(f"{debate_folder}")


# Define the file path for the transcript
transcript_file_path = os.path.join(debate_folder, "transcript.json")

# Save the transcript
with open(transcript_file_path, "w") as file:
    json.dump(debate_messages, file, indent=4, ensure_ascii=False)

print(f"Transcript saved to {transcript_file_path}")

# get the names of the speakers

for participant in debate_config["participants"]:
    if participant["role"] == "proponent":
        proponent_name = participant["name"]
    elif participant["role"] == "opponent":
        opponent_name = participant["name"]

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
   # save the audio to a file in the debate folder
   speech_file_path = Path(f"{debate_folder}/{i:03}.mp3")
   response.stream_to_file(speech_file_path)
#
## iterate through the conversation and create an image for each message.

for i, message in enumerate(debate_messages):
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
    with open(f"{debate_folder}/{i:03}.png", "wb") as f:
        f.write(image.content)

# start creating a video from the images and audio files


directory = debate_folder

# get all png files in the directory

png_files = list(pathlib.Path(directory).glob("*.png"))

# get all mp3 files in the directory

mp3_files = list(pathlib.Path(directory).glob("*.mp3"))

print(f"{mp3_files}\n\n{png_files}")

# sort the files by name

png_files.sort()
mp3_files.sort()

# create a list of clips

clips = []

# for example, 0.png and 0.mp3 should be combined into a video clip.
# the video clip should match the duration of the mp3 file.

for i in range(len(png_files)):
    png_file = str(png_files[i])
    mp3_file = str(mp3_files[i])
    print(f"Processing {png_file} and {mp3_file}")
    png_clip = ImageClip(png_file)
    mp3_clip = AudioFileClip(mp3_file)
    png_clip = png_clip.set_duration(mp3_clip.duration)
    png_clip = png_clip.set_audio(
        mp3_clip
    )  # Set the audio of the png_clip to be the mp3_clip
    clips.append(png_clip)

# concatenate the clips
final_clip = concatenate_videoclips(clips)

# write the final clip to a file

final_clip.write_videofile(f"{directory}/final_clip.mp4", fps=24)

# close the final clip

final_clip.close()
