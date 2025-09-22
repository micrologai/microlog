import logging
import time


def worker():
    logging.info("Worker started")
    for i in range(15):
        logging.debug(f"Working on item {i}")
        time.sleep(0.5)
    logging.info("Worker finished")


if __name__ == "__main__":
    from multiprocessing import Process

    processes = []
    for _ in range(3):
        p = Process(target=worker)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    logging.info("All workers completed")
