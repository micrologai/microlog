#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import json
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

ERROR = """
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


def explainLog(application, log):
    if not openai.api_key:
        return(ERROR)
    prompt = getPrompt(application, log)
    print(prompt)
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


def parse(log): 
    import config
    import models
    counts = defaultdict(int)
    duration = defaultdict(float)
    for n, line in enumerate(log.split("\n")):
        try:
            event = json.loads(f"[{line}]")
            kind = event[0]
            if kind == config.EVENT_KIND_SYMBOL:
                models.unmarshallSymbol(event)
            elif kind == config.EVENT_KIND_CALLSITE:
                models.CallSite.unmarshall(event)
            elif kind == config.EVENT_KIND_CALL:
                call = models.Call.unmarshall(event)
                counts[call] += 1
                duration[call] += call.duration
        except Exception as e:
            print(f"Microlog: Error parsing line {n+1} {e}:\n{line}\n")
            raise
    return "\n".join(
        f"{call.callSite.name.replace('__main__.', '')}\t{counts[call]}"
        for call in counts
        if duration[call] > 1
    )


def cleanup(explanation):
    return (
        explanation
            .replace(" appears to be ", " is ")
            .replace(" could be ", " is ")
            .replace(" likely ", " ")
    )


def getPrompt(application, log):
    return f"""
Below is a table with method calls made by a Python program named "{application}".
Explain in detail what purpose the program has. Do not just list the calls it makes:

Method Name          Count  
----------------------------
{parse(log)}
----------------------------
        """
