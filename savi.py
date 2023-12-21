from openai import AsyncOpenAI
from PyPDF2 import PdfReader
from prompt_toolkit import PromptSession
from pathlib import Path

import logging
import logging.handlers
import asyncio
import time
import os

VER=0.1

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

async def get_savi_response(client, prompt, mode='shadowrun'):
    if mode == 'shadowrun':
        completion = await client.chat.completions.create(
            model='gpt-4-1106-preview',

            # yes, you need to provide this context for every message. I know
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a virtual assistant responsible for parsing and explaining the rules from a game called Shadowrun.' + \
                                ' Only use rules from the 5th edition of Shadowrun.' + \
                                ' Use as much errata as possible.' + \
                                ' Reference all source books for the 5th edition.' + \
                                ' Please indicate which sourcebooks you are pulling rules from, and reference with a page number, if possible.' + \
                                ' Use the english-language versions.' + \
                                ' All queries will be relevant to Shadowrun 5th Edition only.' + \
                                ' When possible, use a tabular format.' + \
                                ' Be brief in your responses.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
    elif mode == 'generic':
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
        for frame in animate_ps.frames:
            prompt_session.message = frame
            prompt_session.app.invalidate()
            await asyncio.sleep(0.5)
animate_ps.frames = [
    '>>> [USER QUERY] //? ',
    '>>> [USER QUERY] /// ',
    '>>> [USER QUERY] ?// ',
    '>>> [USER QUERY] /?/ '
]

async def animate_response():
    while True:
        for frame in animate_response.frames:
            print(frame, end='\r', flush=True)
            await asyncio.sleep(0.5)
        print(end='\x1b[2K') # ANSI sequence for LINE CLEAR
animate_response.frames = [
    f'>>> [SAVI v{float(VER):0.2f}] //: ',
    f'>>> [SAVI v{float(VER):0.2f}] //: .',
    f'>>> [SAVI v{float(VER):0.2f}] //: ..',
    f'>>> [SAVI v{float(VER):0.2f}] //: ...',
    f'>>> [SAVI v{float(VER):0.2f}] //:  ..',
    f'>>> [SAVI v{float(VER):0.2f}] //:   .'
]
    
async def chat_loop(client, mode='shadowrun'):
    while True:
        # two states: waiting for user input, and waiting for a response
        prompt_session = PromptSession(message=animate_ps.frames[0])

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
        response_task = asyncio.create_task(get_savi_response(client, prompt, mode=mode))
        response = await response_task
        #
        animate_resp_task.cancel()

        print(f'>>> [SAVI v{float(VER):0.2f}] //: {response}')

def main(args):
    if (mode := args.mode.lower()) not in ('generic', 'shadowrun'):
        raise ValueError(f'Mode value "{mode}" not supported.')

    client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    asyncio.run(chat_loop(client, mode=args.mode.lower()))

    # ingest all pdfs on the path
    # for pdf in Path('pdfs').rglob('*.pdf'):
    #     pdf_text = ingest_pdf(pdf)

    #     with open(f'pdfs/{pdf.stem}.txt', 'w', encoding='utf-8') as pf:
    #         pf.write(pdf_text)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--mode', type=str, help='Use a generic interface, or a Shadowrun-specific interface. Options are "generic" and "shadowrun".')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    main(args)
