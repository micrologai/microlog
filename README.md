# microlog.ai

_Microlog_ is a continuous profiler and logger for the Python language.
Logs and performance profiles are collected and analyzed.
_Microlog_ explains application behavior using interactive graphs.
It summarizes and explains the code using AI.

_Microlog_ makes understanding complex applications easy, reducing support costs
and shortening production problems, increasing application quality, and minimizing outages.

# Installing microlog.ai

To install _Microlog_ from pypi run:
```
python3 -m pip install microlog
```

To install _Microlog_ globally using a `sitecustomize.py`, run:

```
  git clone https://github.com/micrologai/microlog
  cd micrologai/microlog
  python3 setup.py install
```

# How to use microlog.ai

If you used the setup command shown above, 
any time a Python process runs using the same runtime you used to setup _Microlog_, it will automatically trigger _Microlog_ to generate a recording. 

To use microlog manually, use:
```
  import microlog

  with microlog.enabled():
      # run any Python code
```

To give you an idea of the features of _Microlog_, you could run all the examples. This does assume you set up microlog globally. In that case, run:

```
  sh examples/runall.sh
```

This runs for a minute and eventually produces 13 logs. You will see lines appear looking like this:

```
📈 Microlog ··· 26.3s ··· 4.6KB ··· examples-memory ··· http://127.0.0.1:4000/log/examples-memory/0.1.1/2023_07_12_10_24_53 🚀
```

This shows how long the app ran, the size of the (compressed) log, its name, and a URL to view the result.
The report URL is rendered by the _Microlog_ server implemented in `microlog/server.py`.  If it is not yet running,
you can start it as follows:

```
  python3 microlog/server.py
```

# The Microlog.ai UI 

To describe the UI features of _Microlog_, we will look at the output of the `examples\memory.py` example:

