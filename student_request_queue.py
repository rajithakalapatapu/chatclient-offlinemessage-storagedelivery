"""
Name: Venkata Adilakshmi Rajitha Kalapatapu
Student ID: 1001682465
Login ID: vxk2465
"""

import queue


class StudentRequestQueue:
    def __init__(self):
        # Start a queue
        self.request_queue = queue.Queue()

    def add_request(self, student, course):
        try:
            # store incoming data into the queue
            # store it asynchronously - queue takes care of locks
            self.request_queue.put((student, course), False)
            return True
        except queue.Full as e:
            print(e)
            return False

    def get_all_pending_requests(self):
        pending_requests = []
        try:
            # as long as queue has items, get data
            while not self.request_queue.empty():
                # get data asynchronously - queue takes care of locks
                # if there's no data throw queue.Empty error within 1 second
                pending_request = self.request_queue.get(False, 1)
                # store it in a list to be returned
                pending_requests.append(pending_request)
                # remove item from task
                self.request_queue.task_done()
        except queue.Empty as e:
            print("Nothing to return at the moment")
            return pending_requests
        except ValueError as e:
            print("We had more tasks done than tasks in the queue")
            return pending_requests

        return pending_requests


if __name__ == "__main__":
    q = StudentRequestQueue()
    q.add_request("student1", "course1")
    q.add_request("student1", "course2")
    q.add_request("student2", "course2")

    print(q.get_all_pending_requests())

    print("Queue empty at the end? {}".format([] == q.get_all_pending_requests()))
