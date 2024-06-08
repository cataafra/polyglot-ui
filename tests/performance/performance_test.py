from threading import Thread

import requests
import time

import urllib3

LOCAL_URL = "http://localhost:8000"
LOCAL_URL_GPU = "http://localhost:80"
AWS_URL = "https://ec2-16-171-104-203.eu-north-1.compute.amazonaws.com"


def send_request(url, audio_path, language):
    start = time.time()
    speaker_id = 0
    url = url + "/process"

    files = {'file': open(audio_path, 'rb')}
    data = {'language': language, 'speaker_id': str(speaker_id)}
    urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, files=files, data=data, verify=False)

    return time.time() - start


def test_endpoint(iterations, url, audio_path, language):
    process_time = 0
    for i in range(iterations):
        process_time += send_request(url, audio_path, language)
    print(f"--------------------------------------------------------------------\n"
          f"Total time taken: {process_time} seconds. \n"
          f"Average time taken for process: {process_time / iterations} seconds.\n"
          f"--------------------------------------------------------------------\n")


def test_endpoint_with_results(url, audio_path, language, results_list):
    elapsed_time = send_request(url, audio_path, language)
    results_list.append(elapsed_time)


def run_simultaneous_requests():
    threads = []
    results = []
    url = "https://your-url.com"
    audio_path = "sample.wav"
    language = "ron"

    for _ in range(10):  # Number of simultaneous requests
        thread = Thread(target=test_endpoint, args=(url, audio_path, language, results))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_time = sum(results)
    print(f"Total time taken: {total_time} seconds.")
    print(f"Average time taken per process: {total_time / len(results)} seconds.")


def test_local_no_gpu_1():
    """ Test on local with no GPU support. Romanian -> English """
    audio_path = "sample2.wav"
    language = "eng"
    test_endpoint(10, LOCAL_URL, audio_path, language)


def test_local_no_gpu_2():
    """ Test on local with no GPU support. English -> Romanian """
    audio_path = "sample.wav"
    language = "ron"
    test_endpoint(10, LOCAL_URL, audio_path, language)


def test_local_gpu_1():
    """ Test on local with GPU support. Romanian -> English """
    audio_path = "sample2.wav"
    language = "eng"
    test_endpoint(10, LOCAL_URL_GPU, audio_path, language)


def test_local_gpu_2():
    """ Test on local with GPU support. English -> Romanian """
    audio_path = "sample.wav"
    language = "ron"
    test_endpoint(10, LOCAL_URL_GPU, audio_path, language)


def test_aws_no_gpu_1():
    """ Test on AWS with no GPU support. Romanian -> English """
    audio_path = "sample2.wav"
    language = "eng"
    test_endpoint(30, AWS_URL, audio_path, language)


def test_aws_no_gpu_2():
    """ Test on AWS with no GPU support. English -> Romanian """
    audio_path = "sample.wav"
    language = "ron"
    test_endpoint(30, AWS_URL, audio_path, language)


test_aws_no_gpu_1()
test_aws_no_gpu_2()
