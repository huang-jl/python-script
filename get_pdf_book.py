from reportlab.pdfgen import canvas
import requests
import os
from PIL import Image
import numpy as np
from reportlab.lib.utils import ImageReader
import argparse
import re
import time
import my_fake_useragent as ua


class DownloadException(BaseException):
    def __init__(self, page_begin):
        self.page_begin = page_begin
        print('Download error at pages {}\nBegin to download again'.format(page_begin))


class Download:
    def __init__(self, quality, url, hash):
        self.url = url
        self.hash = hash
        self.quality = quality
        self.user_agent = ua.UserAgent()

    def download(self, pages, check=False):
        # sub function

        def download_pages(page):
            headers = {'User-Agent': self.user_agent.random()}
            file_path = os.path.join(DIR_PATH, '{}_4_5.png'.format(page))
            # 检查如果文件不存在或异常太小
            if not os.path.exists(file_path) or os.path.getsize(file_path) < 60:
                try:
                    self.prepared_visit(page, headers)
                except BaseException:
                    raise DownloadException(page)

            for row in rows:
                for col in cols:
                    file_name = os.path.join(
                        DIR_PATH, '{}_{}_{}.png'.format(page, row, col))
                    # 如果文件大小正常且存在，我们就跳过
                    if os.path.exists(file_name) and os.path.getsize(file_name) > 60:
                        print('Already exists\r', end='')
                    else:
                        try:
                            response = requests.get(self.url.format(
                                iter, self.quality, row, col), headers=headers, timeout=(5, 10))
                        except BaseException:
                            raise DownloadException(page)

                        with open(file_name, 'wb') as f:
                            f.write(response.content)

        DIR_PATH = os.path.join('.', 'pic_sample')
        if os.path.isdir(DIR_PATH):
            pass
        else:
            os.mkdir(DIR_PATH)
        rows = list(range(1, 5))
        cols = list(range(1, 6))

        iter = pages[0]
        while iter < pages[1]+1:
            try:
                download_pages(iter)
            except DownloadException:
                print('Page {0} failed. Restart at Page {0}'.format(iter))
                continue
            else:
                print('Page:{} has been download'.format(iter), end='\t')
                complete_ratio = (iter - pages[0] + 1) / (pages[1]-pages[0]+1)
                #simple process bar
                print('\r[{:-<20}] : {}/{}   {:.2f}%\r'.format(
                    '#'*int(20*complete_ratio), iter, pages[1], complete_ratio*100), end='')
                #sleep random time every 20 pics
                if not check and iter % 20 == 0:
                    time.sleep(np.random.randint(1, 3))
                iter += 1
        print('\nDownload Success!\n')
        return DIR_PATH

    def prepared_visit(self, page, headers):
        urls = [
            'http://pdf.cabplink.com/asserts/{}/imagestatus/{}/{}/400?accessToken=accessToken&formMode=true&extenParams=%7B%7D'.format(
                self.hash, page, self.quality),
            'http://pdf.cabplink.com/asserts/{}/imagestatus/{}/{}/400?accessToken=accessToken'.format(
                self.hash, page, self.quality),
            'http://pdf.cabplink.com/asserts/{0}/text/{1}?formMode=true&pageIndex={1}&extenParams=%7B%7D'.format(
                self.hash, page),
            'http://pdf.cabplink.com/asserts/{0}/annots/{1}?formMode=true&pageIndex={1}&extenParams=%7B%7D'.format(
                self.hash, page)
        ]
        for url in urls:
            requests.request('GET', url, headers=headers, timeout=(5, 10))


class Transformer:
    def __init__(self, path='.', method=1, quality=100):
        self.path = path
        self.method = method
        self.quality = quality

    def transform(self, pages=1, target='.'):
        IMG_NAME = '{}_{}_{}.png'
        rows = list(range(1, 5))
        cols = list(range(1, 6))
        size, mode = self.get_img_size(self.path, rows, cols)
        print('mode:', mode)
        size = size.astype(int)
        width = size[:, 0, 0]
        height = size[0, :, 1]
        print('img_sum_width: {}, img_sum_height: {}'.format(
            width.sum(), height.sum()))

        # 下面分别是两种方法
        if self.method == 1:
            image_list = []
            for i in range(1, pages+1):
                pic = Image.new(mode, (width.sum(), height.sum()))
                for row in rows:
                    for col in cols:
                        image_name = os.path.join(self.path, IMG_NAME.format(i, row, col))
                        img = Image.open(image_name,)
                        x, y = width[:row-1].sum(), height[:col-1].sum()
                        pic.paste(img, (x, y, x+width[row-1], y+height[col-1]))
                # Resize the picture
                thumbnail_ratio = 100 / self.quality
                pic.thumbnail((pic.size[0] * thumbnail_ratio, pic.size[1] * thumbnail_ratio), Image.ANTIALIAS)
                image_list.append(pic)
                print('Page:{} has been transformed\r'.format(i), end='')
            # save all the pic to pdf
            im1 = image_list[0]
            im1.save(target, "PDF", save_all=True, append_images=image_list[1:], quality=95)

        # 方法2
        elif self.method == 2:
            resize_ratio = 100 / self.quality
            pdf = canvas.Canvas(target, pagesize=(width.sum()*resize_ratio, height.sum()*resize_ratio))
            pdf.drawString(width.sum()*resize_ratio//2, height.sum()*resize_ratio//2, "BY HuangJiaLiang")
            pdf.showPage()
            print('target position -> {}'.format(target))
            for i in range(1, pages+1):
                for row in rows:
                    for col in cols:
                        image_name = os.path.join(self.path, IMG_NAME.format(i, row, col))
                        pdf.drawImage(image_name, width[:row-1].sum()*resize_ratio, height[col:].sum()*resize_ratio,
                                      width[row-1]*resize_ratio, height[col-1]*resize_ratio, preserveAspectRatio=True)
                print('Page:{} has been transformed\r'.format(i),end='')
                pdf.showPage()
            print('\nSaving...')
            pdf.save()

    def get_img_size(self, path, rows, cols):
        IMG_PATH = '1_{}_{}.png'
        res = np.zeros((len(rows), len(cols), 2))
        mode = None
        for row in rows:
            for col in cols:
                img = Image.open(os.path.join(path, IMG_PATH.format(row, col)))
                img_size = img.size
                res[row-1, col-1] = img_size
                mode = img.mode
        return res, mode


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pages', type=int, action='store', nargs=2,
                        help='the number of pages you want to download')
    parser.add_argument('--hash', type=str, action='store',
                        help='the url of the files')
    parser.add_argument('-m', '--method', type=int,
                        action='store', help='Using PIL or reportlab')
    parser.add_argument('-q', '--quality', type=int,
                        action='store', help='quality of the pic')
    args = parser.parse_args()

    download = Download(args.quality,
                        'http://pdf.cabplink.com/asserts/{}/image/{}/tiles/{}/400/{}/{}?accessToken=accessToken'.format(args.hash, '{}', '{}', '{}', '{}'), args.hash)
    path = download.download(args.pages)
    download.download(args.pages, check=True)
    transformer = Transformer(os.path.join(
        '.', 'pic_sample'), method=args.method, quality=args.quality)
    transformer.transform(args.pages[1], os.path.join('.', 'test.pdf'))

    print('Success!')
