from openai import OpenAI
from dotenv import load_dotenv
from textwrap import dedent
import os
import json
import requests
from pathlib import Path
load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def structure_video_script(script):
    system_message = """Transform the script into a structured json output with the keys 'title' and 'script'.
    Each section of voiceover should be accompanied by a unique image related to the voiceover.
    The final result is a video with voiceover and images.
    Guidelines for image descriptions:
    - The description should be detailed and self-contained.
    - Avoid referring to other image descriptions or sections of the script.
    - Each image description should be at least 100 words long.
    - Avoid images of 'The Host', 'The YouTuber', 'The Narrator', or 'The AI'.
    Remember, you are part of a "Text to Video" pipeline.
    Your output will be fed into a text-to-speech generator and a text-to-image generator."""
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

def generate_image(prompt, size, output_folder, filename, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
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
            return  # Exit the function if the image is successfully generated
        except:
            retries += 1
            if retries < max_retries:
                new_prompt = adjust_prompt(prompt)
                prompt = new_prompt
            else:
                print(f"Failed to generate image after {max_retries} retries. Skipping image generation.")
                return  # Exit the function if the maximum number of retries is reached

def adjust_prompt(prompt):
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": "I will provide you with a prompt that failed to generate an image due to a content policy violation. Your task is to respond with a modified prompt that is less likely to result in a content policy violation."
            },
            {
                "role": "user",
                "content": f"{prompt}",
            },
        ],
    )
    new_prompt = response.choices[0].message.content
    return new_prompt
    