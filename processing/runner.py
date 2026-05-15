from multiprocessing import Pool

def run_parallel(tasks, worker, num_workers):
    with Pool(num_workers) as pool:
        return pool.map(worker, tasks)