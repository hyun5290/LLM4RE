import json
import sys

INPUT_FILENAME = "dataset/not_on_playstore.json"
OUTPUT_FILENAME = ("dataset/not_on_playstore-", ".json")

def main():
    print(f"Reading {INPUT_FILENAME}...", end='')
    with open(INPUT_FILENAME, 'r') as f:
        jf = json.load(f)
    print(f"Done")
    
    for i in range(int(sys.argv[1])):
        print(f"Writing to {OUTPUT_FILENAME[0] + str(i + 1) + OUTPUT_FILENAME[1]}...", end='')
        new_jf = {"count": 0}
        for key in jf:
            if isinstance(jf[key], dict):
                new_jf[key] = dict(list(jf[key].items())[i * (len(jf[key]) // int(sys.argv[1])):(i + 1) * len(jf[key]) // int(sys.argv[1])])
                new_jf["count"] = len(new_jf[key])
        with open(OUTPUT_FILENAME[0] + str(i + 1) + OUTPUT_FILENAME[1], 'w+') as f:
            json.dump(new_jf, f, indent=2)
        print(f"Done")

if __name__ == '__main__':
    main()