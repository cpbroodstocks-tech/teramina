"""Summarize Helpers"""
import requests

URL = "https://rnd-llm-waterquality-3gfipztgma-et.a.run.app/"


def generate_summarize(question: str):
    """generate summarize based on question"""
    data = requests.get(URL + f"/ask?question={question}", timeout=60)
    if data.status_code == 200:
        return data.json()

    return {"answer": "null"}
