# ToonStory AI

A small prototype that turns a short story into cartoon scene images and a simple animated MP4.

## Important truth about the free version

This is designed for a free Hugging Face ZeroGPU Space. Free accounts currently get a limited daily GPU quota, so this is intentionally a small 1–3 scene prototype. It does NOT promise unlimited AI video generation.

The "animation" is created by giving each generated cartoon scene gentle motion/zoom and combining the scenes into an MP4. It is a real video, but it is not yet full text-to-video character animation.

## Deploy from your phone

1. Open https://huggingface.co/spaces
2. Tap **Create new Space**.
3. Choose **Gradio**.
4. If your account is eligible, choose **ZeroGPU** hardware.
5. Upload `app.py` and `requirements.txt`.
6. Wait for the Space to build.
7. Open the Space and enter a short story.
8. Start with **1 scene** for the first test.

Do NOT put your private Hugging Face token into `app.py`.

## If ZeroGPU is not offered

Hugging Face says free personal accounts need to be in good standing (including a verified email and an account older than 30 days) to host up to two ZeroGPU Spaces. If the option is unavailable on your account, you can still use the code elsewhere, but a genuinely free hosted GPU is not guaranteed.

## Next upgrades

After this prototype works, the next version can add:
- character consistency
- automatic storyboarding
- narration
- subtitles
- background music
- sound effects
- better image models
- actual image-to-video models
- 16:9 YouTube export
