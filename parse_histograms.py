import json
import os
from argparse import ArgumentParser
from os.path import join, exists
from time import sleep

import requests


class API:
    _URL = os.environ["URL"]
    _TASK_URL = _URL + "task"
    _HEALTHCHECK_URL = _URL + "healthcheck"
    _RESULTS_URL = _URL + "results"
    _STOP_URL = _URL + "stop"
    _UPLOAD_URL = _URL + "upload"

    @staticmethod
    def task(uuid: str, id: str, filename: str):
        response = requests.post(API._TASK_URL, json={"uuid": uuid, "version": "1", "id": id,
                                                      "file": filename, "is_part": True})
        return response

    @staticmethod
    def healthcheck():
        response = requests.get(API._HEALTHCHECK_URL)
        return response

    @staticmethod
    def results():
        response = requests.get(API._RESULTS_URL)
        return response

    @staticmethod
    def stop():
        response = requests.post(API._STOP_URL)
        return response

    @staticmethod
    def upload(file_path: str, user_id: str):
        response = requests.post(API._UPLOAD_URL, files={"file": open(file_path, "rb")}, headers={"User-Id": user_id})
        return response


def collect_histograms(models_dir: str, save_dir: str):
    API.stop()
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    user_id = os.environ["USER_ID"]
    available_models = set(full_name[:-5] for full_name in os.listdir(save_dir))
    for i, model_name in enumerate(sorted(os.listdir(models_dir))):
        print(f"{i + 1}. Starting {model_name}")
        if model_name[:-4] in available_models:
            print(f"Already uploaded. Skipped.")
            continue

        model_path = join(models_dir, model_name)
        upload_response = API.upload(model_path, user_id)
        if upload_response.ok:
            upload_response = json.loads(upload_response.content)
            task_response = API.task(**upload_response)

            if task_response.ok:
                done = False
                while not done:
                    completed = False
                    while not completed:
                        healthcheck_response = API.healthcheck()
                        healthcheck_response = json.loads(healthcheck_response.content)
                        completed = healthcheck_response["status"] == "COMPLETED"
                        print(f"Progress: {healthcheck_response['progress']}")
                        sleep(5)

                    results_response = API.results()
                    results_response = json.loads(results_response.content)

                    if (results_response["uuid"] == upload_response["uuid"]) and \
                            (results_response["id"] == upload_response["id"]) and \
                            (results_response["file"] == upload_response["filename"]):
                        done = True
                        results_response["origin_uuid"] = model_name[:-4]
                        with open(join(save_dir, f"{results_response['origin_uuid']}.json"), "w") as file:
                            json.dump(results_response, file, indent=2)
                        print(f"Saved!")
                        print()
                    else:
                        print(f"Сaught results from invalid UUID {results_response['uuid']}")
                        print(f"Start again")

            else:
                print(f"Failed task")
                print()
        else:
            print(f"Not uploaded")
            print()


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--models_dir", type=str, default="./data/models")
    arg_parser.add_argument("--save_dir", type=str, default="./data/histograms")
    args = arg_parser.parse_args()

    paths = [args.models_dir, args.save_idr]
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    collect_histograms(args.models_dir, args.save_dir)
