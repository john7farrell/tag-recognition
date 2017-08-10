# -*- coding: utf-8 -*-
"""@author: mat.xi
"""

import re
import os
import sys
import json
import numpy as np
import pandas as pd
#from collections import OrderedDict

#print(os.getcwd())
brand_msk_pairs = [('default',[13])]
origin_df = pd.read_excel('./tag_recognition/origin_df.xlsx')
origin_set = set([s[:-1] for s in list(origin_df['origin'])])
origin_set.remove('輸入衣料')
material_df = pd.read_excel('./tag_recognition/material_new_df.xlsx')
part_set = set(material_df.part);
part_set.remove('.')
material_set = set(material_df.material)


def load_json(filename):
    with open(filename) as data_file:
        fdata = data_file.read()
        data = json.loads(fdata)
    return data

def getFullText(data_json):
    return data_json['fullTextAnnotation']['text']


def getId(fullText, id_msk):
    fullText_split_n = fullText.split('\n')
    def check_line(li):
        start_idx = 0
        while start_idx < len(li) and li[start_idx].islower():
            start_idx += 1
        li = li[start_idx:]
        li = li.upper()
        if 'NO.' in li:
            li = li.split('NO.')[1].strip()
        elif 'NO' in li:
            li = li.split('NO')[1].strip()
        elif 'NUMBER' in li:
            li = li.split('NUMBER')[1].strip()
        elif 'STYLE' in li:
            li = li.split('STYLE')[1].strip()
#        print(li)
#        print(brand_dir)
        li = ''.join(li.split(' '))
        digit_nb = sum(list(map(str.isdigit, list(li))))
        if digit_nb < 3:
            li = ''
        if '$' in li:
            li = ''
        li = ''.join(re.findall('[a-zA-Z0-9 -]', li))
        li_split = li.split('-')
        if len(li_split) < sum(id_msk):
            li_split = li_split + ['0'] * (sum(id_msk) - len(li_split))
        else:
            li_split = li_split[:len(id_msk)]
        li_len = list(map(len, li_split))
        mse = lambda liLen: np.mean([abs(liLen[i] - id_msk[i])
                                         for i in range(min(len(liLen), len(id_msk)))])
        return mse(li_len), li
    res_li = [check_line(s) for s in fullText_split_n]
    mse_li = [res[0] for res in res_li]
#    print(res_li)
    slct_id = np.argmin(mse_li)
    return res_li[slct_id]
#%%


def getOrigin(fullText):
    fullText_split_n = fullText.split('\n')

    def check_line(line):
        #        line_raw = str(line)
        line = line.upper()
        line = ''.join(line.split(' '))
        if 'MADEIN' in line:
            return 'MADE IN ' + line.split('MADEIN')[1]
        elif 'ADEIN' in line:
            return 'MADE IN ' + line.split('ADEIN')[1]
        # elif len(line) > 1 and '製' in line[1:] and len(line) < len('MADEINAMERICA'):
        #            return line_raw
        #        elif '産地' in line:
        #            return line_raw
        #        elif '原産国' in line:
        #            return line_raw
        else:
            return ''

    res_li = [check_line(s) for s in fullText_split_n]
    # res_li = list(set(filter(lambda x: x != '', res_li)))

    fullText = fullText.replace('\n', ' ')
    fullText = fullText.replace('　', ' ')
    fullText_split = fullText.split(' ')
    for term in fullText_split:
        term = term.strip('0123456789%')
        if term in origin_set or term.split('製')[0] in origin_set:
            res_li.append(term)
    res_li = list(set(filter(lambda x: x != '', res_li)))
    return res_li


def getPartMaterial(fullText):
    fullText = fullText.replace('％', '%')
    fullText = fullText.replace('　', ' ')
    fullText = fullText.replace('\n', ' ')
    fullText_split = fullText.split(' ')
    part_res = []
    material_res = []
    for term in fullText_split:
        term = term.strip('0123456789%')
        if term in part_set:
            part_res.append(term)
        if term in material_set and term not in part_set:
            material_res.append(term)

    digit_percent = lambda s: re.compile('\d+%').findall(s)
    digit_percent_res = digit_percent(fullText)

    return {'part': list(set(part_res)),
            'material': list(set(material_res)),
            'percent': list(set(digit_percent_res))
            }


def json_result(jsonname, id_msk=[13], jsondir='upload'):
    assert '.json' in jsonname, 'Please select a json file!'
    assert 'maxHeight' in jsonname, 'Please use resized image!'
    try:
        fullText = getFullText(load_json(jsondir+'/'+jsonname))
    except KeyError as k_err:
        print("Key error: {0}".format(k_err))
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        print('Set fullText to null')
        fullText = 'null'
    res = dict()
    res['FullText'] = fullText
    res['ID'] = getId(fullText, id_msk)
    res['Origin'] = getOrigin(fullText)
    pm_res = getPartMaterial(fullText)
    res['Part'] = pm_res['part']
    res['Material'] = pm_res['material']
    res['Percent'] = pm_res['percent']
    return res
