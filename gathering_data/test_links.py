import requests
import json
import pandas  # for reading csv file
from multiprocessing import Process, shared_memory
import os
import time

CSV_FILENAME = "dataset/Google-Playstore.csv"
JSON_FILENAME = ("dataset/playstore_temp/list_validity_", ".json")
PLAYSTORE_URL = 'https://play.google.com/store/apps/details?id='
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
START, END = 2, 2312945  # line number in CSV to start and end, both ends inclusive
JSON_FILE_SIZE = 5000  # how many items per json file
WRITE_FREQUENCY = 200  # update json every WRITE_FREQUENCY items
PROCESS_CHECK_FREQUENCY = 60  # how often to check if processes alive in seconds
NUM_PROCESSES = 8  # number of child processes to run

# check if app_id is available on Play Store
def check(app_id):
    url = PLAYSTORE_URL + app_id
    print(f"Opening: {app_id}...", end="")
    try:
        r = requests.get(url, headers=HEADERS)
        return int(r.status_code == 200)  # 404 if app not on store anymore
    except Exception as e:
        return type(e), e

def get_json_filename(ind):
    return f"{JSON_FILENAME[0]}{str(ind // JSON_FILE_SIZE * JSON_FILE_SIZE)}-{str((ind // JSON_FILE_SIZE + 1) * JSON_FILE_SIZE - 1)}{JSON_FILENAME[1]}"

class TestLinks:
    def __init__(self, csv_filename, shm_name):
        self.csv_content = pandas.read_csv(csv_filename)
        self.jf = {}
        self.shm = shared_memory.SharedMemory(name=shm_name)

    # given a line in csv, return app name, app id, and price
    def get_app_info(self, csv_line):
        return self.csv_content["App Name"][csv_line - 2], self.csv_content["App Id"][csv_line - 2], self.csv_content["Price"][csv_line - 2]

    def write_to_json(self, filename):
        self.jf["count"]["valid_links"] = len(self.jf["valid_links"])
        self.jf["count"]["invalid_links"] = len(self.jf["invalid_links"])
        self.jf["count"]["error"] = len(self.jf["error"])
        with open(filename, 'w+') as outfile:
            json.dump(self.jf, outfile, indent=2)

    def read_from_json(self, filename):
        try:
            with open(filename, 'r') as f:
                self.jf = json.load(f)
        except FileNotFoundError:
            self.jf = {"count": {"valid_links": 0, "invalid_links": 0, "error": 0}, "valid_links": {}, "invalid_links": {}, "error": {}}

    def test_links(self, r, child_num):
        self.read_from_json(get_json_filename(r[0]))
        pid = os.getpid() % 100
        print(f"\nPID: {pid} entering...\n")
        for i in range(r[0], r[1]):
            app_name, app_id, app_price = self.get_app_info(i)
            if app_id in self.jf["valid_links"] or app_id in self.jf["invalid_links"] or app_id in self.jf["error"]: continue
            if self.shm.buf[child_num] == 0b11111111: self.shm.buf[child_num] = 0
            self.shm.buf[child_num] += 1
            print(f"PID: {pid}\tLine: {i}\t", end='')
            code = check(app_id)
            if code == 1:
                print("Success")
                self.jf["valid_links"][app_id] = {"name": app_name, "csv_line": i, "price": app_price}
            elif code == 0:
                print("Failed")
                self.jf["invalid_links"][app_id] = {"name": app_name, "csv_line": i, "price": app_price}
            else:
                print("Error")
                self.jf["error"][app_id] = {"name": app_name, "csv_line": i, "price": app_price, "error_type": str(code[0]), "error_msg": str(code[1])}
            if i % WRITE_FREQUENCY == 0:
                self.write_to_json(get_json_filename(r[0]))
                print(f"PID: {pid}\tLine: {i}\tOverwriting: {get_json_filename(r[0])}")
        self.write_to_json(get_json_filename(r[0]))
        print(f"\nPID: {pid} exiting...\n")

def main():
    range_lst = [START] + [i * JSON_FILE_SIZE for i in range(START // JSON_FILE_SIZE + 1, END // JSON_FILE_SIZE + 1)] + [END + 1]
    range_lst = [(range_lst[i], range_lst[i + 1]) for i in range(len(range_lst) - 1)]  # list of tuples with ranges
    shm = shared_memory.SharedMemory(create=True, size=NUM_PROCESSES)
    t = TestLinks(CSV_FILENAME, shm.name)
    children = []
    i = 0

    # initialize processes
    while len(children) < min(NUM_PROCESSES, len(range_lst)):
        print(f"\nStarting process with {range_lst[i]}...\n")
        child = Process(target=t.test_links, args=(range_lst[i],len(children),))
        child.start()
        i += 1
        # if process is over in 0.5s, start another process
        time.sleep(0.5)
        child.join(timeout=0)
        if not child.is_alive(): continue
        children.append([child, range_lst[i - 1]])

    while i < len(range_lst):
        time.sleep(PROCESS_CHECK_FREQUENCY)
        print('\n')
        for j in range(len(children)):
            children[j][0].join(timeout = 0)
            print(f"{children[j][0]} is working on {children[j][1]}, Iterations: {shm.buf[j]}")
            # done with that range, start another process
            if not children[j][0].is_alive():
                print(f"Starting new process with {range_lst[i]}...")
                children[j] = [Process(target=t.test_links, args=(range_lst[i],j,)), range_lst[i]]
                children[j][0].start()
                i += 1
            # process didn't do anything this cycle, terminate and start another
            elif shm.buf[j] == 0:
                print(f"Terminating {children[j][0]}...")
                children[j][0].terminate()
                time.sleep(0.1)
                print(f"Starting new process with {children[j][1]}...")
                children[j][0] = Process(target=t.test_links, args=(children[j][1],j,))
                children[j][0].start()
            shm.buf[j] = 0
        print('\n')
    
    shm.close()
    shm.unlink()

if __name__ == '__main__':
    main()
