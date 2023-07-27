#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

SEARCH_URLS = {
    "Google": "https://www.google.com/search?q=",
    "Brave": "https://search.brave.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?va=v&t=ha&q=",
    "Bing": "https://www.bing.com/search?q=",
    "SourceGraph": "https://sourcegraph.com/search?q=lang:",
    "StackOverflow": "https://stackoverflow.com/search?q=",
    "HackerNews": "https://hn.algolia.com/?dateRange=all&page=0&prefix=false&query=",
    "Twitter": "https://twitter.com/search?q=",
}

import js # type: ignore
import pyodide # type: ignore
import random
from typing import List

from microlog.models import CallSite

PROMPTS = [
    "best practices",
    "performance",
    "how can I",
]
        
IGNORE_MODULES = set([
    "",
    "copy",
    "__main__",
    "examples",
])

class Tips():
    def __init__(self, calls: List[CallSite]):
        self.calls = calls
        self.modules = list(set([call.callSite.name.split(".")[0] for call in calls]) - IGNORE_MODULES)
        random.shuffle(self.modules)
        usage = f"This code is using the following modules: {', '.join(self.modules)}.<br><br>" if self.modules else ""
        prompt = " AND ".join(random.choice(PROMPTS).split(" "))
        js.jQuery("#tips").empty() \
            .append(js.jQuery("<div>").html(f"""
                {usage}
                To improve best practices or performance of your code, consider these resources:
            """)) \
            .append(*[
                self.createButton(provider, f"/microlog/images/logo-{provider.lower()}.png", f"{url}Python AND {' AND '.join(list(self.modules)[:2])} AND {prompt}")
                for provider, url in SEARCH_URLS.items()
            ])
    
    def createButton(self, provider, logo, url):
        return (js.jQuery("<button>")
            .addClass("tips-button")
            .append(
                js.jQuery("<img>").addClass("tips-logo").attr("src", logo),
                js.jQuery("<span>").text(provider),
            )
            .click(pyodide.ffi.create_proxy(lambda event: self.open(url)))
        )

    def open(self, url):
        print("Tips", self.modules, url)
        js.window.open(url)