import os
import re
import subprocess
import tempfile
from pathlib import Path

import gradio as gr
import spaces

# ToonStory AI
# A small, free-friendly prototype:
# Story -> scenes -> cartoon images -> animated MP4.
# It intentionally keeps generation small so it can fit free GPU quotas.

MODEL_ID = os.getenv("IMAGE_MODEL", "stabilityai/sd-turbo")
pipe = None

def load_pipeline():
    global pipe
    if pipe is not None:
        return pipe
    import torch
    from diffusers import AutoPipelineForText2Image

    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
    )
    pipe.to("cuda")
    return pipe

def split_story(story, scene_count):
    story = (story or "").strip()
    if not story:
        return []
    # If the user provides explicit sentences, use them as scene seeds.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story) if s.strip()]
    if len(sentences) >= scene_count:
        return sentences[:scene_count]

    # Otherwise make simple scene beats from the story.
    beats = [
        "opening establishing shot",
        "the characters discover something interesting",
        "the characters have a small adventure",
        "a happy ending",
        "final cheerful group shot",
    ]
    base = story.rstrip(". ")
    return [f"{beat}: {base}." for beat in beats[:scene_count]]

def make_prompt(scene, style):
    style_text = {
        "3D Kids Cartoon": "high quality 3D children's cartoon, cute rounded characters, colorful friendly environment, soft cinematic lighting",
        "2D Kids Cartoon": "bright 2D children's cartoon illustration, clean outlines, colorful, friendly, playful",
        "Anime Kids": "family friendly anime-inspired children's illustration, colorful, expressive, soft lighting",
    }.get(style, "colorful children's cartoon")
    return f"{style_text}. {scene}. No text, no watermark, kid-safe, cheerful."

def make_video(images, out_path, seconds_per_scene=4):
    # ffmpeg is normally available in Spaces. We create a smooth slideshow
    # with a gentle zoom/pan effect, then concatenate the scenes.
    tmp = Path(tempfile.mkdtemp(prefix="toonstory_"))
    clips = []
    for i, img in enumerate(images):
        clip = tmp / f"clip_{i:02d}.mp4"
        vf = (
            "scale=1280:720:force_original_aspect_ratio=increase,"
            "crop=1280:720,"
            f"zoompan=z='min(zoom+0.0015,1.12)':d={seconds_per_scene*25}:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=25"
        )
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(img),
            "-vf", vf, "-t", str(seconds_per_scene),
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(clip)

    concat = tmp / "concat.txt"
    concat.write_text("\n".join(f"file '{c}'" for c in clips))
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-c", "copy", str(out_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(out_path)

@spaces.GPU
def generate(story, style, scene_count):
    if not story or not story.strip():
        raise gr.Error("Write a short story first.")

    scenes = split_story(story, int(scene_count))
    if not scenes:
        raise gr.Error("Write a short story first.")

    # Generate a small number of images to keep the free demo practical.
    generator = load_pipeline()
    images = []
    gallery = []

    for scene in scenes:
        prompt = make_prompt(scene, style)
        result = generator(
            prompt=prompt,
            num_inference_steps=2,
            guidance_scale=0.0,
            width=512,
            height=512,
        )
        img = result.images[0]
        images.append(img)
        gallery.append(img)

    out = Path(tempfile.mktemp(suffix=".mp4"))
    make_video(images, out)
    return gallery, str(out)

with gr.Blocks(title="ToonStory AI") as demo:
    gr.Markdown(
        "# 🎬 ToonStory AI\n"
        "Turn a short children's story into a simple animated cartoon video."
    )
    gr.Markdown(
        "**Free-demo note:** video generation uses limited shared GPU resources. "
        "Start with 1–3 scenes."
    )

    story = gr.Textbox(
        label="Your story",
        placeholder="A little bear finds a rainbow in the forest and teaches his friends about colors.",
        lines=6,
    )
    with gr.Row():
        style = gr.Dropdown(
            ["3D Kids Cartoon", "2D Kids Cartoon", "Anime Kids"],
            value="3D Kids Cartoon",
            label="Cartoon style",
        )
        scene_count = gr.Slider(1, 3, value=2, step=1, label="Number of scenes")

    generate_btn = gr.Button("✨ Generate My Cartoon", variant="primary")
    gallery = gr.Gallery(label="Generated scenes", columns=3, height="auto")
    video = gr.Video(label="Your animated video")

    generate_btn.click(
        generate,
        inputs=[story, style, scene_count],
        outputs=[gallery, video],
    )

if __name__ == "__main__":
    demo.launch()
