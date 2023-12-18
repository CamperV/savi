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

async def get_savi_response(client, prompt):
    completion = await client.chat.completions.create(
        model="gpt-4",
        # model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a virtual assistant responsible for parsing and explaining the rules from a game called Shadowrun."
            },
            {
                "role": "user",
                "content": prompt
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
    
async def chat_loop(client):
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
    response_task = asyncio.create_task(get_savi_response(client, prompt))
    response = await response_task
    #
    animate_resp_task.cancel()

    print(f'>>> [SAVI v{float(VER):0.2f}] //: {response}')

def main(args):
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # first, ingest all PDFs and "configure" this open instance of GPT4processed_text
    processed_text = ""
    for pdf in Path('pdfs').rglob('*.txt'):
        with open(pdf, 'r', encoding='utf-8') as rf:
            start_t = time.time()
            processed_text = rf.read()
            print(f'> read {len(processed_text)} text lines? in {time.time() - start_t:02f} seconds')
    ingest_prompt = f"The following rulebook explains rules about Shadowrun: {processed_text}"
    print(ingest_prompt[:100])

    completion = asyncio.run(get_savi_response(client, ingest_prompt[:100]))
    # print(completion)
    print(f'I have read 1000 characters of Shadowrun, I think.')

    asyncio.run(chat_loop(client))
    # ingest all pdfs on the path
    # for pdf in Path('pdfs').rglob('*.pdf'):
    #     pdf_text = ingest_pdf(pdf)

    #     with open(f'pdfs/{pdf.stem}.txt', 'w', encoding='utf-8') as pf:
    #         pf.write(pdf_text)



if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    # parser.add_argument('prompt', type=str)
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    main(args)
