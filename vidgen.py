import sys
from video_utils import create_video_from_clips

# input arguments
# user will specify a folder which contains png and mp3 files. these will be combined into a video.

directory = sys.argv[1]

output_video_path = f"{directory}/final_video.mp4"

create_video_from_clips(directory, output_video_path)