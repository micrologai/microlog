#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import sys

ERROR_OPENAI = """
Could not import openai, please install the Microlog dependencies before running the server.

Run this:
```
      $ python3 -m pip install -r requirements.txt
      $ python3 microlog/server.py
```
"""

ERROR_KEY = """
You did not set an OpenAI key before running the Microlog server. 

Get an OpenAI API key and then run this:
```
      $ export OPENAI_API_KEY=<your-api-key>
      $ python3 microlog/server.py
```

See https://platform.openai.com/account/api-keys for creating a key.
The OpenAI API may not work when you are on a free trial of the OpenAI API.
"""

HELP = """
See https://platform.openai.com/account/api-keys
The OpenAI API may not work when you are on a free trial of the OpenAI API.
"""

def parse(log):
    import json
    from microlog.models import Call
    calls = set()
    for call in json.loads(log)["calls"]:
        calls.add(Call.fromDict(call))
    return "\n".join(call.callSite.name for call in calls)

def explainLog(application, log):
    try:
        import openai
    except:
        return(ERROR_OPENAI)

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return(ERROR_KEY)

    prompt = getPrompt(application, log)
    print(f"{prompt}")
    try:
        return cleanup(openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=350,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\"\"\""]
        )["choices"][0]["text"])
    except Exception as e:
        return f"Could not access OpenAI. Here is what they said:\n\n- {str(e)}\n{HELP}"


def cleanup(explanation):
    return (
        explanation
            .replace(" appears to be ", " is ")
            .replace(" suggest that ", " indicate that ")
            .replace(" could be ", " is ")
            .replace(" likely ", " ")
    )


def getPrompt(application, log):
    return f"""
Below is a trace with method calls made by a Python program named "{application}".
Explain in detail what purpose the program does.
Do not just list the calls it makes.

{parse(log)}
"""
