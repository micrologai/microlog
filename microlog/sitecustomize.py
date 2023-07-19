#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

def install_microlog_as_a_continuous_profiler():
    try:
        import psutil
        try:
            import logging
            import microlog

            logging.Logger("Microlog").info("Microlog has been enabled in", __file__)
            microlog.start()
        except:
            import traceback
            traceback.print_exc()
    except:
        pass # do not run microlog if psutil is not installed


install_microlog_as_a_continuous_profiler()
