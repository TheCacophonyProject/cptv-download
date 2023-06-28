import queue
import threading


class Pool:
    """
    Simple worker thread pool
    """

    def __init__(self, num_workers, run, *args):
        self._q = queue.Queue()
        args = (self._q,) + args
        self._threads = []
        for _ in range(num_workers):
            t = threading.Thread(target=run, args=args)
            t.start()
            self._threads.append(t)

    def put(self, item):
        self._q.put(item)

    def stop(self):
        self._q.join()

        for _ in self._threads:
            self._q.put(None)
        for t in self._threads:
            t.join()

    def wait(sef):
        self._q.join()
