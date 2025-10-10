#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Use OpenAI to analyse a recording."""

import logging
import os
import textwrap
import time
import traceback

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


LLM_MODEL = os.environ.get("MICROLOG_LLM_MODEL", "gpt-4o")
LLM_BASE_URL = os.environ.get("MICROLOG_LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.environ.get("MICROLOG_LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "OPENAI API KEY IS MISSING"))


client = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=SecretStr(LLM_API_KEY),
)

ERROR_KEY = textwrap.dedent("""
    Could not find an OpenAI key. Run this:
    ```
        $ export OPENAI_API_KEY=<your-api-key>
        $ python3 microlog/server.py
    ```

    See https://platform.openai.com/account/api-keys for creating a key.
    The OpenAI API may not work when you are on a free trial of the OpenAI API.
""")

HELP = textwrap.dedent("""
    Helpful links:
    - https://platform.openai.com (general information on OpenAI APIs).
    - https://platform.openai.com/account/api-keys (for setting up keys).

    The OpenAI API may not work when you are on a free trial of the OpenAI API.
""")


def get_system_prompt_for_microlog(name: str) -> str:
    """Get system prompt instructions specific to Microlog itself"""
    return textwrap.dedent(f"""\n
        You are an authoritative, experienced, and expert Python architect.

        Analyse the design and architecture of my program named "{name}".
        If there are ways to improve the design or performance, suggest them.

        Do not suggest using cProfile, py-spy, or scalene to profile code.
        Instead suggest using the Timeline tab in Microlog. Tell people
        they can click on a slow funtion to get a link to the source code
        that will open in VSCode.
    """)


def analyse_recording(prompt: str) -> str:
    """Use OpenAI to analyse the high level design of a Python program given its trace."""
    try:
        start = time.time()
        name = prompt.split("\n", 1)[0]
        logging.info("Sending OpenAI prompt for %s", name)
        response = client.invoke([
            ("system", get_system_prompt_for_microlog(name)),
            ("human", prompt)
        ])
        duration = int(time.time() - start)
        logging.info("Received OpenAI response in %s for %s", duration, name)
        return cleanup(name, str(response.content))
    except Exception: # pylint: disable=broad-except
        return textwrap.dedent(f"""{name}
            # OpenAI Error
            Could not analyse this code using OpenAI. Here is what happened:\n
            {traceback.format_exc()}\n
            # Help
            {HELP}\n
            # The prompt used by Microlog was:
            {prompt}
        """)


def cleanup(name: str, analysis: str) -> str:
    """Clean up the analysis text."""
    return f"{name}\n{analysis}"