![Example run of microlog](https://github.com/micrologai/microlog/raw/main/microlog/images/overview.png)

The main elements of the UI are:

 - `Log list`, at the left, showing currently available logs on the local machine.
 - `Timeline`, the starting point for analysis of your application:
    - `Status`, providing insights into CPU, memory, and I/O.
    - `Timescale`, with ticks for second elapsed since start.
    - `Flamegraph`, showing the result of the continuous profiler. 
 - `Design`, showing a graphical rendering of the structure of the application.
 - `Log`, listing all print and logging output and statistics in a chronological order.
 - `Explanation`, giving a human language description of your code, using OpenAIs' ChatGPT.
 - `Tips`, linking to best practices and tips for the modules used in your code.


## Timeline Navigation and Zoom

Using the mouse, the dashboard can be panned and zoomed. More details will be shown when zoomed in deeper:

![Example run of microlog](https://github.com/micrologai/microlog/raw/main/microlog/images/zoomedin.png)

In the above example, we panned the flame graph by grabbing it with the mouse and zoomed in using the scrollwheel on the mouse.

In addition, we clicked on a method call in the flame graph, which is now highlight in red. A moveable popup dialog shows details about the method, such as average CPU during the call. A CPU percentage below 100% means the process is involved
in reading or writing files on the local disk, loading or sending data over sockets, loading new modules (requiring disk I/O), or async or thread synchronization, or other system level event handling using `select` or event handlers. 

Low CPU typically indicates a bottleneck and warrants in-depth investigation.

## Timeline Anomaly Detection

When a method is selected in the flame graph, the popup shows information about similar calls detected in the same run, showing when they ran and how long they ran. _Microlog_ also uses anomaly detection to highlight methods you may want to investigate in more detail. In the screenshot below, the average call duration is 1 second, and four calls were more than 50% over the average. 

Automatic anomaly detection, call stack analysis, and process health indicators offered by _Microlog_ allow you to debug performance/quality issues quickly.

![Anomaly detection in the Microlog UI](https://github.com/micrologai/microlog/raw/main/microlog/images/anomaly.png)

## Timeline Detecting expensive I/O or Starved Processes

The top bar shows general statistics for the process, such as CPU and number of modules loaded over time. 
Note that a low CPU in the top bar tends to indicate I/O took place at that moment.

![Mircolog's status bar](https://github.com/micrologai/microlog/raw/main/microlog/images/status.png)

## Timeline Integrating Profiling with Logging

Log entries are shown as visual markers in the top bar. Because _Microlog_ shows log entries on the timeline, analyzing problems becomes much easier than with normal logs. No more scrolling page after page to find a stack trace. With _Microlog_, they appear as easy-to-see stop signs:

![Log entries in the status bar](https://github.com/micrologai/microlog/raw/main/microlog/images/error-log.png)

## Formatting Logs with Markdown

Log entries can be formatted using Markdown to make it easier to show important information to the reader.

![Using markdown for log entries](https://github.com/micrologai/microlog/raw/main/microlog/images/markdown.png)

# Logging 

_Microlog_ detects calls to `print` and `logging`. Those calls are automatically intercepted
added to the _Microlog_ event log.  

Manual log entries can be inserted into Microlog using `info`, `warn`, `debug`, and `error`:

```python
   print("Add a log entry to microlog with an info marker...")
   print("... or as an error marker.", stream=sys.stderr)

   import logging
   logger = logging.Logger("Microlog Demo")

   logger.info("Add a log entry to microlog with an info marker...")
   logger.debug("... or a bug marker...")
   logger.warning("... or a warning marker...")
   logger.error("... or an error marker.")
   
   microlog.info("Add something to the log explicitly...")
   microlog.warning("... as a warning...")
   microlog.debug("... as a debug message...")
   microlog.error("... as an error.")
```

# Design

The Design tab analyzes the runtime call graph and draws a structural diagram of the underlying design of your application.
Here is an example for `examples\go.py`:

![Microlog's innovative design graph](https://github.com/micrologai/microlog/raw/main/microlog/images/design-go.png)

# Log

The log tab contains a chronological listing of all print and logging output, statistics, and analysis performed by _Microlog_ in a more traditional linear log style:

![Microlog's traditional log, with a twist](https://github.com/micrologai/microlog/raw/main/microlog/images/log.png)

The links shown in lightblue directly take you to the source file where the print took place. This makes it extremely easy to figure out what code prints what exactly. For the `files.py` example, the log shows that this program leaked one file descriptor. That same report is also shown in the timeline when you click at the warning icon at the end of the run. 
The popup also shows a link to the source location where the file was opened:

![Detecting leaked file descriptors](https://github.com/micrologai/microlog/raw/main/microlog/images/fd-leak.png)

## Log - Memory Leaks

In addition to checking for leaked file descriptors, _Microlog_ aims to detect memory leaks. Those objects that were
allocated but cannot be garbage-collected as they are either reachable from a module or are involed in a reference cycle that
cannot be broken. The following report shows the top-10 offenders for the `dataframes.py` example, that uses Pandas dataframes.

![Detecting memory leaks](https://github.com/micrologai/microlog/raw/main/microlog/images/memory-leak.png)

# Explanation

The explanation tab shows a human-language explanation provided by OpenAI's `ChatGPT` to explain the design and implementation behind the application being monitored by _Microlog_. This analysis is not performed on the source code, but on a condensed call graph generated from the performance log that was recorded by _Microlog_. Here is an example of the what `ChatGPT` thinks of
our `examples\go.py` execution:

![ChatGPT's simple explanation of complex Python code](https://github.com/micrologai/microlog/raw/main/microlog/images/chatgpt.png)

# Tips

To discover best practices, performance tips, or tutorials for modules being used by the application, _Microlog_ offers quick
links to general information sources, such as search engines and Q&A sites:

![Tips make you a better Python developer](https://github.com/micrologai/microlog/raw/main/microlog/images/tips.png)


# Developer Notes

## Run all unit tests

```
python3 -m unittest discover tests
```


## Upload new version to PyPi

First build the package into a source distribution and a Python wheel:
```
python3 -m pip install --user --upgrade setuptools wheel twine build
python3 -m build --sdist
python3 -m build --wheel
```

Then verify whether the build works for pypi:
```
twine check dist/*
```

Then upload to the pypi test environment:
```
twine upload --repository pypitest dist/*
```

```
twine upload dist/*
```

# License



## Run all examples

```
sh examples/runall.sh
```

# License

_Microlog_ is released under version 1 of the [Server Side Public License (SSPL)](LICENSE).



To give you an idea of the features, of _Microlog_, run all the examples:

```
  sh examples/runall.sh
```

This runs for a minute and eventually produces 13 logs. You will see lines appear looking like this:

```
📈 Microlog ··· 26.3s ··· 4.6KB ··· examples-memory ··· http://127.0.0.1:4000/log/examples-memory/0.1.1/2023_07_12_10_24_53 🚀
```

This shows how long the app ran, the size of the (compressed) log, its name, and a URL to view the result.
The report URL is rendered by the _Microlog_ server implemented in `microlog/server.py`.  If it is not yet running,
you can start it as follows:

```
  python3 microlog/server.py
```

# The Microlog.ai UI 

To describe the UI features of _Microlog_, we will look at the output of the `examples\memory.py` example:

![Example run of microlog](https://github.com/micrologai/microlog/raw/main/microlog/images/overview.png)

The main elements of the UI are:

 - `Log list`, at the left, showing currently available logs on the local machine.
 - `Timeline`, the starting point for analysis of your application:
    - `Status`, providing insights into CPU, memory, and I/O.
    - `Timescale`, with ticks for second elapsed since start.
    - `Flamegraph`, showing the result of the continuous profiler. 
 - `Design`, showing a graphical rendering of the structure of the application.
 - `Log`, listing all print and logging output and statistics in a chronological order.
 - `Explanation`, giving a human language description of your code, using OpenAIs' ChatGPT.
 - `Tips`, linking to best practices and tips for the modules used in your code.


## Timeline Navigation and Zoom

Using the mouse, the dashboard can be panned and zoomed. More details will be shown when zoomed in deeper:

![Example run of microlog](https://github.com/micrologai/microlog/raw/main/microlog/images/zoomedin.png)

In the above example, we panned the flame graph by grabbing it with the mouse and zoomed in using the scrollwheel on the mouse.

In addition, we clicked on a method call in the flame graph, which is now highlight in red. A moveable popup dialog shows details about the method, such as average CPU during the call. A CPU percentage below 100% means the process is involved
in reading or writing files on the local disk, loading or sending data over sockets, loading new modules (requiring disk I/O), or async or thread synchronization, or other system level event handling using `select` or event handlers. 

Low CPU typically indicates a bottleneck and warrants in-depth investigation.

## Timeline Anomaly Detection

When a method is selected in the flame graph, the popup shows information about similar calls detected in the same run, showing when they ran and how long they ran. _Microlog_ also uses anomaly detection to highlight methods you may want to investigate in more detail. In the screenshot below, the average call duration is 1 second, and four calls were more than 50% over the average. 

Automatic anomaly detection, call stack analysis, and process health indicators offered by _Microlog_ allow you to debug performance/quality issues quickly.

![Anomaly detection in the Microlog UI](https://github.com/micrologai/microlog/raw/main/microlog/images/anomaly.png)

## Timeline Detecting expensive I/O or Starved Processes

The top bar shows general statistics for the process, such as CPU and number of modules loaded over time. 
Note that a low CPU in the top bar tends to indicate I/O took place at that moment.

![Mircolog's status bar](https://github.com/micrologai/microlog/raw/main/microlog/images/status.png)

## Timeline Integrating Profiling with Logging

Log entries are shown as visual markers in the top bar. Because _Microlog_ shows log entries on the timeline, analyzing problems becomes much easier than with normal logs. No more scrolling page after page to find a stack trace. With _Microlog_, they appear as easy-to-see stop signs:

![Log entries in the status bar](https://github.com/micrologai/microlog/raw/main/microlog/images/error-log.png)

## Formatting Logs with Markdown

Log entries can be formatted using Markdown to make it easier to show important information to the reader.

![Using markdown for log entries](https://github.com/micrologai/microlog/raw/main/microlog/images/markdown.png)

# Logging 

_Microlog_ detects calls to `print` and `logging`. Those calls are automatically intercepted
added to the _Microlog_ event log.  

Manual log entries can be inserted into Microlog using `info`, `warn`, `debug`, and `error`:

```python
   print("Add a log entry to microlog with an info marker...")
   print("... or as an error marker.", stream=sys.stderr)

   import logging
   logger = logging.Logger("Microlog Demo")

   logger.info("Add a log entry to microlog with an info marker...")
   logger.debug("... or a bug marker...")
   logger.warning("... or a warning marker...")
   logger.error("... or an error marker.")
   
   microlog.info("Add something to the log explicitly...")
   microlog.warning("... as a warning...")
   microlog.debug("... as a debug message...")
   microlog.error("... as an error.")
```

# Design

The Design tab analyzes the runtime call graph and draws a structural diagram of the underlying design of your application.
Here is an example for `examples\go.py`:

![Microlog's innovative design graph](https://github.com/micrologai/microlog/raw/main/microlog/images/design-go.png)

# Log

The log tab contains a chronological listing of all print and logging output, statistics, and analysis performed by _Microlog_ in a more traditional linear log style:

![Microlog's traditional log, with a twist](https://github.com/micrologai/microlog/raw/main/microlog/images/log.png)

The links shown in lightblue directly take you to the source file where the print took place. This makes it extremely easy to figure out what code prints what exactly. For the `files.py` example, the log shows that this program leaked one file descriptor. That same report is also shown in the timeline when you click at the warning icon at the end of the run. 
The popup also shows a link to the source location where the file was opened:

![Detecting leaked file descriptors](https://github.com/micrologai/microlog/raw/main/microlog/images/fd-leak.png)

## Log - Memory Leaks

In addition to checking for leaked file descriptors, _Microlog_ aims to detect memory leaks. Those objects that were
allocated but cannot be garbage-collected as they are either reachable from a module or are involed in a reference cycle that
cannot be broken. The following report shows the top-10 offenders for the `dataframes.py` example, that uses Pandas dataframes.

![Detecting memory leaks](https://github.com/micrologai/microlog/raw/main/microlog/images/memory-leak.png)

# Explanation

The explanation tab shows a human-language explanation provided by OpenAI's `ChatGPT` to explain the design and implementation behind the application being monitored by _Microlog_. This analysis is not performed on the source code, but on a condensed call graph generated from the performance log that was recorded by _Microlog_. Here is an example of the what `ChatGPT` thinks of
our `examples\go.py` execution:

![ChatGPT's simple explanation of complex Python code](https://github.com/micrologai/microlog/raw/main/microlog/images/chatgpt.png)

# Tips

To discover best practices, performance tips, or tutorials for modules being used by the application, _Microlog_ offers quick
links to general information sources, such as search engines and Q&A sites:

![Tips make you a better Python developer](https://github.com/micrologai/microlog/raw/main/microlog/images/tips.png)


# Developer Notes

## Run all unit tests

```
python3 -m unittest discover tests
```


## Upload new version to PyPi

First build the package into a source distribution and a Python wheel:
```
python3 -m pip install --user --upgrade setuptools wheel twine build
python3 -m build --sdist
python3 -m build --wheel
```

Then verify whether the build works for pypi:
```
twine check dist/*
```

Then upload to the pypi test environment:
```
twine upload --repository pypitest dist/*
```

If that looks fine, upload to the real pypi environment:
```
twine upload dist/*
```

# License



## Run all examples

```
sh examples/runall.sh
```

# License

_Microlog_ is released under version 1 of the [Server Side Public License (SSPL)](LICENSE).
