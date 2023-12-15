from openai import OpenAI

from pathlib import Path
import logging
import logging.handlers
import os

# logging.basicConfig(
#     format='[%(name)s] %(asctime)s [%(levelname)-5.5s] %(message)s',
#     datefmt='%H:%M:%S',
#     level=logging.DEBUG
# )

VER=0.1

logger = logging.getLogger("SAVI")
formatter = logging.Formatter('[%(name)s] %(asctime)s [%(levelname)-5.5s] %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

file_handler = logging.handlers.RotatingFileHandler(filename='savi.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def get_blocking_query(printer=print):
    printer(f'>>> [colorme USER QUERY] //? ', end='', flush=True)
    user_input = input()
    return user_input

def savi_response(msg, printer=print):
    printer(f'>>> [colorme SAVI v{float(VER):0.2f}] //: {msg}')

def main(args):
    logger = logging.getLogger('savi-inst')

    logger.debug(f'Loading OpenAI client...')
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    prompt = get_blocking_query()
    logger.debug(f'Received prompt "{prompt}"')

    logger.debug(f'Generating completion...')
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    logger.debug(f'done!')

    logger.debug(completion.choices[0].message.content)
    savi_response(completion.choices[0].message.content)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('prompt', type=str)
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    main(args)
