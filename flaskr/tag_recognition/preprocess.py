# -*- coding: utf-8 -*-
"""
resize to [maxHeight=600]
resized images are saved in the same location as the original images
"""
import cv2
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


def getResizedImage(img_name, maxHeight=600):
    image = cv2.imread(img_name)
    image_resized = resize(image, height=maxHeight, inter=cv2.INTER_LANCZOS4)
    image_resized = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image_resized)
