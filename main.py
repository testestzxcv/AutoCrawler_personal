"""
Copyright 2018 YoongiKim

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


import os
import requests
import shutil
from multiprocessing import Pool
import argparse
from collect_links import CollectLinks


class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'google'
        elif code == Sites.NAVER:
            return 'naver'
        elif code == Sites.GOOGLE_FULL:
            return 'google'
        elif code == Sites.NAVER_FULL:
            return 'naver'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=True, download_path='download',
                 full_resolution=False, face=False):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        :param download_path: Download folder path
        :param full_resolution: Download full resolution image instead of thumbnails (slow)
        :param face: Face search mode
        """

        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):        # 디렉토리에 있는 파일들의 리스트
            if os.path.isdir(path + '/' + dir): # 디렉토리이면
                paths.append(path + '/' + dir)  # paths 리스트에 /dir 형식으로 추가

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):     # 시작 디렉터리부터 시작하여 그 하위의 모든 디렉터리를 차례대로 방문하게 해주는 함수, path 이하
            for file in files:
                if os.path.isfile(path + '/' + file):   # 파일이면
                    paths.append(path + '/' + file)     # paths 리스트에 /dir 형식으로 추가

        return paths

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(keywords_file='keywords.txt'):
        # read search keywords from file
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} keywords found: {}'.format(len(keywords), keywords))

        # re-save sorted keywords
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords

    def save_image_to_file(self, image, file_path):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                shutil.copyfileobj(image.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    def download_images(self, keyword, links, site_name):   # 검색어,
        self.make_dir('{}/{}'.format(self.download_path, keyword))
        total = len(links)

        for index, link in enumerate(links):
            try:
                print('Downloading {} from {}: {} / {}'.format(keyword, site_name, index + 1, total))
                response = requests.get(link, stream=True)
                ext = self.get_extension_from_link(link)
                self.save_image_to_file(response, '{}/{}/{}_{}.{}'.format(self.download_path, keyword, site_name, str(index).zfill(4), ext))
                del response

            except Exception as e:
                print('Download failed - ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)   # google, naver
        add_url = Sites.get_face_url(site_code) if self.face else ""    # cmd로 실행하면 매개변수 입력됨, 파이참에서 실행하면 ""
        collect = CollectLinks()  # initialize chrome driver    수집 인스턴스 생성

        try:
            print('Collecting links... {} from {}'.format(keyword, site_name))  # 키워드, 사이트

            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)    # 파이참에서 실행하면 구글(검색어, "") 로 실행됨, 결과값은 links에 저장
                print("links1==========", links)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)
                print("links2==========", links)

            elif site_code == Sites.GOOGLE_FULL:
                links = collect.google_full(keyword, add_url)
                print("links3==========", links)

            elif site_code == Sites.NAVER_FULL:
                links = collect.naver_full(keyword, add_url)
                print("links4==========", links)

            else:
                print('Invalid Site Code')
                links = []

            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name)     # 실제로 다운로드 됨

            print('Done {} : {}'.format(site_name, keyword))    # 다운로드 완료

        except Exception as e:
            print('Exception {}:{} - {}'.format(site_name, keyword, e))

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def do_crawling(self):
        keywords = self.get_keywords()

        tasks = []

        for keyword in keywords:
            dir_name = '{}/{}'.format(self.download_path, keyword)  # 생성 디렉토리 이름
            if os.path.exists(os.path.join(os.getcwd(), dir_name)) and self.skip:   # (현재작업 디렉토리+생성디렉토리) 존재하고, skip 상태이면
                print('Skipping already existing directory {}'.format(dir_name))
                continue

            if self.do_google:
                if self.full_resolution:
                    tasks.append([keyword, Sites.GOOGLE_FULL])
                else:
                    tasks.append([keyword, Sites.GOOGLE])

            if self.do_naver:
                if self.full_resolution:
                    tasks.append([keyword, Sites.NAVER_FULL])
                else:
                    tasks.append([keyword, Sites.NAVER])

        pool = Pool(self.n_threads)         # 입력데이터를 프로세스에 분산
        pool.map_async(self.download, tasks)    # 결과 객체를 반환하는 map 메서드의 변형, 여기서부터 프로세스 시작
        pool.close()
        pool.join()
        print('Task ended. Pool join.')

        self.imbalance_check()

        print('End Program')

    def imbalance_check(self):
        print('Data imbalance checking...')

        dict_num_files = {}

        for dir in self.all_dirs(self.download_path):   # download_path 에 디렉토리가 있으면
            n_files = len(self.all_files(dir))      # 해당 디렉토리 안에 파일 개수
            dict_num_files[dir] = n_files           # 딕셔너리에 저장

        avg = 0
        for dir, n_files in dict_num_files.items():
            avg += n_files / len(dict_num_files)
            print('dir: {}, file_count: {}'.format(dir, n_files))   # 파일개수 출력

        dict_too_small = {}

        for dir, n_files in dict_num_files.items():
            if n_files < avg * 0.5:
                dict_too_small[dir] = n_files

        if len(dict_too_small) >= 1:
            for dir, n_files in dict_too_small.items():
                print('Data imbalance detected.')
                print('Below keywords have smaller than 50% of average file count.')
                print('I recommend you to remove these directories and re-download for that keyword.')
                print('_________________________________')
                print('Too small file count directories:')
                print('dir: {}, file_count: {}'.format(dir, n_files))

            print("Remove directories above? (y/n)")
            answer = input()

            if answer == 'y':
                # removing directories too small files
                print("Removing too small file count directories...")
                for dir, n_files in dict_too_small.items():
                    shutil.rmtree(dir)
                    print('Removed {}'.format(dir))

                print('Now re-run this program to re-download removed files. (with skip_already_exist=True)')
        else:
            print('Data imbalance not detected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()      # 파서 아규먼트 세팅
    parser.add_argument('--skip', type=str, default='true',
                        help='Skips keyword already downloaded before. This is needed when re-downloading.')    # 스킵한다 키워드를 이미 다운로드된것을 이전에. 이것은 필요하다 언제냐면 다시 다운로딩할때
    parser.add_argument('--threads', type=int, default=4, help='Number of threads to download.')                # 넘버 of 스레드 to 다운로드
    parser.add_argument('--google', type=str, default='true', help='Download from google.com (boolean)')        # 구글에서 다운로드(참/거짓)
    parser.add_argument('--naver', type=str, default='true', help='Download from naver.com (boolean)')          # 네이버에서 다운로드(참/거짓)
    parser.add_argument('--full', type=str, default='false', help='Download full resolution image instead of thumbnails (slow)')    # 다운로드 전체 해상도 이미지 무엇대신이냐면 섬네일(느림)
    parser.add_argument('--face', type=str, default='false', help='Face search mode')                           # 페이스 찾기 모드
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True        # str(args.skip).lower 가 false 이면 False, 아니면 True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True

    print('Options - skip:{}, threads:{}, google:{}, naver:{}, full_resolution:{}, face:{}'.format(_skip, _threads, _google, _naver, _full, _face))

    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads, do_google=_google, do_naver=_naver, full_resolution=_full, face=_face)
    crawler.do_crawling()
