import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv('.env')

_client = None


def get_client():
    """Create the OpenAI client on first use, so a missing key fails with a clear
    message at call time (where the UI can handle it) rather than when importing."""
    global _client
    if _client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to the .env file.")
        # Timeout and retries stop a slow or flaky API call from hanging the app
        _client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
    return _client


def get_embedding(input, model='text-embedding-3-small'):
    response = get_client().embeddings.create(
        input=input,
        model=model
    )
    return [x.embedding for x in response.data]


def get_completion(prompt, model="gpt-4o-mini", temperature=0, top_p=1.0, max_tokens=1024, n=1, json_output=False):
    if json_output == True:
        output_json_structure = {"type": "json_object"}
    else:
        output_json_structure = None

    messages = [{"role": "user", "content": prompt}]
    response = get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=1,
        response_format=output_json_structure,
    )
    return response.choices[0].message.content


def get_completion_by_messages(messages, model="gpt-4o-mini", temperature=0, top_p=1.0, max_tokens=1024, n=1):
    response = get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=1
    )
    return response.choices[0].message.content


def is_flagged(text):
    """Return True if the OpenAI Moderation API flags the text."""
    response = get_client().moderations.create(input=text)
    return response.results[0].flagged


def count_tokens(text):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    return len(encoding.encode(text))


def count_tokens_from_message(messages):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    value = ' '.join([x.get('content') for x in messages])
    return len(encoding.encode(value))
