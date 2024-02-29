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

OUTLINER_SYSTEM_MESSAGE = """Your job is to write an outline for a YouTube video based on the topic provided by the user..
Include a reminder that the script, voiceover, and images for this video are entirely AI generated.
Include a reminder that the AI generated images are not factually accurate.
The video should be 10-15 minutes long.
Optimize the outline content for SEO and engagement.
Include a call to action section at the end of the video, reminding viewers to like, comment, and subscribe.
The outline should be a json object. The top level keys are 'title' and 'sections'.
The 'sections' key should have a list of objects. Each object should have a 'title' and 'writing_prompt' key.
If there are subsections, the object should have a 'title' and 'items' key.
The 'items' key should have a list of objects with a 'title' and 'writing_prompt' key.
'title' is the title of the section. 'writing_prompt' should be a writing prompt for the section."""


SECTION_MODEL = "gpt-4-turbo-preview"

SECTION_SYSTEM_MESSAGE = """Your job is to write a script for a portion of a YouTube video.
Each section of voiceover should be accompanied by a single image.
Optimize the script for SEO and engagement.
Your response should be a json list with the key 'section'.
Each object in 'section' should have the keys 'voiceover' and 'image_description'.
'voiceover' should be the voiceover for the section. 'image_description' should be a description of the image for the section.
Do not wrap up the video unless the section is titled 'Conclusion' or 'Outro'."""


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
                "content": f"Write an outline for a video about '{topic}'.",
            },
        ],
        response_format={"type": "json_object"},
        temperature=1.1,
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
        temperature=0.7,
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
                writing_prompt = item["writing_prompt"]
                flat_outline.append({"title": title, "writing_prompt": writing_prompt})
        else:
            flat_outline.append(section)
    return flat_outline


def process_outline(outline):
    video_title = outline["title"]
    flat_outline = flatten_outline(outline)
    script = []
    for section in flat_outline:
        print(f"title: {section['title']}\nwriting_prompt: {section['writing_prompt']}")
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

# Save the outline
output_folder = OutputFolder("long_videos", outline["title"])
with open(output_folder.path / "outline.json", "w") as f:
    json.dump(outline, f, indent=2, ensure_ascii=False)

# Process the outline into a script
script = process_outline(outline)

# Save the script
with open(output_folder.path / "script.json", "w") as f:
    json.dump(script, f, indent=2, ensure_ascii=False)

# Generate the images and voiceovers
for i, segment in enumerate(script):
    if isinstance(segment, dict):
        image_description = segment.get("image_description")
        if image_description:
            generate_image(image_description, "1024x1024", output_folder.path, f"{i:03}.png")
        voiceover = segment.get("voiceover")
        if voiceover:
            generate_voice_clip(voiceover, "alloy", output_folder.path, f"{i:03}.mp3")
    else:
        print(f"Warning: segment {i} is not a dictionary! Skipping...")
# Create the video
video_path = f"{output_folder.path}/video.mp4"
create_video_from_clips(output_folder.path, video_path)
print(f"Video created at {video_path}")
