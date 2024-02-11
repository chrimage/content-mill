from openai import OpenAI
from dotenv import load_dotenv
from textwrap import dedent
import os
import json
import requests
from pathlib import Path
load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_json_video_script(script):
    script = dedent(script)
    system_message=f"""
    You will be provided with the script for a YouTube video.
    Transform the script into a structured json output with the keys 'title' and 'script'.
    'script' should be a list of objects with the keys 'voiceover' and 'image_description'.
    The goal is to accompany each section of voiceover with a unique image related to the voiceover.
    The final result is a video with voiceover and images.
    Guidelines for image descriptions:
    - The description should be detailed.
    - The description should be self contained.
    - The image description should never refer to other image descriptions. The image descriptions are provided individually to a text to image generator.
    - Do not refer to other sections of the script. The image generator does not have access to the script.
    - The image description should be at least 100 words long.
    - Avoid images of 'The Host', 'The YouTuber', 'The Narrator', or 'The AI'. There is no character associated with the video, as it is AI generated.
    Remember, you are part of a "Text to Video" pipeline. Your output will be fed into a text to speech generator and a text to image generator.
    """
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": dedent(system_message),
            },
            {
                "role": "user",
                "content": f"{script}",
            },
        ],
    )
    revised_script = response.choices[0].message.content
    revised_script = json.loads(revised_script)
    return revised_script

def generate_voice_clip(input, voice, output_folder, filename):
    speech_file_path = output_folder / filename
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=input
    ) as response:
        response.stream_to_file(speech_file_path)


def generate_image(prompt, size, output_folder, filename):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    image = requests.get(image_url)

    # save the image
    with open(output_folder / filename, "wb") as f:
        f.write(image.content)
