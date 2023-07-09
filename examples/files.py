#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

# 
# Microlog detects files that are opened, but never closed. 
# They are listed as a warning in the statusbar, at the end of the Timeline.
#
this_file_is_never_closed = open(__file__)

# 
# When a file is closed explicitly, no warning is generated.
#
this_file_is_correctly_closed = open(__file__)
this_file_is_correctly_closed.close()

# 
# Files that are opened with a context manager are safe.
#
with open(__file__) as this_file_is_always_closed:
    pass