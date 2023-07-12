#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import sys
import traceback


ERROR_OPENAI = """
Could not import openai, please install the Microlog dependencies before running the server.

Run this:
```
      $ python3 -m pip install -r requirements.txt
      $ python3 microlog/server.py
```
"""

ERROR_KEY = """
Could not find an OpenAI key. Run this:
```
      $ export OPENAI_API_KEY=<your-api-key>
      $ python3 microlog/server.py
```

See https://platform.openai.com/account/api-keys for creating a key.
The OpenAI API may not work when you are on a free trial of the OpenAI API.
"""

HELP = """
Helpful links:
- https://platform.openai.com (general information on OpenAI APIs).
- https://platform.openai.com/account/api-keys (for setting up keys).

The OpenAI API may not work when you are on a free trial of the OpenAI API.
"""
    

def tree():
    from collections import defaultdict
    return defaultdict(tree)


def parse(data):
    from microlog import log
    from collections import defaultdict
    log.log.load(data)

    modules = tree()
    calls = defaultdict(float)
    for singleCall in log.log.calls:
        calls[singleCall.callSite.name] += singleCall.duration
    for name, duration in sorted(calls.items(), key=lambda item: -item[1]):
        parts = name.split(".")
        module = parts[0]
        clazz = ".".join(parts[1:-1])
        function = parts[-1]
        if module in ["", "tornado", "ipykernel", "asyncio", "decorator", "runpy", "traitlets", "threading", "selectors", "jupyter_client", "IPython"]:
            continue
        if len(modules[module][clazz]) < 2:
            modules[module][clazz][function] = duration
    lines = []
    for module, classes in modules.items():
        lines.append(module)
        for clazz, functions in classes.items():
            lines.append(f" {clazz}")
            for function, duration in functions.items():
                lines.append(f"  {function}")
                if len(lines) > 25:
                    return "\n".join(lines)
    return "\n".join(lines)


def explainLog(application, log):
    try:
        import openai
    except:
        return(ERROR_OPENAI)

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return(ERROR_KEY)

    prompt = "???"
    try:
        prompt = getPrompt(application, log)
        sys.stdout.write(f"{prompt}\n")
        return cleanup(prompt, openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\"\"\""]
        )["choices"][0]["text"])
    except:
        return f"""
# OpenAI Error
Could not explain this code using OpenAI. Here is what happened:

{traceback.format_exc()}

# Help
{HELP}

# The prompt used by Microlog was:
{prompt}
"""


def cleanup(prompt, explanation):
    return (explanation
        .replace(" appears to be ", " is ")
        .replace(" suggest that ", " indicate that ")
        .replace(" could be ", " is ")
        .replace(" likely ", " ")
    )


def getPrompt(application, log):
    return f"""
You are an authoritative expert Python architect.

My Python program is named "{application}".  Below is a trace.
Explain the high level design and architecture of this program. 

{parse(log)}
"""
