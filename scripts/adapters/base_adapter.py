# -*- coding: utf-8 -*-
import hashlib
import os
import re
from urllib.parse import urlparse


class BaseAdapter:
    def __init__(self, base_url, session=None):
        self.base_url = base_url.rstrip('/')
        self.session = session
        self.domain = urlparse(base_url).netloc

    def list_products(self):
        raise NotImplementedError

    def extract_product(self, product_url):
        raise NotImplementedError

    def download_image(self, img_url, save_dir):
        if not img_url or not self.session:
            return None
        try:
            resp = self.session.get(img_url, timeout=15)
            if resp.status_code != 200:
                return None
            ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
            fname = hashlib.md5(img_url.encode('utf-8')).hexdigest()[:16] + ext
            fpath = os.path.join(save_dir, fname)
            with open(fpath, 'wb') as f:
                f.write(resp.content)
            return fpath
        except Exception:
            return None

    def is_product_page(self, url):
        patterns = [
            r'/product/',
            r'/products/',
            r'/item/',
            r'/p/',
            r'/detail/',
            r'/goods/',
            r'part_no=',
            r'id=',
        ]
        return any(re.search(pattern, url, re.I) for pattern in patterns)
