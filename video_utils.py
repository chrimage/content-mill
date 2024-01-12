from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import os
from pathlib import Path

def create_video_from_clips(directory, output_file, fps=24):
    """
    Creates a video from image and audio clips in a given directory.

    :param directory: Directory containing numbered image and audio files.
    :param output_file: Path for the output video file.
    :param fps: Frames per second for the output video.
    """
    # Get all image and audio files, assuming they are named with numbers
    image_files = sorted(Path(directory).glob("*.png"))
    audio_files = sorted(Path(directory).glob("*.mp3"))

    clips = []
    for image_file, audio_file in zip(image_files, audio_files):
        # Create an ImageClip and set its duration to match the corresponding AudioFileClip
        image_clip = ImageClip(str(image_file))
        audio_clip = AudioFileClip(str(audio_file))
        video_clip = image_clip.set_duration(audio_clip.duration).set_audio(audio_clip)
        clips.append(video_clip)

    # Concatenate all video clips
    final_clip = concatenate_videoclips(clips)

    # Write the final video to the specified file
    final_clip.write_videofile(output_file, fps=fps)

    # Close the clips to free up resources
    for clip in clips:
        clip.close()
    final_clip.close()

    return output_file
