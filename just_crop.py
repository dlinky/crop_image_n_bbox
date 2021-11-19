import os
import get_roi

import cv2


path_dir = os.getcwd()
original_dir = os.path.join(path_dir, 'original')
result_dir = os.path.join(path_dir, 'result')
file_list = [_ for _ in os.listdir(original_dir) if _.endswith('.jpg')]

for file in file_list:
    img = cv2.imread(os.path.join(original_dir, file))
    square = get_roi.find_roi(img, 'square')

    # print('square =', square)

    # 이미지, bbox 정사각형으로 crop
    # print('cropping image, bboxes')
    img = get_roi.process_roi(img, square)

    cv2.imwrite(os.path.join(result_dir, file), img)