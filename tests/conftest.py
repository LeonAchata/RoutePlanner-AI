import os

# Settings are read once per process, so set fake keys before the app imports.
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "AIzaTestKey")
