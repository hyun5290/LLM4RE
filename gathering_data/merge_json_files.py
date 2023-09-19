import json
import os
import natsort

JSON_FILENAME = ("dataset/on_playstore.json", "dataset/not_on_playstore.json")
JSON_FILE_DIRECTORY = "dataset/playstore_temp/"

def merge(jf1, jf2):
    for key in jf2.keys():
        if key in jf1:
            jf1[key].update(jf2[key])
        else:
            jf1[key] = jf2[key]

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

    if "error" in jf and not jf["error"]:
        del jf["error"]
    if "error" in jf["count"] and not jf["count"]["error"]:
        del jf["count"]["error"]
    if "error" in jf["count"] or "error" in jf:
        raise Exception("Error present")

    new_jf = []
    for key in jf:
        if key == "count": continue
        new_jf.append({"count": len(jf[key]), "links": jf[key]})
    
    for i in range(len(new_jf)):
        print(f"\nWriting to {JSON_FILENAME[i]}...", end='')
        with open(JSON_FILENAME[i], 'w+') as f:
            json.dump(new_jf[i], f, indent=2)
        print(f"Done")

if __name__ == '__main__':
    main()