import xml.etree.ElementTree as ET


def read_xml(path, filename):
    # 파일 불러오기
    doc = ET.parse(path + filename)
    # 최상단 태그 지정 : 'annotation'
    root = doc.getroot()

    # 레이블만 빼놓은것. 아마 안쓸듯
    labels_title = ['folder', 'filename', 'path', 'database', 'width', 'height', 'depth', 'segmented']

    title = []  # 파일, 이미지 정보 등 저장
    table = []  # bounding box 저장

    # 파일정보, 이미지정보 읽어와서 title에 저장
    for child in root.iter():
        # 2단계 자식노드 (source, size) 따로 처리
        if child.iter():
            # bndbox 따로 처리
            for grandchild in child.iter():
                if child.iter():
                    continue
                else:
                    title.append(grandchild.text)
        # 1단계 자식노드
        else:
            title.append(child.text)

    # bounding box 저장
    for object in root.iter('object'):
        print(object.tag)
        line = []
        for bndbox in object.iter('bndbox'):
            print(bndbox.tag)
            for point in bndbox:
                print(point.tag)
                print(point.text)
                line.append(int(point.text))
        table.append(line)
        line.clear()
    return title, table


def write_xml(title, table, path, filename):
    root = ET.Element('annotation')
    for line in title:
        ET.SubElement(root, 'folder').text = line[0]
        ET.SubElement(root, 'filename').text = line[1]
        ET.SubElement(root, 'path').text = line[2]

        source = ET.SubElement(root, 'source')
        ET.SubElement(source, 'database').text = line[3]

        size = ET.SubElement(root, 'size')
        ET.SubElement(size, 'width').text = line[4]
        ET.SubElement(size, 'height').text = line[5]
        ET.SubElement(size, 'depth').text = line[6]

        ET.SubElement(root,'segmented').text = line[7]

    for line in table:
        obj = ET.SubElement(root, 'object')
        ET.SubElement(obj, 'name').text = line[0]
        ET.SubElement(obj, 'pose').text = '0'
        ET.SubElement(obj, 'truncated').text = '0'
        ET.SubElement(obj, 'difficult').text = '0'

        bndbox = ET.SubElement(obj, 'bndbox')
        ET.SubElement(bndbox, 'xmin').text = line[1]
        ET.SubElement(bndbox, 'ymin').text = line[2]
        ET.SubElement(bndbox, 'xmax').text = line[3]
        ET.SubElement(bndbox, 'ymax').text = line[4]

    tree = ET.ElementTree(root)
    tree.write(path + filename)


def main():
    title, table = read_xml('./', 'sample.xml')
    print('read xml')
    print(title)
    print(table)
    write_xml(title, table, './', 'result.xml')


if __name__ == '__main__':
    main()