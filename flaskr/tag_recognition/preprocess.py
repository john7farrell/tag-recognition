# -*- coding: utf-8 -*-
"""
resize to [maxHeight=600]
resized images are saved in the same location as the original images
"""
import cv2
import numpy as np
import pandas as pd
from PIL import Image


def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    # dim = None
    (h, w) = image.shape[:2]
    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image
    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation=inter)
    return resized


def getResizedImage(img_name, img_obj=None,
                    maxHeight=600):
    # if there is an image object, copy and then use it
    if img_obj is not None:
        img = img_obj.copy()
    # if there is no img_obj, read image from file path and then use it
    else:
        img = cv2.imread(img_name)
    img_resized = resize(img, height=maxHeight, inter=cv2.INTER_LANCZOS4)
    return img_resized


def getEnhancedImage(img_name, img_obj=None,
                     thrs_lo=145,
                     thrs_md=170,
                     thrs_hi=215):
    # if there is an image object, copy and then use it
    if img_obj is not None:
        img = img_obj.copy()
    # if there is no img_obj, read image from file path and then use it
    else:
        img = cv2.imread(img_name)

    # convert to YCrCb color
    img_YCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    # Y --- Luminance, to be adjusted
    img_Y = img_YCrCb[:, :, 0].astype(np.float)
    # mean value of luminance(brightness)
    y_mean = np.mean(img_Y)

    ### mapping y mean values to be three threshold(low, middle, high)
    # if meanVal < threshold_low
    if y_mean < thrs_lo:
        img_Y *= thrs_lo / y_mean
        img_Y[img_Y>255] = 255
    # if meanVal > threshold_high
    elif y_mean > thrs_hi:
        img_Y *= thrs_hi / y_mean
        img_Y[img_Y>255] = 255
    # if thrs_lo < meanVal < thrs_hi
    else:
        img_Y *= thrs_md / y_mean
        img_Y[img_Y>255] = 255

    # convert matrix type
    img_Y = img_Y.astype(np.uint8)
    img_YCrCb[:, :, 0] = img_Y
    # convert back to be BGR color
    img_enhanced = cv2.cvtColor(img_YCrCb, cv2.COLOR_YCrCb2BGR)
    return img_enhanced


def getRotatedImage(img, angle, scale=1.):
    rows, cols = img.shape[:2]
    M = cv2.getRotationMatrix2D(center=(cols/2., rows/2.),
                                angle=angle,
                                scale=scale)
    return cv2.warpAffine(img, M, (rows, cols))


def getDeskewedImage(img_name, img_obj=None,
                     ang_min=-50,
                     ang_max=50,
                     ang_num=120):
    # if there is an image object, copy and then use it
    if img_obj is not None:
        img = img_obj.copy()
    # if there is no img_obj, read image from file path and then use it
    else:
        img = cv2.imread(img_name)
    # convert to YCrCb color
    img_YCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    # Y --- Luminance, to be used as grayscale image
    img_Y = img_YCrCb[:, :, 0].astype(np.float)


    # possible angle range to be searched
    angle_li = np.linspace(ang_min, ang_max, ang_num)
    # dict to save...
    # angle:        angle, (float)
    # sum_axis0:    sum of image matrics by axis-0, (np.array)
    # s0_diff:      diff of sum_axis0, (np.array)
    s0_res = {'angle': [],
              'sum_axis0': [],
              's0_diff':[]}
    for angle in angle_li:
        # rotate image by angle (zoom-in 1.3X)
        res = getRotatedImage(img_Y, angle, 1.3)
        # calculate sum of image matrics in axis-0
        sum_axis0 = np.sum(res, axis=0).astype(np.float)
        # save data
        s0_res['angle'].append(angle)
        s0_res['sum_axis0'].append(sum_axis0)
        s0_res['s0_diff'].append(np.diff(sum_axis0))
    # convert to dataframe
    s0_res = pd.DataFrame(s0_res)
    # get maximum of s0_diff for each angle
    s0_res['s0_diff_max'] = s0_res.s0_diff.apply(np.max)
    # get position of s0_diff_max
    ang_idx = np.argmax(s0_res['s0_diff_max'])
    ang = angle_li[ang_idx]
    # print('rotate {}'.format(ang))

    # if ang is 0 or 45 ~ ang_max, ang -> -ang
    if abs(ang_max)*(1-9e-5) > abs(ang) > 45:
        ang = -ang
        print('(fix)rotate {}'.format(ang))
    img_deskewed = getRotatedImage(img, ang)
    return img_deskewed
