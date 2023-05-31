Summarize what my program does. It generates the following call graph:
matplotlib calls numpy.concatenate
matplotlib calls pyparsing.parse_string
matplotlib calls pyparsing.parse_string
matplotlib calls genericpath.exists
pyparsing calls matplotlib.symbol
pyparsing calls matplotlib.math_string
pyparsing calls traceback.extract_stack
matplotlib calls posixpath.realpath
matplotlib calls copy.copy
calls numpy.histogram
calls pandas.sort_values
matplotlib calls numpy.concatenate
matplotlib calls numpy.column_stack
pandas calls matplotlib.get_position
pandas calls matplotlib.inner
pandas calls matplotlib.get_majorticklabels
matplotlib calls numpy.sort
matplotlib calls numpy.vstack
matplotlib calls numpy.concatenate
pandas calls matplotlib.add_subplot
ipykernel calls zmq.flush
matplotlib calls PIL.save
IPython calls matplotlib.print_figure
decorator calls IPython.catch_format_error
IPython calls decorator.fun
matplotlib_inline calls IPython.display
IPython calls matplotlib_inline.flush_figures
IPython calls matplotlib._draw_all_if_interactive
matplotlib calls numpy.dot
squarify calls matplotlib.inner
matplotlib calls numpy.column_stack
calls squarify.plot
matplotlib calls genericpath.isfile
calls matplotlib.loglog
contextlib calls matplotlib._open_file_or_url
matplotlib calls inspect.getdoc
calls folderstats.folderstats
IPython calls .ipykernel_launcher
jupyter_client calls ipykernel.send_multipart
ipykernel calls jupyter_client.send
ipykernel calls zmq.send
ipykernel calls threading.wait
asyncio calls ipykernel.dispatch_queue
asyncio calls selectors.select
ipykernel calls IPython.run_cell
IPython calls traitlets.inner
platform calls subprocess.check_output
pkg_resources calls genericpath.isdir
re calls sre_compile.compile
linecache calls tokenize.open
traceback calls linecache.getline