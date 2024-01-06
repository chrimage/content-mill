from moviepy.editor import *
import os
import sys
import pathlib

# input arguments
# user will specify a folder which contains jpg and mp3 files. these will be combined into a video.

directory = sys.argv[1]

# get all jpg files in the directory

jpg_files = list(pathlib.Path(directory).glob("*.jpg"))

# get all mp3 files in the directory

mp3_files = list(pathlib.Path(directory).glob("*.mp3"))

print (f"{mp3_files}\n\n{jpg_files}")

# sort the files by name

jpg_files.sort()
mp3_files.sort()

# create a list of clips

clips = []

# for example, 0.jpg and 0.mp3 should be combined into a video clip.
# the video clip should match the duration of the mp3 file.

for i in range(len(jpg_files)):
    jpg_file = str(jpg_files[i])
    mp3_file = str(mp3_files[i])
    print(f"Processing {jpg_file} and {mp3_file}")
    jpg_clip = ImageClip(jpg_file)
    mp3_clip = AudioFileClip(mp3_file)
    jpg_clip = jpg_clip.set_duration(mp3_clip.duration)
    jpg_clip = jpg_clip.set_audio(mp3_clip)  # Set the audio of the jpg_clip to be the mp3_clip
    clips.append(jpg_clip)

# concatenate the clips
final_clip = concatenate_videoclips(clips)

# write the final clip to a file

final_clip.write_videofile(f"{directory}/final_clip.mp4", fps=24)

# close the final clip

final_clip.close()
