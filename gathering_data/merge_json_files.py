import json
import os
import natsort

JSON_FILENAME = ("gathering_data/", "list_validity.json")
JSON_FILE_DIRECTORY = "gathering_data/dataset/"

def merge(jf1, jf2):
    for key in jf1:
        if isinstance(jf1[key], dict) and key in jf2:
            merge(jf1[key], jf2[key])
            jf1[key].update(jf2[key])

def main():
    jf = {}
    for filename in natsort.os_sorted(os.listdir(JSON_FILE_DIRECTORY)):
        if filename.endswith(".json") and filename != JSON_FILENAME[1]:
            print(f"Merging {filename}...", end='')
            with open(JSON_FILE_DIRECTORY + filename, 'r') as f:
                if jf:
                    merge(jf, json.load(f))
                else:
                    jf = json.load(f)
            print(f"Done")
    for key in jf["count"]:
        
    print(f"\nWriting to {JSON_FILENAME[0] + JSON_FILENAME[1]}...", end='')
    with open(JSON_FILENAME[0] + JSON_FILENAME[1], 'w+') as f:
        json.dump(jf, f, indent=2)
    print(f"Done")

if __name__ == '__main__':
    main()