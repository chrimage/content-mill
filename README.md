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
4. Run listicle.py and provide a topic
5. Run explainer.py and provide a topic

## Experiment Results

I started this project with the hypothesis that we could use Generative AI to create videos with minimal human input. Hypothesis confirmed. Most of the videos are poor quality. Some of them are good on accident.

I used three different formats: debate, listicle, and explainer.

### Debate Videos ([Playlist](https://www.youtube.com/playlist?list=PLbNdqC_BkyEBEXRu6a8G2TKucW1xOd6JX))

Debate videos are longer, because of the recursive prompting used to create them. I used system prompts to define "personas" for each character involved in the debate. This worked well and generated semi-interesting debates. However, both sides presented pretty generic arguments. The content of the debates was repetitive. The image generation technique led to videos that were not visually engaging, simply because the images did not change often enough. Additionally, the generated images were not very good. I tried using GPT-4 to enhance the image prompts by feeding it the debate argument and prompting it to generate visuals to accompany the debate argument. This improved the results, but only slightly.

### Listicle Videos ([Playlist](https://www.youtube.com/playlist?list=PLbNdqC_BkyECUDl20HwFkHeuptbZY7R9z))

This format yielded shorter videos that were more visually engaging. I changed the prompting technique slightly. Instead of recursively prompting GPT, I simply asked GPT to generate a json object to represent the script for the video. It created a list of objects with the keys "voiceover" and "image_description". This structure made it easy to generate voiceovers and images for each section of the video. In the prompt for the listicle videos, I asked GPT to close out the video by asking viewers to like and subscribe. It also generated imagery to go along with the like and subscribe call to action.

### Explainer Videos ([Playlist](https://www.youtube.com/playlist?list=PLbNdqC_BkyECUDl20HwFkHeuptbZY7R9z))

The explainer video format used the same techniques employed in the listicle format. I was hoping that changing the prompts slightly would allow GPT-4 to do a deep dive on specific topics. Some of the videos were mildly amusing, but it's becoming clear that these videos are just never going to be remotely good. They might be entertaining to someone who is curious about AI Generated content.

### Conclusion

This project turned out about how I expected. I expected that it would be possible to generate low quality content at a ridiculous rate. GPT-4 is not good at being funny on purpose, but it is often funny on accident. It can be somewhat amusing to see how AI represents various concepts in the form of a video script. DALL-E 3 can create some impressive visuals, but they are often flawed, and generally did not mesh well with the narration. Generative AI is more useful under close human supervision. Generating "good" images with DALL-E 3 often requires multiple attempts. Generating "good" scripts requires starting out with a good idea. The more specifics you provide, the better results you will get. What I wanted to do with this project was give the AI a "seed" of an idea, and let it run with that idea to completion. In conclusion, current state of the art Generative AI (GPT-4) does not create compelling content when left to its own devices. However, it does generally make "coherent" content that follows the prompt it was given.
