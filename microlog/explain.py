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
Helpful links:
- https://platform.openai.com (general information on OpenAI APIs).
- https://platform.openai.com/account/api-keys (for setting up keys).

The OpenAI API may not work when you are on a free trial of the OpenAI API.
"""
    

def tree():
    from collections import defaultdict
    return defaultdict(tree)


def parse(log):
    import json
    from microlog.models import Call
    modules = tree()
    for serializedCall in json.loads(log)["calls"]:
        call = Call.fromDict(serializedCall)
        parts = call.callSite.name.split(".")
        module = parts[0]
        clazz = ".".join(parts[1:-1])
        function = parts[-1]
        modules[module][clazz][function] = call
    lines = []
    for module, classes in modules.items():
        if module in ["ipykernel", "jupyter_client", "IPython"]:
            continue
        lines.append(module)
        for clazz, functions in classes.items():
            lines.append(f" {clazz}")
            for function in functions:
                lines.append(f"  {function}")
    return "\n".join(lines)


def explainLog(application, log):
    try:
        import openai
    except:
        return(ERROR_OPENAI)

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return(ERROR_KEY)

    prompt = getPrompt(application, log)
    sys.stdout.write(f"{prompt}\n")
    try:
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
    except Exception as e:
        return f"""
# OpenAI ErrorCould not access OpenAI. Here is what they said:

- {str(e)}

# Help
{HELP}

# The prompt used by Microlog was:
{prompt}"
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
Below is a trace with method calls made by a Python program named "{application}".
Explain in detail what purpose the program does and not just list the calls it makes.

{parse(log)}
"""
