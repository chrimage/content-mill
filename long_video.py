from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from folder_utils import OutputFolder
from openai_utils import generate_image, generate_voice_clip
from video_utils import create_video_from_clips

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OUTLINER_MODEL = "gpt-4-turbo-preview"

OUTLINER_SYSTEM_MESSAGE = """Your job is to write outlines for YouTube videos.
The outline should be a json object. The top level keys are 'title' and 'sections'.
The 'sections' key should have a list of objects. Each object should have a 'title' and 'description' key.
If there are subsections, the object should have a 'title' and 'items' key.
The 'items' key should have a list of objects with a 'title' and 'description' key."""

SECTION_MODEL = "gpt-4-turbo-preview"

SECTION_SYSTEM_MESSAGE = """Your job is to write a script for a section of a YouTube video.
Each section of voiceover should be accompanied by a single image.
Optimize the script for SEO and engagement.
Your response should be in json as a list of objects. The list key is 'section'.
Each object in 'section' should have the keys 'voiceover' and 'image_description'.
Do not use phrases like "in conclusion" until you are writing the closing section of the video."""

def get_outline(topic):
    response = client.chat.completions.create(
        model=OUTLINER_MODEL,
        messages=[
            {
                "role": "system",
                "content": OUTLINER_SYSTEM_MESSAGE,
            },
            {
                "role": "user",
                "content": f"I am creating a video about {topic}.",
            },
        ],
        response_format={"type": "json_object"},
    )
    outline = response.choices[0].message.content
    outline = json.loads(outline)
    return outline


def get_section_script(video_title, script, section):
    response = client.chat.completions.create(
        model=SECTION_MODEL,
        messages=[
            {
                "role": "system",
                "content": SECTION_SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": f"""Video Title: {video_title}\n\nHere's the script so far: {json.dumps(script,ensure_ascii=False)}\n\nThe next Section to write is: {json.dumps(section,ensure_ascii=False)}""",
            },
        ],
        response_format={"type": "json_object"},
    )
    section_script = response.choices[0].message.content
    section_script = json.loads(section_script)
    section_script = section_script["section"]
    return section_script


def flatten_outline(outline):
    flat_outline = []
    for section in outline["sections"]:
        if "items" in section:
            for item in section["items"]:
                title = f"{section['title']} - {item['title']}"
                description = item["description"]
                flat_outline.append({"title": title, "description": description})
        else:
            flat_outline.append(section)
    return flat_outline


def process_outline(outline):
    video_title = outline["title"]
    flat_outline = flatten_outline(outline)
    script = []
    for section in flat_outline:
        print(section["title"])
        section_script = get_section_script(video_title, script, section)
        print(json.dumps(section_script, indent=2, ensure_ascii=False))
        script.extend(section_script)
    return script


# Prompt the user for a topic
video_topic = input("What is the topic of your video? ")

# Generate the outline
outline = get_outline(video_topic)

# Print the outline
print(json.dumps(outline, indent=2, ensure_ascii=False))

# Process the outline into a script
script = process_outline(outline)

# Save the script
output_folder = OutputFolder("long_videos", outline["title"])
with open(output_folder.path / "script.json", "w") as f:
    json.dump(script, f, indent=2, ensure_ascii=False)

# Generate the images and voiceovers
for i, segment in enumerate(script):
    image_description = segment["image_description"]
    generate_image(image_description, "1024x1024", output_folder.path, f"{i:03}.png")
    voiceover = segment["voiceover"]
    generate_voice_clip(voiceover, "alloy", output_folder.path, f"{i:03}.mp3")

# Create the video
video_path = f"{output_folder.path}/video.mp4"
create_video_from_clips(output_folder.path, video_path)
print(f"Video created at {video_path}")
