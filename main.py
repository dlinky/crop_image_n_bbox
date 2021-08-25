import os
import cv2
from xml.etree import ElementTree as ET

import get_roi


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error. creating directory', directory)


def load_xml(doc):
    root = doc.getroot()  # annotation
    table = [['folder', 'filename', 'path', 'database', 'width', 'height', 'depth', 'segmented']]
    line = []
    line.append(root.findtext('folder'))
    line.append(root.findtext('filename'))
    line.append(root.findtext('path'))
    line.append(root.find('source').findtext('database'))
    line.append(root.find('size').findtext('width'))
    line.append(root.find('size').findtext('height'))
    line.append(root.find('size').findtext('depth'))
    line.append(root.findtext('segmented'))
    table.append(line)
    table.append(['name, pose, truncated, difficult, xmin, ymin, xmax, ymax'])
    for object in root.iter('object'):
        line = []
        line.append(object.findtext('name'))
        line.append(object.findtext('pose'))
        line.append(object.findtext('truncated'))
        line.append(object.findtext('difficult'))
        line.append(int(object.find('bndbox').findtext('xmin')))
        line.append(int(object.find('bndbox').findtext('ymin')))
        line.append(int(object.find('bndbox').findtext('xmax')))
        line.append(int(object.find('bndbox').findtext('ymax')))
        table.append(line)
    return table


# boundary box가 정사각형 밖에 있는지 확인
def is_bbox_outside_square(bbox, square):
    left, up, right, down = bbox
    xmin, ymin, xmax, ymax = square

    # 오차 적용
    xmin = int(xmin * 0.99)
    ymin = int(ymin * 0.99)
    xmax = int(xmax * 1.01)
    ymax = int(ymax * 1.01)

    if left < xmin or up < ymin or right > xmax or down > ymax:
        return 1
    else:
        return 0


def crop_boxes(table, square):
    for i, cell in enumerate(table):
        bbox = cell[4:8]
        # square 밖의 bbox 제거
        if is_bbox_outside_square(bbox, square) == 1:
            table.pop(i)
        # square 안의 bbox 사이즈에 맞게 이동
        else:
            move_bbox(bbox, square)
    table[1][4] = square[2] - square[0]
    table[1][5] = square[3] - square[1]
    return table


def move_bbox(bbox, square):
    left = bbox[0] - square[0] + 1
    up = bbox[1] - square[1] + 1
    right = bbox[2] - square[0] + 1
    down = bbox[3] - square[1] + 1
    return [left, up, right, down]


def resize_bbox(bbox, scale):
    for item in bbox[4:]:
        item = int(item * scale)
    return bbox


def split_img(img, mat):
    height, width = img.shape[:2]
    dh = int(height / mat[0])
    dw = int(width / mat[1])
    print('h, w = %d, %d, mat = [%d, %d], dh, dw = %d, %d' % (height, width, mat[0], mat[1], dh, dw))
    images = []
    for r in range(mat[0]):
        for c in range(mat[1]):
            print('split : [%d:%d, %d:%d]'%(dh*r, dh*(r+1), dw*c, dw*(c+1)))
            images.append(img[dh*r : dh*(r+1), dw*c : dw*(c+1)].copy())
    return images


def split_table(table_title, table, mat):
    height = int(table_title[1][5])
    width = int(table_title[1][4])
    dh = int(height / mat[0])
    dw = int(width / mat[1])

    tables = []

    for r in range(mat[0]-1):
        tables.append([])
        for c in range(mat[1]-1):
            square = [dh*r, dw*c, dh*(r+1), dw*(c+1)]
            tables[r].append(crop_boxes(table, square))

    return tables


def main():
    # 경로 설정
    path_dir = os.getcwd()
    original_dir = path_dir + '/original/'
    result_dir = path_dir + '/result/'
    create_folder(result_dir)

    # xml, 이미지 명단
    xmlExt = r'.xml'
    imgExt = r'.jpg'
    xml_list = [_ for _ in os.listdir(original_dir) if _.endswith(xmlExt)]
    img_list = [_ for _ in os.listdir(original_dir) if _.endswith(imgExt)]

    # 파일 이름만 별도로 저장
    filename_list = []
    for item in xml_list:
        filename_list.append(item.split('.')[0])

    for page, file in enumerate(filename_list):
        # xml, 이미지 로드
        img = cv2.imread(original_dir + img_list[page])
        doc = ET.parse(original_dir + xml_list[page])
        print('loaded file : %s, %s' % (img_list[page], xml_list[page]))

        # xml파일을 리스트로 불러오기 ... title까지 전부!
        print('loading xml')
        table_origin = load_xml(doc)
        table_title = table_origin[:3]
        table = table_origin[3:]

        # scope에 내접하는 정사각형 찾기
        print('finding square inside scope : ', end='')
        square = get_roi.find_roi(img, 'square')
        print('square =', square)

        # 이미지, bbox 정사각형으로 crop
        print('cropping image, bboxes')
        table = crop_boxes(table, square)
        img = get_roi.process_roi(img, square)

        # 이미지, bbox resize, split, 저장까지 일괄로
        ratios = [1.0, 1.2, 1.5, 2.0]
        mat_split = [[3, 2], [2, 2]]
        for i, ratio in enumerate(ratios):
            print('resizing %.1fx' % ratio)
            img_temp = cv2.resize(img, (0, 0), fx=ratio, fy=ratio)
            table_temp = table.copy()
            for bbox in table_temp:
                resize_bbox(bbox, ratio)

            # split, 저장
            ratio_dir = result_dir + 'resized(x%.1f)/' % ratio
            create_folder(ratio_dir)
            for mat in mat_split:
                print('spliting in', mat)
                images = split_img(img_temp, mat)
                tables = split_table(table_title, table_temp, mat)
                split_dir = ratio_dir + 'splited(%d,%d)/' % (mat[0], mat[1])
                create_folder(split_dir)
                print(split_dir)
                for i, img_result in enumerate(images):
                    cv2.imwrite(split_dir + filename_list[page] + '-%d' % (i+1) + '.jpg', img_result)
                    # autoxml.autoxml(
        print('complete')
    print('all process completed')


if __name__ == '__main__':
    main()