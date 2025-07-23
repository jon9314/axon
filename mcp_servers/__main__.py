import uvicorn
from multiprocessing import Process
from .filesystem_server import app as fs_app
from .time_server import app as time_app
from .calculator_server import app as calc_app
from .markdown_backup_server import app as md_app
from .github_server import app as gh_app

SERVERS = [
    (fs_app, 9001),
    (time_app, 9002),
    (calc_app, 9003),
    (md_app, 9004),
    (gh_app, 9005),
]

def run(app, port):
    # Listen on all interfaces so the backend container can reach the servers
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    processes = []
    for app, port in SERVERS:
        p = Process(target=run, args=(app, port))
        p.start()
        processes.append(p)
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
