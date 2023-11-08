from app import *
import time

start_time = time.time()
selfscan_cron(None,None)
print("Runtime of function: --- %s seconds ---" % (time.time() - start_time))