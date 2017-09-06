# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 10:03:53 2017

@author: x
"""
#%%
import os
import cv2
import time
import numpy as np
import pandas as pd
from tag_recognition.preprocess \
    import getResizedImage, getEnhancedImage, getDeskewedImage
from tag_recognition.json_analyze import json_result
from tag_recognition.gcv_api import gcv_result


#%% config upload directory and apikey
app_config = dict()
app_config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '/upload'
with open('.apikey', 'r') as f:
    app_config['API_KEY'] = f.read()


#%% set id rules
id_rule_dict = {
    'BEAMS': [2, 2, 4, 3, 2, 2],
    'OWD': [12],
    'SHIPS': [3,2,4,4],
    'TML': [2,2,2,7],
    'UA': [4,3,4,4],
    'Sanyo': [5, 3, 2],
    'alcali': [11],
    'CONVERSE TOKYO': [11],
    'Liess': [11],
    'martinique': [11],
    'MENS MELROSE': [10],
    'Soffitto': [10],
    'Unknown13': [13]
}


#%% get objective images
file_dir = app_config['UPLOADED_PHOTOS_DEST']
file_list = os.listdir(file_dir)


### add filter rules here to filter specific files !!!
file_list = list(filter(lambda s: '.json' not in s and \
                        'maxHeight' not in s and \
                        '_proc' not in s and \
                        '.git' not in s, file_list))
res_li = []
res = {'Origin': [],
       'ID': '',
       'FullText': '',
       'Percent': [],
       'Material': [],
       'Part': [],
       'Filename': ''}
# result format:
# res -> dict
# res_li -> list: [res, res, res, ...]
# res_df = pd.DataFrame(res_li)


#%% iteratively process
cnt = 0
for fullname in file_list:
    file_name, file_ext = os.path.splitext(fullname)


    ## preprocessing
    # 1. adjust brightness
    image_proc = getEnhancedImage(file_dir + '/' + file_name + file_ext)
    # 2. adjust image angle
    image_proc = getDeskewedImage('', image_proc)
    # 3. resize image
    image_proc = getResizedImage('', image_proc,
                                 maxHeight=900)


    ## save the processed image
    cv2.imwrite(file_dir + '/' + file_name + '_proc' + file_ext,
                image_proc)
    del image_proc
    fname_proc = file_name + '_proc'
    fname_json = fname_proc + file_ext + '.json'


    # if no json file for the image uploaded, call google vision api
    if fname_json not in os.listdir(file_dir):
        gcv_result(file_dir + '/' + fname_proc + file_ext,
                   api_key=app_config['API_KEY'])


    # analyze json to get info of image
    res = json_result(fname_json, id_rule_dict['UA'], file_dir)


    # res['ID']: (score, ID) # get ID by res['ID'][1]
    res['ID'] = res['ID'][1] if res['ID'] != '' else ''
    res['Filename'] = fname_proc
    res_li.append(res)
    time.sleep(0.01)
    print('Finished!', fname_proc)
    cnt += 1


res_df = pd.DataFrame(res_li)
# save result to excel
#res_df.to_excel('json_anal_result.xlsx')
del res, res_li
