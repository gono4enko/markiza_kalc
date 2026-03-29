import os

bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

loglevel = "debug"
accesslog = "/var/log/awning-calculator/access.log"
errorlog = "/var/log/awning-calculator/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

preload_app = True
