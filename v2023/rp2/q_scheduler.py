import heapq


""" Task Scheduler with Function-Queue method
    First, I created this for my micropython project. It can be used in python too but there are better options.

    FunctionQueueTask      -> Class for create Task
    FunctionQueueScheduler -> Class for Task Scheduler

    How to use:
        1) Create scheduler first by using FunctionQueueScheduler class

            s = FunctionQueueScheduler()

        2) Create task(s) by using FunctionQueueTask class

            t = FunctionQueueTask(<task function>, <task ID>, s)
            <task function> : function of that task to run whenever scheduler called the task
            <task ID> : task number. scheduler will use Min-Heap as function queue,
                        to select which task is needed to be run first.
                        So, Least ID number means most Task Priority
            s : scheduler from 1)

        3) Install task(s) from 2) into scheduler by

            s.installTask(t1)   # task 1
            s.installTask(t2)   # task 2
            s.installTask(t3)   # task 3
                .
                .
                .

        4) To put task in scheduler's queue, Call s.pushTask(<task ID>)
            Or task can be put automatically by binding t.handler to the callback function of HW interrupt
            (Timer, GPIO etc.)

        5) Call s.popTask() in main loop. If there are task(s) in the queue, It will be run immediately.

"""
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


