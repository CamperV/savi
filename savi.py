from openai import AsyncOpenAI
from PyPDF2 import PdfReader
from prompt_toolkit import PromptSession
from rich import print as r_print
from rich.markdown import Markdown

from pathlib import Path

import asyncio
import time
import os

VER=0.2
OPMODE = None   # defined via args

def ingest_pdf(pdf_path):
    try:
        print(f'Ingesting {pdf_path}...')
        assert(isinstance(pdf_path, Path) and pdf_path.exists())
        reader = PdfReader(pdf_path)
        start_t = time.time()
        text = ''.join([page.extract_text() for page in reader.pages])
        print(f'read {len(reader.pages)} pages in {time.time() - start_t:02f} seconds')
        return text

    except:
        raise Exception(f'Supplied path {pdf_path} does not exist, or is not a PDF path.')

async def user_input(prompt_session):
    return await prompt_session.prompt_async()

async def get_savi_response(client, prompt):
    if OPMODE == 'SR5E':
        completion = await client.chat.completions.create(
            model='gpt-4-1106-preview',

            # yes, you need to provide this context for every message. I know
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a virtual assistant responsible for parsing and explaining the rules from a game called Shadowrun.' + \
                                ' Your name is SAVI, which stands for Shadowrun Aggregator Virtual Interface. Also, Shiawase Arms Virtual Intelligence.' + \
                                ' Only use rules from the 5th edition of Shadowrun.' + \
                                ' Reference all source books for the 5th edition.' + \
                                ' Please indicate which sourcebooks you are pulling rules from, and reference with a page number, if possible.' + \
                                ' All queries will be relevant to Shadowrun 5th Edition only.' + \
                                ' When possible, use a tabular format.' + \
                                ' Be brief in your responses.' + \
                                ' Your quantitative answers are typically incorrect. Try to use qualitative answers.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
    elif OPMODE == 'GENERIC':
        completion = await client.chat.completions.create(
            model='gpt-4-1106-preview',
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )

    return completion.choices[0].message.content
    
async def animate_ps(prompt_session):
    while True:
        for frame in get_dynamic_ps_frames():
            prompt_session.message = frame
            prompt_session.app.invalidate()
            await asyncio.sleep(1)
animate_ps.static_frames = [
    '>>> [{}] //? ',
    '>>> [{}] //: ',
]

def get_dynamic_ps_frames():
    return [
        frame.format(f'userQuery {{mode:{OPMODE}}}')
        for frame in animate_ps.static_frames
    ]

async def animate_response():
    while True:
        for frame in get_dynamic_response_frames():
            print(frame, end='\r', flush=True)
            await asyncio.sleep(0.5)
        print(end='\x1b[2K') # ANSI sequence for LINE CLEAR
animate_response.static_frames = [
    '>>> [{}] //: ',
    '>>> [{}] //: .',
    '>>> [{}] //: ..',
    '>>> [{}] //: ...',
    '>>> [{}] //:  ..',
    '>>> [{}] //:   .'
]

def get_dynamic_response_frames():
    return [
        frame.format(f'SAVI v{float(VER):0.1f} {{mode:{OPMODE}}}')
        for frame in animate_response.static_frames
    ]
    
async def chat_loop(client):
    while True:
        # two states: waiting for user input, and waiting for a response
        prompt_session = PromptSession(message=get_dynamic_ps_frames()[0])

        # animate the waiting prompt
        animate_ps_task = asyncio.create_task(animate_ps(prompt_session))
        #
        # gather input and await it, then cancel the animation
        prompt_task = asyncio.create_task(user_input(prompt_session))
        prompt = await prompt_task
        #
        animate_ps_task.cancel()

        # now generate the response (and animate the wait time)
        animate_resp_task = asyncio.create_task(animate_response())
        #
        response_task = asyncio.create_task(get_savi_response(client, prompt))
        response = await response_task
        #
        animate_resp_task.cancel()

        print(get_dynamic_response_frames()[0])
        r_print(Markdown('---'))
        r_print(Markdown(response))
        r_print(Markdown('---'))

def main(args):
    if (mode := args.mode.upper()) in ('GENERIC', 'SR5E'):
        global OPMODE
        OPMODE = mode

        client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        asyncio.run(chat_loop(client))

    else:
        raise ValueError(f'Mode value "{mode}" not supported.')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument(
        '--mode',
        type=str,
        default='SR5E',
        help='Use a generic interface, or a Shadowrun-specific interface. Options are "GENERIC" and "SR5E".'
    )
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    main(args)
