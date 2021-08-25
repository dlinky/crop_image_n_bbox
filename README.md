# crop_image_n_bbox

## 실행 방법

'''
python main.py
'''

## 입출력 파일 경로
원본 이미지, xml : ./original/
출력 이미지, xml : ./result/resized(ratio)/splited(r,c)/

## 파일 설명
main.py : 메인 기능
get_roi.py : roi 설정. 여기서는 스코프 및 내접 정사각형 검출
manual_roi.py : get_roi에서 자동으로 검출 안될경우 스코프를 직접 
