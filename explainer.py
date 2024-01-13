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

# We're going to use OpenAI Chat Completions API to make a explainer video.

# Prompt the user for the topic

topic = input("What topic should the AI make a explainer about?")

# prompt the AI for explainer script in json format

response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": f"Your task is to write a script for an explainer video. Represent the script for an explainer video in json format. The video will be a slideshow with AI generated images, and TTS voiceover. Be sure to include interesting facts throughout the video. Be as thorough as possible. Use the keys title and script. script is a list of objects, each with the key 'image_description' and 'voiceover'. Each voiceover section should be about 150 words in length. The goal is to accompany each section of voiceover with a unique image related to the voiceover. The video should be suitable for audiences of all ages. Close out the video by thanking the viewer for watching, asking them to like the video, and asking them to subscribe to our channel.",
        },
        {
            "role": "user",
            "content": f"Write an explainer video about {topic}.",
        },
    ],
)

script = response.choices[0].message.content

script = json.loads(script)

# print the explainer script

# print(json.dumps(script, indent=4))

title = script["title"]

print(f"Title: {title}")

title_slug = slugify.slugify(title)

# create the explainers folder if it doesn't exist

if not os.path.exists("explainers"):
    os.makedirs("explainers")

# create a folder for thisexplainer 

explainer_dir = f"explainers/{title_slug}-{uuid.uuid4()}"
os.makedirs(explainer_dir)

# save the explainer script to a file

with open(f"{explainer_dir}/script.json", "w") as f:
    json.dump(script, f, indent=4)

script = script["script"]

# get list of voiceovers

voiceovers = [item["voiceover"] for item in script]

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
    voiceover_path = Path(f"{explainer_dir}/{i:03}.mp3")
    response.stream_to_file(voiceover_path)


# get list of image descriptions

image_descriptions = [item["image_description"] for item in script]

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
    with open(f"{explainer_dir}/{i:03}.png", "wb") as handler:
        handler.write(image)

# start creating a video from the images and audio files

output_video_path = f"{explainer_dir}/final_video.mp4"
create_video_from_clips(explainer_dir, output_video_path)