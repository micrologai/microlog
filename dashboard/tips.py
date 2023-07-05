#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

SEARCH_URLS = {
    "Google": "https://www.google.com/search?q=",
    "Brave": "https://search.brave.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/?va=v&t=ha&q=",
    "Bing": "https://www.bing.com/search?q=",
    "SourceGraph": "https://sourcegraph.com/search?q=",
    "StackOverflow": "https://stackoverflow.com/search?q=",
    "HackerNews": "https://hn.algolia.com/?dateRange=all&page=0&prefix=false&query=",
    "Twitter": "https://twitter.com/search?q=",
}

import js # type: ignore
import pyodide # type: ignore
from typing import List

from microlog.models import CallSite

class Tips():
    def __init__(self, calls: List[CallSite]):
        self.calls = calls
        self.modules = set([call.callSite.name.split(".")[0] for call in calls]) - set(["examples"])
        js.jQuery("#tips").empty().append(*[
            self.createButton(provider, f"{url}Performance+{'+'.join(self.modules)}")
            for provider, url in SEARCH_URLS.items()
        ])
    
    def createButton(self, provider, url):
        return (js.jQuery("<button>")
            .addClass("tips-button")
            .text(provider)
            .click(pyodide.ffi.create_proxy(lambda event: self.open(url)))
        )

    def open(self, url):
        print("Tips", self.modules, url)
        js.window.open(url)