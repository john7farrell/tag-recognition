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
part_set = set(material_df.part)
part_set.remove('.')
part_set.remove('91')
part_set.remove('C/♯7931')
part_set.remove('GRAY')
part_set.remove('WHITE')
part_set.remove('本体')
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
        # skip the first several strings if they are lower-case (rare in ID)
        while start_idx < len(li) and li[start_idx].islower():
            start_idx += 1
        li = li[start_idx:]
        li = li.upper()
        # filter specific keywords
        if 'NO.' in li:
            li = li.split('NO.')[1].strip()
        elif 'NO' in li:
            li = li.split('NO')[1].strip()
        elif 'NUMBER' in li:
            li = li.split('NUMBER')[1].strip()
        elif 'STYLE' in li:
            li = li.split('STYLE')[1].strip()
        # re-connect by '-'
        li = '-'.join(li.split(' '))
        digit_nb = sum(list(map(str.isdigit, list(li))))
        # if less than 3 numbers, set to ''
        if digit_nb < 3:
            li = ''
        if '$' in li:
            li = ''
        li = ''.join(re.findall('[a-zA-Z0-9 -]', li))
        # split by '-'
        li_split = li.split('-')
        #print(0,li_split)
        if ' ' in li_split[-1]:
            li_split_last = li_split[-1].split(' ')[0]
            li_split[-1] = li_split_last
            #print(1,li_split)
        if len(li_split[-1]) > id_msk[-1]:
            li_split_last = li_split[-1][:id_msk[-1]]
            li_split[-1] = li_split_last
            #print(2,li_split)
        # padding 0 if shorter than id_msk
        if len(li_split) < sum(id_msk):
            li_split = li_split + ['0'] * (sum(id_msk) - len(li_split))
        else:
            li_split = li_split[:len(id_msk)]
        li_split = li_split[:len(id_msk)]
        #print(3,li_split)
        li_len = list(map(len, li_split))
        # calculate length difference (mse) of different parts
        mse = lambda liLen: np.mean([abs(liLen[i] - id_msk[i])
                                         for i in range(min(len(liLen), len(id_msk)))])
        #print(mse(li_len), li_split)
        return mse(li_len), '-'.join(li_split)
    res_li = [check_line(s) for s in fullText_split_n]
    mse_li = [res[0] for res in res_li]
#    print(res_li)
    slct_id = np.argmin(mse_li)
    return res_li[slct_id]
#%%


def getOrigin(fullText):
    fullText_split_n = fullText.split('\n')
    def check_line(line):
        line = line.upper()
        line = ''.join(line.split(' '))
        if 'MADEIN' in line:
            return 'MADE IN ' + line.split('MADEIN')[1]
        elif 'ADEIN' in line:
            return 'MADE IN ' + line.split('ADEIN')[1]
        else:
            return ''
    res_li = [check_line(s) for s in fullText_split_n]
    fullText = fullText.replace('\n', ' ')
    fullText = fullText.replace('　', ' ')
    fullText_split = fullText.split(' ')
    # loop in terms of fulltext, check if in origin set
    for term in fullText_split:
        term = term.strip('0123456789%')
        if term in origin_set or term.split('製')[0] in origin_set:
            res_li.append(term)
    origin_cnt = 0
    # loop in terms of origin set, check if in fulltext
    for origin in origin_set:
        if origin in fullText:
            origin_cnt += 1
            res_li.append(origin + '製')
    res_li = list(set(filter(lambda x: x != '', res_li)))
    res_li2 = []
    # merge / delete replica
    for res in res_li:
        if '製' not in res:
            res_li2.append(res + '製')
        else:
            res_li2.append(res)
    res_li = list(set(res_li2))
    return res_li


def getPartMaterial(fullText):
    fullText = fullText.replace('％', '%')
    fullText = fullText.replace('　', ' ')
    fullText = fullText.replace('\n', ' ')
    fullText_split = fullText.split(' ')
    fullText_split = list(filter(lambda s: s != '', fullText_split))
    part_res = []
    material_res = []
    percent_res = []
    digit_percent = lambda s: re.compile('\d+%').findall(s)
    digit_percent_res = digit_percent(fullText)
    for term_raw in fullText_split:
        term = term_raw.strip('0123456789%')
        if term in part_set:
            part_res.append(term)
        if term in material_set and term not in part_set:
            material_res.append(term)
            if digit_percent_res != []:
                pct = digit_percent_res.pop(0)
                if pct == '00%':
                    pct = '100%'
                percent_res.append(term+pct)
            else:
                percent_res.append(term+'?%')
    if digit_percent_res != []:
        for pct in digit_percent_res:
            percent_res.append('?'+pct)
    res = {'part': list(set(part_res)),
           'material': list(set(material_res)),
           'percent': percent_res}
    return res


def json_result(jsonname, id_msk=[13], jsondir='upload'):
    assert '.json' in jsonname, 'Please select a json file!'
    assert 'proc' or 'maxHeight' in jsonname, 'Please use resized image!'
    try:
        fullText = getFullText(load_json(jsondir+'/'+jsonname))
    except KeyError as k_err:
        print("Key error: {0}".format(k_err))
        print('Set fullText to null')
        fullText = 'null'
    except:
        print("Unexpected error:", sys.exc_info()[0])
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
