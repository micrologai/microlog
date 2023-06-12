#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

def install_microlog_as_a_continuous_profiler():
    import logging
    import microlog

    logging.Logger("Microlog").info("Microlog has been enabled in", __file__)


    microlog.start()


install_microlog_as_a_continuous_profiler()
