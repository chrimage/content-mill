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
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# load environment variables
dotenv.load_dotenv()

# set up the openai client

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# We're going to use OpenAI Chat Completions API to make a haiku video.

# Prompt the user for the topic

topic = input("What topic should the AI make a haiku about?")

# prompt the AI for haiku script in json format

response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": f"Your task is to write a script for an haiku video. Represent the script for an haiku video in json format. The video will be a slideshow with AI generated images, and TTS voiceover. Use the keys title and script. script is a list of objects, each with the key 'image_description' and 'voiceover'. The entire haiku should be a single voiceover with a single image description. Terminate each line of the haiku with a '[pause]' to represent a pause. Provide only the haiku, nothing else. Adhere to the haiku poem format.",
        },
        {
            "role": "user",
            "content": f"Write a haiku video about {topic}.",
        },
    ],
)

script = response.choices[0].message.content

script = json.loads(script)

# print the haiku script

# print(json.dumps(script, indent=4))

title = script["title"]

print(f"Title: {title}")

title_slug = slugify.slugify(title)

# create the haikus folder if it doesn't exist

if not os.path.exists("haikus"):
    os.makedirs("haikus")

# create a folder for thishaiku 

haiku_dir = f"haikus/{title_slug}-{uuid.uuid4()}"
os.makedirs(haiku_dir)

# save the haiku script to a file

with open(f"{haiku_dir}/script.json", "w") as f:
    json.dump(script, f, indent=4)

script = script["script"]

# get list of voiceovers

voiceovers = [item["voiceover"] for item in script]

# choose a random voice
voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

for i, voiceover in enumerate(voiceovers):
    # print status message
    print(f"Processing voiceover {i} of {len(voiceovers)}")
    # print the voiceover
    print(voiceover)
    # valid voice names are alloy, echo, fable, onyx, nova, and shimmer
    # choose a random voice
    voice = voice
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=voiceover,
    )
    voiceover_path = Path(f"{haiku_dir}/{i:03}.mp3")
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
    with open(f"{haiku_dir}/{i:03}.png", "wb") as handler:
        handler.write(image)

# start creating a video from the images and audio files

directory = haiku_dir

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
