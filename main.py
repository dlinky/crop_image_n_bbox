import os
import cv2
import labelimg_xml

import get_roi


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error. creating directory', directory)


# boundary box가 정사각형 밖에 있는지 확인
def is_bbox_outside_square(bbox, square):
    # 오차 적용
    xmin = int(square[0] * 0.99)
    ymin = int(square[1] * 0.99)
    xmax = int(square[2] * 1.01)
    ymax = int(square[3] * 1.01)

    if bbox[0] < xmin or bbox[1] < ymin or bbox[2] > xmax or bbox[3] > ymax:
        print('bbox =', bbox, ', square =', square, '. remove')
        return 1
    else:
        print('bbox =', bbox, ', square =', square, '. move')
        return 0


def crop_boxes(title, table, square):
    new_title = title.copy()
    new_table = table.copy()
    print('cropping bboxes')
    for i, cell in enumerate(new_table[:]):
        bbox = cell[1:5]
        # square 밖의 bbox 제거
        if is_bbox_outside_square(bbox, square) == 1:
            new_table.remove(cell)
        # square 안의 bbox 사이즈에 맞게 이동
        else:
            cell[1:5] = move_bbox(bbox, square)
            print('moved to', cell[1:5])

    new_title[4] = str(square[2] - square[0])
    new_title[5] = str(square[3] - square[1])
    return new_title, new_table


def move_bbox(bbox, square):
    left = bbox[0] - square[0]
    up = bbox[1] - square[1]
    right = bbox[2] - square[0]
    down = bbox[3] - square[1]
    return [left, up, right, down]


def resize_bbox(bbox, scale):
    for item in bbox[4:]:
        item = int(item * scale)
    return bbox


def split_img(img, mat):
    print('splitting image')
    height, width = img.shape[:2]
    dh = int(height / mat[0])
    dw = int(width / mat[1])
    print('h, w = %d, %d, mat = [%d, %d], dh, dw = %d, %d' % (height, width, mat[0], mat[1], dh, dw))
    images = []
    for r in range(mat[0]):
        for c in range(mat[1]):
            print('split image : [%d:%d, %d:%d]' % (dh*r, dh*(r+1), dw*c, dw*(c+1)))
            images.append(img[dh*r: dh*(r+1), dw*c: dw*(c+1)].copy())
    return images


def split_table(title, table, mat):
    print('splitting bboxes in (%d, %d)' % (mat[0], mat[1]))
    height = int(title[5])
    width = int(title[4])
    dh = int(height / mat[0])
    dw = int(width / mat[1])
    print('size = %d x %d into %d x %d' % (width, height, dw, dh))

    titles = []
    tables = []
    i = 0
    for r in range(mat[0]):
        for c in range(mat[1]):
            print('r = %d, c = %d' % (r, c))
            i += 1
            square = [dw*c, dh*r, dw*(c+1), dh*(r+1)]
            new_title, new_table = crop_boxes(title, table, square)
            print('table size : %d, cropped table size : %d' % (len(table), len(new_table)))
            print('appended splited table. zone : (%d:%d, %d:%d)' % (square[0], square[1], square[2], square[3]))
            titles.append(new_title.copy())
            tables.append(new_table.copy())
    return titles, tables


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

    for page, filename in enumerate(filename_list):
        print('processing', filename)
        # xml, 이미지 로드
        img = cv2.imread(original_dir + img_list[page])
        title, table = labelimg_xml.read_xml(original_dir, filename + '.xml')

        '''
        # scope에 내접하는 정사각형 찾기
        print('finding square inside scope : ', end='')
        square = get_roi.find_roi(img, 'square')

        print('square =', square)

        # 이미지, bbox 정사각형으로 crop
        print('cropping image, bboxes')
        title, table = crop_boxes(title, table, square)
        img = get_roi.process_roi(img, square)
        '''

        # 이미지, bbox resize, split, 저장까지 일괄로
        print('resizing image, bboxes')
        ratios = [1.0, 1.2, 1.5, 2.0]
        mat_split = [[1, 1], [2, 2], [3, 2]]
        for ratio in ratios:
            print('resizing %.1fx' % ratio)
            img_temp = cv2.resize(img, (0, 0), fx=ratio, fy=ratio)
            table_temp = table.copy()
            for bbox in table_temp:
                resize_bbox(bbox, ratio)

            print('spliting image, bboxes')
            # split, 저장
            ratio_dir = result_dir + 'resized(x%.1f)/' % ratio
            create_folder(ratio_dir)
            for mat in mat_split:
                print('spliting in', mat)
                images = split_img(img_temp, mat)
                titles, tables = split_table(title, table_temp, mat)
                split_dir = ratio_dir + 'splited(%d,%d)/' % (mat[1], mat[0])
                create_folder(split_dir)
                for i, img_result in enumerate(images):
                    new_filename = filename + '-%d' % (i+1) + '.jpg'
                    cv2.imwrite(split_dir + new_filename, img_result)
                    print('result position. table size : %d, cropped table size : %d' % (len(table_temp), len(tables[i])))
                    titles[i][1] = new_filename
                    titles[i][2] = split_dir + new_filename

                    print('write xml')
                    labelimg_xml.write_xml(titles[i], tables[i], split_dir, filename_list[page] + '-%d' % (i+1) + '.xml')
        print('complete')
    print('all process completed')


if __name__ == '__main__':
    main()