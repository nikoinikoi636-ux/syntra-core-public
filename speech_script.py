import os

def speak(text):
    os.system(f'termux-tts-speak "{text}"')
