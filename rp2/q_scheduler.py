import heapq



class FunctionQueueTask:
    def __init__(self, task_fn, task_id, scheduler=None):
        self.task_fn = task_fn
        self.task_id = task_id
        self.scheduler = scheduler

    def run(self, **kwargs):
        self.task_fn(**kwargs)

    def handler(self, *args):
        self.scheduler.pushTask(self.task_id)



class FunctionQueueScheduler:
    def __init__(self):
        # heap q?
        self.fq = []
        heapq.heapify(self.fq)
        self.task_dict = {}

    def installTask(self, task):
        self.task_dict[task.task_id] = task.task_fn

    def pushTask(self, task_id):
        heapq.heappush(self.fq, task_id)

    def popTask(self):
        # de-queue the task
        # less task ID -> most task priority
        try:
            task_id = heapq.heappop(self.fq)
            self.task_dict[task_id]()
        except IndexError:
            #print("task empty")
            pass
        except:
            #print("Something went wrong in task scheduler")
            pass


