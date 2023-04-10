# microlog

Microlog is an AI-driven approach to observability and monitoring.

# Installing Microlog

```bash
  git clone https://github.com/laffra/microlog
```

# Enabling Microlog

```python
  import microlog

  microlog.start(
      application="Example",
      version=1.0,
      info="Just testing",

      showInBrowser=True,   # this loads the local log in the browser when finished
      verbose=True,         # this prints out statistics about microlog
  )
``` 

That's all you need to do to get going. Microlog is an AI-driven monitoring solution that 
will observe your code while it is running, analyze the metrics, and produce easy to use 
dashboards for observing the health of your system, set SLOs, and register alerts.

# Logging 

Manual log entries are inserted into microlog using `info`, `warn`, `debug`, and `error`:

```python
   microlog.info("add something to the log")
```

# Tracing 

Functions and methods can be traced with microlog using the `@trace` decorator:

```python
   @microlog.trace
   def someFunction():
       pass
```

# An Example

The Microlog UI consist of four main sections: a status bar, a timeline, a flame graph, and spans. The status bar shows general information about the process and manually created log entries. The flame graph is generated automatically by microlog, without needing any instrumentation in the code. Finally, the span view show functions or methods that were annotated manually.

![Example run of microlog](images/overview.png)

Using the mouse, the dashboard can be panned and zoomed. More details will be shown when zoomed in deeper:

![Example run of microlog](images/zoomedin.png)

When hovering over a call, details are shown. In the case below, microlog detected four anomalies. Each took longer than average. The current call is also an anomaly:
 - It took almost 6 seconds, whereas the average is below 4 seconds. 
 - The top bar shows the CPU consumption during the call which is suspiciously low for about 1.5 seconds. 
 - All this resulted in the total CPU consumption during the call to be below 66%. 
 - For around 33% of the time, the process was waiting. Typically, this indicates bottlenecks elsewhere in the system, such as having to wait for data to arrive from a micro-service. 

 Automatic anomaly detection, call stack analysis, and process health indicators offered by Microlog allow us to quickly debug perfomance issues.

![Example run of microlog](images/dialog.png)

The top bar shows general statistics for the process, such as CPU and number of modules:

![Microlog logs](images/status.png)

Log entries are shown as visual markers in the top bar. Because Microlog shows log entries on the timeline, analyzing problems becomes much easier than with normal logs. No more scrolling page after page to find a stacktrace. With Microlog they appear as easy to see stop signs:

![Microlog logs](images/error-log.png)

Functions and methods can be traced. These traced spans are positioned along the timeline and are shown at the bottom. Parameters to the function or method being traced are automatically extracted by Microlog and added to the log:

![Microlog logs](images/span.png)

