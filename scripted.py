from openai import OpenAI
from pathlib import Path
import os
import sys
import json
import dotenv
import slugify
import requests
import uuid
import random
import pathlib
from video_utils import create_video_from_clips
from openai_utils import structure_video_script, generate_voice_clip, generate_image
from folder_utils import OutputFolder

# load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Steps
# 1. input a draft script for a video
# 2. feed the script to the AI, asking for a revised version
# 3. The revised version should be a json object with the keys voiceover and image_description

# expect the first argument to be the path to the draft script

draft_script_path = sys.argv[1]

# read the draft script

with open(draft_script_path) as f:
    draft_script = f.read()

# print the draft script
print(draft_script)

# prompt the AI for a revised script

final_script = structure_video_script(draft_script)

title = final_script["title"]

final_script = final_script["script"]

# print the title

print(f"Title: {title}")

print(json.dumps(final_script, indent=4, ensure_ascii=False))

# prompt the user to confirm the script

response = input("Does this script look good? (y/n) ")

if response != "y":
    print("Exiting...")
    sys.exit(1)

output_folder = OutputFolder("scripted", title)
video_dir = output_folder.path

# save the script to a file 

with open(f"{video_dir}/script.json", "w") as f:
    json.dump(final_script, f, indent=4, ensure_ascii=False)


voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

for i, section in enumerate(final_script):
    voiceover = section["voiceover"]
    print(f"Generating voiceover for section {i}")
    print(voiceover)
    generate_voice_clip(voiceover, voice, video_dir, f'{i:03}.mp3')
    image_description = section["image_description"]
    print(f"Generating image for section {i}")
    print(image_description)
    generate_image(image_description, "1024x1024", video_dir, f'{i:03}.png')

output_video_path = f"{video_dir}/final_video.mp4"
create_video_from_clips(video_dir, output_video_path)