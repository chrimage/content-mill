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

# We're going to use OpenAI Chat Completions API to make a listicle video.

# Prompt the user for the topic

topic = input("What topic should the AI make a listicle about?")

# prompt the AI for listicle script in json format

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": f"Your task is to write a script for a listicle video. Represent the script for a listicle video in json format. The video will be a slideshow with AI generated images, and TTS voiceover. Use the keys title and script. script is a list of objects, each with the key 'image_description' and 'voiceover'. The goal is to accompany each section of voiceover with a unique image related to the voiceover. Close out the video by thanking the viewer for watching, asking them to like the video, and asking them to subscribe to our channel.",
        },
        {
            "role": "user",
            "content": f"Write a listicle about {topic}.",
        },
    ],
)

listicle_script = response.choices[0].message.content

listicle_script = json.loads(listicle_script)

# print the listicle script

# print(json.dumps(listicle_script, indent=4))

title = listicle_script["title"]

print(f"Title: {title}")

title_slug = slugify.slugify(title)

# create the listicles folder if it doesn't exist

if not os.path.exists("listicles"):
    os.makedirs("listicles")

# create a folder for this listicle

listicle_dir = f"listicles/{title_slug}-{uuid.uuid4()}"
os.makedirs(listicle_dir)

# save the listicle script to a file

with open(f"{listicle_dir}/listicle_script.json", "w") as f:
    json.dump(listicle_script, f, indent=4)

listicle_script = listicle_script["script"]

# get list of voiceovers

voiceovers = [item["voiceover"] for item in listicle_script]

for i, voiceover in enumerate(voiceovers):
    # print status message
    print(f"Processing voiceover {i} of {len(voiceovers)}")
    # print the voiceover
    print(voiceover)
    # valid voice names are alloy, echo, fable, onyx, nova, and shimmer
    # choose a random voice
    voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=voiceover,
    )
    voiceover_path = Path(f"{listicle_dir}/{i:03}.mp3")
    response.stream_to_file(voiceover_path)


# get list of image descriptions

image_descriptions = [item["image_description"] for item in listicle_script]

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
    with open(f"{listicle_dir}/{i:03}.png", "wb") as handler:
        handler.write(image)

# start creating a video from the images and audio files

output_video_path = f"{listicle_dir}/final_video.mp4"
create_video_from_clips(listicle_dir, output_video_path)