# -*- coding: utf-8 -*-
"""四轮一带产品信息采集器 - 主入口。

使用方式:
    python collect.py <供应商官网URL> [--output-dir OUTPUT_DIR] [--adapter ADAPTER_MODULE]
"""

import importlib
import os
import re
import sys
from datetime import datetime
from urllib.parse import urljoin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

import export
import standardize


def collect(url, output_dir=None, adapter_name=None):
    """Run collection, standardization, image download, and export."""
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    adapter = load_adapter(url, adapter_name)
    if adapter is None:
        print("[错误] 无法为该网站加载适配器")
        return []

    print(f"开始采集: {url}")
    products = crawl(adapter)
    print(f"  采集到 {len(products)} 个产品")

    for product in products:
        _, std_en, cn = standardize.standardize_name(product.get("raw_name", ""))
        product["std_name"] = cn
        product["std_name_en"] = std_en

    raw_image_dir = os.path.join(output_dir, "images_raw")
    os.makedirs(raw_image_dir, exist_ok=True)
    for product in products:
        for image_url in product.get("image_urls", []):
            image_path = adapter.download_image(image_url, raw_image_dir)
            if image_path:
                product["image_path"] = image_path
                product["image_name"] = os.path.basename(image_path)
                break

    excel_dir = os.path.join(output_dir, "Excel")
    os.makedirs(excel_dir, exist_ok=True)
    excel_path = os.path.join(excel_dir, "products.xlsx")
    export.export_to_excel(products, excel_path)

    image_output_dir = os.path.join(output_dir, "官网图片")
    os.makedirs(image_output_dir, exist_ok=True)
    export.organize_images(products, image_output_dir)

    for product in products:
        print(
            f"  - {product.get('part_no', '?')} | "
            f"{product.get('raw_name', '?')} -> {product.get('std_name', '?')}"
        )

    return products


def load_adapter(url, adapter_name=None):
    """Load a site-specific adapter, or fall back to BasicAdapter."""
    if adapter_name:
        module = importlib.import_module(f"adapters.{adapter_name}")
        adapter_class = getattr(module, "Adapter")
        return adapter_class(url)
    return BasicAdapter(url)


class BasicAdapter:
    """Generic crawler for simple product-list/product-detail pages."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

    def list_products(self):
        """Discover candidate product detail links from the starting page."""
        if not requests:
            return []
        try:
            response = self.session.get(self.base_url, timeout=20)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            product_urls = set()
            for anchor in soup.find_all("a", href=True):
                full_url = urljoin(self.base_url, anchor["href"])
                if self.is_product_page(full_url):
                    product_urls.add(full_url)
            return sorted(product_urls)
        except Exception:
            return []

    def extract_product(self, product_url):
        """Extract product fields from one product page."""
        if not requests:
            return None
        try:
            response = self.session.get(product_url, timeout=20)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else ""
            raw_name = title.strip() if title else ""
            page_text = soup.get_text(" ", strip=True)

            part_no = ""
            part_match = re.search(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b|\b[A-Z]{2,}\d{3,}\b", page_text)
            if part_match:
                part_no = part_match.group(0)

            image_urls = []
            for image in soup.find_all("img"):
                src = image.get("src", "")
                if not src:
                    continue
                full_src = urljoin(product_url, src)
                if self._is_product_image(full_src):
                    image_urls.append(full_src)

            description = ""
            desc_meta = soup.find("meta", attrs={"name": "description"})
            if desc_meta:
                description = desc_meta.get("content", "")

            return {
                "url": product_url,
                "raw_name": raw_name,
                "part_no": part_no or "待确认",
                "description": description,
                "image_urls": image_urls[:3],
                "brand": "",
                "model": "型号缺失",
                "machine_type": "",
                "notes": "",
            }
        except Exception:
            return None

    def download_image(self, image_url, save_dir):
        if not image_url or not self.session:
            return None
        try:
            from urllib.parse import urlparse
            import hashlib

            response = self.session.get(image_url, timeout=15)
            if response.status_code != 200:
                return None
            ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
            filename = hashlib.md5(image_url.encode("utf-8")).hexdigest()[:16] + ext
            output_path = os.path.join(save_dir, filename)
            with open(output_path, "wb") as handle:
                handle.write(response.content)
            return output_path
        except Exception:
            return None

    def is_product_page(self, url):
        patterns = [
            r"/product/",
            r"/products/",
            r"/item/",
            r"/p/",
            r"/detail/",
            r"/goods/",
            r"part_no=",
            r"id=",
        ]
        return any(re.search(pattern, url, re.I) for pattern in patterns)

    def _is_product_image(self, src):
        skip = ["logo", "banner", "icon", "nav", "bg_"]
        if any(keyword in src.lower() for keyword in skip):
            return False
        return os.path.splitext(src.split("?", 1)[0])[1].lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }


def crawl(adapter):
    """Run adapter collection and return standardized candidate products."""
    product_urls = adapter.list_products()
    if not product_urls:
        product_urls = [adapter.base_url]

    products = []
    seen = set()
    for url in product_urls[:50]:
        data = adapter.extract_product(url)
        if not data:
            continue
        dedupe_key = (data.get("part_no", ""), data.get("raw_name", ""))
        if dedupe_key in seen:
            continue
        if standardize.is_crawler_part(data.get("raw_name", ""), data.get("description", "")):
            seen.add(dedupe_key)
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            products.append(data)
    return products


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python collect.py <URL> [--output-dir DIR]")
        sys.exit(1)

    target_url = sys.argv[1]
    target_output_dir = None
    target_adapter = None
    if "--output-dir" in sys.argv:
        index = sys.argv.index("--output-dir")
        target_output_dir = sys.argv[index + 1] if index + 1 < len(sys.argv) else None
    if "--adapter" in sys.argv:
        index = sys.argv.index("--adapter")
        target_adapter = sys.argv[index + 1] if index + 1 < len(sys.argv) else None

    collect(target_url, target_output_dir, target_adapter)
