import queue


class StudentRequestQueue:
    def __init__(self):
        self.request_queue = queue.Queue()

    def add_request(self, student, course):
        try:
            self.request_queue.put((student, course), False)
            return True
        except queue.Full as e:
            print(e)
            return False

    def get_all_pending_requests(self):
        pending_requests = []
        try:
            while not self.request_queue.empty():
                pending_request = self.request_queue.get(False, 1)
                pending_requests.append(pending_request)
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

    for request in q.get_all_pending_requests():
        print(request)

    print("Queue empty at the end? {}".format([] == q.get_all_pending_requests()))
