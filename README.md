# Generative AI Content Mill

This is an experiment to see if we can generate youtube videos using GPT-3.5, GPT-4, DALL-E 3, and OpenAI Text to Speech.

The answer is yes we can. Whether it's good or not is another question.

## How it works

1. We start debater.py and provide a topic, along with the names of the "people" who will be debating.
2. We use OpenAI Chat Completions API to generate a debate.
3. We use OpenAI Text to Speech API to generate audio for the debate.
4. We use OpenAI DALL-E 3 to generate images for each audio clip.
5. We use moviepy to combine the audio and images into a video.
6. After this, the video can be manually uploaded to youtube. This part will be automated later.

## How to use

1. Install dependencies: openai, moviepy, etc... I will make a requirements.txt file later.
2. Create a .env file with your OpenAI API key.
3. Run debater.py and answer the prompts
