from moviepy.editor import *
import os
import sys
import pathlib

# input arguments
# user will specify a folder which contains png and mp3 files. these will be combined into a video.

directory = sys.argv[1]

# get all png files in the directory

png_files = list(pathlib.Path(directory).glob("*.png"))

# get all mp3 files in the directory

mp3_files = list(pathlib.Path(directory).glob("*.mp3"))

print (f"{mp3_files}\n\n{png_files}")

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
    png_clip = png_clip.set_audio(mp3_clip)  # Set the audio of the png_clip to be the mp3_clip
    clips.append(png_clip)

# concatenate the clips
final_clip = concatenate_videoclips(clips)

# write the final clip to a file

final_clip.write_videofile(f"{directory}/final_clip.mp4", fps=24)

# close the final clip

final_clip.close()
