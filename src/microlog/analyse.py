#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Use OpenAI to analyse a recording."""

import logging
import textwrap
import time
import traceback

from openai import OpenAI


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


def add_system_prompt_for_microlog(prompt: str) -> str:
    """Add prompt instructions specific to Microlog itself"""
    return prompt + textwrap.dedent("""\n
        Do not suggest using cProfile, py-spy, or scalene to profile code.
        Instead suggest using the Timeline tab in Microlog. Tell people
        they can click on a slow funtion to get a link to the source code
        that will open in VSCode.
    """)


def analyse_recording(prompt: str) -> str:
    """Use OpenAI to analyse the high level design of a Python program given its trace."""
    client = OpenAI()
    try:
        start = time.time()
        name = prompt.split("\n", 1)[0]
        logging.info("Sending OpenAI prompt for %s", name)
        response = client.responses.create(model="gpt-5", input=prompt)
        duration = int(time.time() - start)
        logging.info("Received OpenAI response in %s for %s", duration, name)
        return cleanup(name, response.output_text)
    except Exception: # pylint: disable=broad-except
        return textwrap.dedent(f"""
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
