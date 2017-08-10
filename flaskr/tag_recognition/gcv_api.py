# -*- coding: utf-8 -*-
"""
json is saved in the same location as the iamges
reference:
=> https://gist.github.com/dannguyen/a0b69c84ebc00c54c94d
"""
from base64 import b64encode
import os
from os import makedirs
from os.path import join, basename
from sys import argv
import json
import requests
import time

ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
RESULTS_DIR = 'jsons'


def make_image_data_list(image_filenames):
    """
    image_filenames is a list of filename strings
    Returns a list of dicts formatted as the Vision API
        needs them to be
    """
    img_requests = []
    for imgname in image_filenames:
        with open(imgname, 'rb') as f:
            ctxt = b64encode(f.read()).decode()
            img_requests.append({
                'image': {'content': ctxt},
                'features': [{
                    'type': 'TEXT_DETECTION',
                    'maxResults': 1
                }]
            })
    return img_requests


def make_image_data(image_filenames):
    """Returns the image data lists as bytes"""
    imgdict = make_image_data_list(image_filenames)
    return json.dumps({"requests": imgdict}).encode()


def request_ocr(api_key, image_filenames):
    response = requests.post(ENDPOINT_URL,
                             data=make_image_data(image_filenames),
                             params={'key': api_key},
                             headers={'Content-Type': 'application/json'})
    return response


def response_proc(response, fnames):
    if response.status_code != 200 or response.json().get('error'):
        print(response.text)
    else:
        for idx, resp in enumerate(response.json()['responses']):
            # save to JSON file
            imgname = fnames[idx]
            jpath = join(imgname + '.json')
            with open(jpath, 'w') as f:
                datatxt = json.dumps(resp, indent=2)
                print("Wrote", len(datatxt), "bytes to", jpath)
                f.write(datatxt)

            # print the plaintext to screen for convenience
            print("---------------------------------------------")
            # t = resp['textAnnotations'][0]
            # print("    Bounding Polygon:")
            # print(t['boundingPoly'])
            # print("    Text:")
            # print(t['description'].encode('utf-8'))


def gcv_result(*image_filenames, api_key):
    # api_key = 'AIzaSyAwrUETKbU8c8zUnMpbaBoEkZSUAdFkYDY'
    if not api_key or not image_filenames:
        print("""
            Please supply one or more image filenames, then api key
            """)
    else:
        max_per_request = 16
        if len(image_filenames) <= max_per_request:
            response = request_ocr(api_key, image_filenames)
            response_proc(response, image_filenames)
        else:
            fnames_queue = [image_filenames[start:start + max_per_request]
                            for start in list(range(0,
                                                    len(image_filenames),
                                                    max_per_request))]
            for fnames_batch in fnames_queue:
                response = request_ocr(api_key, fnames_batch)
                response_proc(response, fnames_batch)
                time.sleep(0.01)
