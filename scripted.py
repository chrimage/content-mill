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

# prompt the AI for a revised script

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": f"You will be provided with a draft script for a YouTube video. Transform the script into a structured json output with the keys 'title' and 'script'. 'script' should be a list of objects with the keys 'voiceover' and 'image_description', where voiceover is the revised script, and image_description is a description of an image to accompany the voiceover. Stay true to the spirit of the original draft. The goal is to accompany each section of voiceover with a unique image related to the voiceover. Editor instructions are inside triple braces.",
        },
        {
            "role": "user",
            "content": f"Write a revised version of this script:\n\n {draft_script}",
        },
    ],
)

revised_script = response.choices[0].message.content

final_script = json.loads(revised_script)

title = final_script["title"]

# print the title

print(f"Title: {title}")

final_script = final_script["script"]

print(json.dumps(final_script, indent=4, ensure_ascii=False))

# prompt the user to confirm the script

response = input("Does this script look good? (y/n) ")

if response != "y":
    print("Exiting...")
    sys.exit(1)

# ensure the scripted_videos folder exists

if not os.path.exists("scripted_videos"):
    os.makedirs("scripted_videos")

# generate a uuid for this video

video_uuid = uuid.uuid4()

# slugify the title

title_slug = slugify.slugify(title)

# create a folder for this video

video_dir = f"scripted_videos/{title_slug}-{video_uuid}"

os.makedirs(video_dir)

# save the script to a file 

with open(f"{video_dir}/script.json", "w") as f:
    json.dump(final_script, f, indent=4, ensure_ascii=False)

voiceovers = [item["voiceover"] for item in final_script]

voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

for i, voiceover in enumerate(voiceovers):
    # print status message
    print(f"Processing voiceover {i} of {len(voiceovers)}")
    # print the voiceover
    print(voiceover)
    # valid voice names are alloy, echo, fable, onyx, nova, and shimmer
    # choose a random voice
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=voiceover,
    )
    voiceover_path = Path(f"{video_dir}/{i:03}.mp3")
    response.stream_to_file(voiceover_path)

# get list of image descriptions

image_descriptions = [item["image_description"] for item in final_script]

for i, image_description in enumerate(image_descriptions):
    # print status message
    print(f"Processing image {i} of {len(image_descriptions)}")
    # print the image description
    print(image_description)
    response = client.images.generate(
        model="dall-e-3",
        prompt=image_description,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    image = requests.get(image_url).content
    # save the image to a file
    with open(f"{video_dir}/{i:03}.png", "wb") as handler:
        handler.write(image)

# start creating a video from the images and audio files

output_video_path = f"{video_dir}/final_video.mp4"
create_video_from_clips(video_dir, output_video_path)