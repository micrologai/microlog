#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

"""Main module for the Microlog dashboard application."""

from __future__ import annotations

import asyncio
from collections import defaultdict
import traceback
from typing import Any
from typing import Callable

import ltk

import js
import pyodide

from microlog.dashboard.treeview import TreeView
from microlog.models import recording
from microlog.dashboard.design import Design
from microlog.dashboard.flamegraph import Flamegraph
from pyodide import http

window = ltk.find(js.window)
body = ltk.find("body")

class Main():
    """
    Main class for the Microlog dashboard application.
    Handles UI creation, log management, flamegraph visualization, and event setup.
    """

    def __init__(self) -> None:
        """
        Initialize the dashboard, create UI, set up handlers, and load logs if present in URL.
        """
        self.create_ui()
        self.flamegraph = Flamegraph("#flameCanvas", "#timelineCanvas")
        self.design = Design([])
        self.name = ""
        self.setup_log_handlers()
        self.setup_search_handler()
        self.show_all_logs()
        self.load()
        self.ai_responses = {}
        self.last_ai_request: str = ""
        ltk.find(ltk.window).on("resize", ltk.proxy(lambda event: self.resize()))

    def load(self, name: str="") -> None:
        """Load the recording."""
        self.flamegraph.reset()
        self.name = name
        if not self.name:
            self.name = self.get_recording_from_url()
        if self.name:
            asyncio.create_task(self.load_recording(self.name))
        self.resize()

    async def load_recording(self, name: str) -> None:
        """
        Load a log file by name and display its flamegraph.

        Args:
            name (str): The name of the log file to load.
        """
        self.flamegraph.loading(name)
        self.flamegraph.draw()
        recording.clear()
        url = f"zip/{name}"
        try:
            response = await http.pyfetch(url)
            binary_data = await response.bytes()
            self.show_flamegraph(binary_data)
            self.design = Design(self.flamegraph.calls)
        except pyodide.http.AbortError as e:
            self.flamegraph.show_message(f"Cannot reach the Microlog server: {e}")
        except Exception as e: # pylint: disable=broad-except
            self.flamegraph.show_message(f"Cannot load the recording: {type(e)} {e}")

    def show_all_logs(self) -> None:
        """
        Fetch and display all logs matching the current filter.
        """
        filter_string = ltk.find("#filter").val().lower()
        url = f"logs?filter={filter_string}"
        js.jQuery.get(
            url,
            ltk.proxy(
                lambda data, *rest: self.render_logs(data.strip().split("\n") if data else [])
            ),
        )
        ltk.find(".logs").empty().append(
            ltk.create("<img>").addClass("spinner").attr("src", "/images/spinner.gif"),
            ltk.create("<span>").css("color", "pink").text("Loading..."),
        )

    def delete_log(self, name: str, done_handler: Callable[[], None]) -> None:
        """
        Delete a log file by name and call the provided handler when done.

        Args:
            name (str): The name of the log file to delete.
            done_handler (Callable): Function to call after deletion.
        """
        url = f"delete/{name}"
        ltk.get(url, ltk.proxy(lambda data, *rest: done_handler()))

    def get_recording_from_url(self) -> str:
        """
        Extract the log file name from the URL hash.

        Returns:
            str: The log file path if present, else an empty string.
        """
        hash_string = js.document.location.hash
        if hash_string:
            app, name = hash_string[1:].split("/")[:2]
            return f"{app}/{name}"
        return ""

    def render_logs(self, log_list: list[str]) -> None:
        """
        Render the list of logs in the sidebar.

        Args:
            log_list (list[str]): List of log file entries.
        """
        ltk.find(".logs").empty()
        if not any(log_list):
            ltk.find(".logs").empty().append(
                ltk.create("<span>").css("color", "pink").text("No matching logs found")
            )
            return
        logs: dict[str, dict[str, dict[str, str]]] = {}
        for entry in [entry for entry in reversed(log_list) if entry]:
            try:
                entry = entry.rstrip("/")
                application, name = entry.rsplit("/", 1)
                if application != "-":
                    if application not in logs:
                        logs[application] = {}
                    run = name.replace(".log", "")
                    logs[application][run] = {}
            except Exception as e: # pylint: disable=broad-except
                print(f"Cannot handle log name {entry}: {e}")
                traceback.print_exc()
        TreeView(
            ltk.find(".logs").empty(),
            logs,
            self.get_recording_from_url(),
            lambda path: self.reload(path), # pylint: disable=unnecessary-lambda
            lambda path, done_handler: self.delete_log(path, done_handler), # pylint: disable=unnecessary-lambda
            self.refresh_logs,
        )

    def reload(self, name: str) -> None:
        """Reload the dashboard with the specified log file."""
        js.document.location.hash = f"#{name}"
        self.load(name)

    def show_flamegraph(self, pickled_data: Any) -> None:
        """
        Display the flamegraph for the loaded log data.
        """
        if pickled_data:
            try:
                recording.load(pickled_data)
            except Exception as e: # pylint: disable=broad-except
                self.flamegraph.show_message(f"Could not load recording: {e}")
                return
            self.flamegraph.load()
            self.flamegraph.draw()

    def refresh_logs(self, _: Any | None = None) -> None:
        """
        Refresh the log list based on the current filter.
        """
        js.localStorage.setItem("filter", ltk.find("#filter").val())
        js.setTimeout(ltk.proxy(lambda: self.show_all_logs()), 1) # pylint: disable=unnecessary-lambda

    def setup_log_handlers(self) -> None:
        """
        Set up event handlers for log refresh and filter changes.
        """
        ltk.find("#refresh").click(ltk.proxy(lambda event: self.refresh_logs()))
        ltk.find("#filter").change(ltk.proxy(lambda event: self.refresh_logs()))

    def setup_search_handler(self) -> None:
        """
        Set up event handler for span search input.
        """
        ltk.find(".span-search").keyup(
            ltk.proxy(lambda event: self.flamegraph.draw())
        )

    def resize(self, _: Any | None = None) -> None:
        """
        Resize the dashboard UI elements to fit the window.

        Args:
            event (Any | None): The resize event, if any.
        """
        ltk.find(".sidebar").height(window.height() - 2)
        ltk.schedule(ltk.proxy(lambda: self.flamegraph.resize()), "resize") # pylint: disable=unnecessary-lambda

    def create_flamegraph(self) -> None:
        """Create and render the flamegraph tab."""
        return (
            ltk.VBox(
                ltk.VBox(
                    ltk.Canvas()
                        .attr("id", "timelineCanvas"),
                    ltk.Canvas()
                        .attr("id", "flameCanvas")
                ),
                ltk.Div().css("width", "100%").css("height", 5),
                ltk.Div().attr("id", "hairline")
                    .addClass("hairline"),
                ltk.Div().attr("id", "summary")
                    .addClass("summary"),
                ltk.Input("")
                    .attr("id", "span-search")
                    .attr("placeholder", "search regex...")
                    .addClass("filter span-search"),
                ltk.Div()
                    .attr("id", "dialog")
                    .addClass("dialog"),
            )
            .addClass("tabs-timeline tabs-content")
            .css("width", "100%")
            .attr("name", "Timeline")
        )

    def create_log(self) -> None:
        """Create and render the log tab."""
        return (
            ltk.VBox(
            )
            .attr("id", "tabs-log")
            .addClass("tabs-log tabs-content")
            .css("width", "100%")
            .css("height", ltk.find(ltk.window).height() - 50)
            .css("overflow-y", "auto")
            .attr("name", "Log")
        )

    def create_design(self) -> None:
        """Create and render the design tab. """
        return (
            ltk.VBox(
                ltk.Div()
                    .attr("id", "design-canvas")
                    .css("height", ltk.find(ltk.window).height() - 50)
                    .css("width", "100%"),
                ltk.Span()
                    .attr("id", "design-configure")
                    .addClass("design-configure")
            )
            .addClass("tabs-design tabs-content")
            .attr("name", "Design")
        )

    def create_analysis(self) -> None:
        """Create and render the ai tab. """
        return (
            ltk.VBox(
                ltk.Text("Prompt for OpenAI:")
                    .css("color", "#cbc9c9")
                    .css("height", 23)
                    .css("font", "bold 14px sans-serif"),
                ltk.TextArea(self.get_prompt())
                    .addClass("prompt")
                    .css("font", "normal 14px monospace")
                    .css("margin-bottom", 16)
                    .attr("id", "prompt"),
                ltk.Button("Ask OpenAI", ltk.proxy(lambda _event: self.ask_ai()))
                    .attr("id", "ask-ai"),
                ltk.Preformatted()
                    .attr("id", "analysis")
                    .addClass("analysis")
            )
            .addClass("tabs-ai tabs-content")
            .css("height", ltk.find(ltk.window).height() - 50)
            .css("overflow-y", "auto")
            .attr("name", "Analysis")
        )

    def extract_callstack_summary(self) -> str:
        """Extract the calls made by the app from the recording."""
        def tree():
            return defaultdict(tree)
        modules = tree()
        calls = defaultdict(float)
        for call in recording.calls:
            calls[call.call_site.name] += call.duration
        for name, duration in sorted(calls.items(), key=lambda item: -item[1]):
            parts = name.split(".")
            module = parts[0]
            clazz = ".".join(parts[1:-1])
            function = parts[-1]
            if module in [
                    "", "tornado", "ipykernel", "asyncio", "decorator", "runpy",
                    "traitlets", "threading", "selectors", "jupyter_client", "IPython"
                ]:
                continue
            if len(modules[module][clazz]) < 2:
                modules[module][clazz][function] = duration
        lines = []
        for module, classes in modules.items():
            lines.append(module)
            for clazz, functions in classes.items():
                lines.append(f" {clazz}")
                for function, duration in functions.items():
                    if function in ("", "<module>", "__init__"):
                        lines.append(f"  import {function.strip(".")} {duration:.1f}s")
                    else:
                        lines.append(f"  {module} {clazz} {duration:.1f}s")
                    if len(lines) > 25:
                        return "\n".join(line for line in lines if line)
        return "\n".join(line for line in lines if line)

    def get_prompt(self) -> str:
        """Generate the prompt for OpenAI based on the recording."""
        application = self.get_recording_from_url().split("/", 1)[0]
        return f"""
You are an authoritative, experienced, and expert Python architect.

Analyse the design and architecture of my program named "{application}".
If there are ways to improve the design or performance, suggest them.
"""

    def ask_ai(self) -> None:
        """Ask an LLM to analyse our recording."""
        self.last_ai_request = name = self.get_recording_from_url()
        if name in self.ai_responses:
            return self.show_ai_response(self.ai_responses[name])
        spinner = '<br><br><img src="/images/windmill.gif" width="80" height="60"/>'
        loading = f"Loading OpenAI analysis. This can take a minute... {spinner}"
        ltk.find("#analysis").html(loading)
        ltk.find("#ask-ai").attr("disabled", True)
        prompt = "\n".join([
            ltk.find("#prompt").val(),
            "Here is a trace of my code:",
            self.extract_callstack_summary()
        ])
        def post():
            ltk.post(
                "/analysis/",
                f"{name}\n{prompt}",
                ltk.proxy(lambda response: self.show_ai_response(response)), # pylint: disable=unnecessary-lambda
                "text"
            )
        ltk.schedule(post, "allow windmill to load before doing a post")

    def show_ai_response(self, response: str) -> None:
        """Display the response from the LLM in the analysis tab."""
        name, response = response.split("\n", 1)
        self.ai_responses[name] = response
        if name == self.last_ai_request:
            ltk.find("#analysis").text(response)
        ltk.find("#ask-ai").attr("disabled", False)

    def create_sidebar(self) -> None:
        """Create and render the sidebar with log filter and list."""
        return (
            ltk.VBox(
                ltk.HBox(
                    ltk.Input("")
                        .attr("id", "filter")
                        .attr("placeholder", "filter regex...")
                        .addClass("filter")
                ).css("height", 38).css("background", "#545454"),
                ltk.Div().attr("id", "logs").addClass("logs")
            )
            .addClass("sidebar")
        )

    def create_ui(self) -> None:
        """Create and render the main dashboard UI layout."""
        ltk.find(".loading").remove()
        body.append(
            ltk.HorizontalSplitPane(
                self.create_sidebar(),
                ltk.Tabs(
                    self.create_flamegraph(),
                    self.create_log(),
                    self.create_design(),
                    self.create_analysis(),
                )
                .on("tabsactivate", ltk.proxy(lambda *args: self.switch_tab())),
                "main",
            ).addClass("main")
        )
        self.customize_styling()

    def switch_tab(self) -> None:
        """Handle tab switch events to update UI elements accordingly."""
        ltk.find(".dialog").css("display", "none")

    def customize_styling(self) -> None:
        """Apply custom CSS styles to the UI elements."""
        ltk.find(".ltk-tabs") \
            .css("padding", 0) \
            .css("overflow", "hidden") \
            .css("border-width", 0) \
            .css("width", "100%") \
            .css("background", "#222222")

        ltk.find(".ui-tabs-panel") \
            .css("padding", 0) \
            .css("overflow", "hidden") \
            .css("height", "100%") \
            .css("width", "100%") \
            .css("background", "#222222")

        ltk.find(".ui-widget-header") \
            .css("background", "#545454") \
            .css("border-width", 0) \
            .css("border-radius", 0) \
            .css("border-bottom-width", 1)


def load():
    Main()
