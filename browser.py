from testgneur.core.browser import PagesBrowser, URL
from testgneur.modules.practicefarma.alchemy.tables import SubDomain
from testgneur.core.browser.exceptions import ServerError
from testgneur.core.tools.decorators import retry
from mbackend.tools.exceptions.ecommerce.exceptions import CategoryDesactivated, ProductNotFound, MetaDesactivated
from mbackend.tools.tools import TooManyProxyErrors
from .pages import HomePage, CategoryPage, CategoryApiPage, ProductPage, MetaPage, BrandListApiPage, ProductsApiPage#, EmptyProductPage
from requests.exceptions import ConnectionError,ChunkedEncodingError
from urllib3.exceptions import ProtocolError, InvalidChunkLength,ReadTimeoutError
from  urllib.parse import quote
import time,random
from fake_useragent import UserAgent
from user_agents import parse

__all__ = ['AroggaBrowser']


class AroggaBrowser(PagesBrowser):
    BASEURL = "https://www.arogga.com/"
    TIMEOUT = 60

    
    category_api_page = URL("https://api.arogga.com/general/v1/menuItem\?_parent_id=(?P<_parent_id>\d+)", CategoryApiPage)
    
    product_page = URL('/(?P<slug>.+)', ProductPage)
    #empty_product_page = URL('/(?P<slug>.+)', EmptyProductPage)
    category_page = URL("(?P<slug>.+)", CategoryPage)
    #products_page = URL('/(?P<slug>fr/taxons/.+)\?limit=48&page=(?P<page>\d+)', CategoryPage)
    brand_list_api_page = URL("https://api.arogga.com/general/v1/productBrand/\?_perPage=3000", BrandListApiPage)
    products_api_page = URL(
        "https://api.arogga.com/general/v3/search/\?_page=(?P<page>\d+)&_perPage=18&_product_category_id=(?P<pcategory_id>\d+)&_order=pv_allow_sales:desc,productCountOrdered:desc&_is_base=1&_get_filters=true&f=web&(?P<ua_param>.+)",
        "https://api.arogga.com/general/v3/search/\?_page=(?P<page>\d+)&_perPage=18&_order=pv_allow_sales:desc,productCountOrdered:desc&_brand_id=(?P<brandid>\d+)&f=web&(?P<ua_param>.+)",
        "https://lab.arogga.com/lab-search/api/v1/search/category\?page=(?P<page>\d+)&tags=(?P<lab_test_tag>.+)&popular=desc&limit=20&f=web&(?P<ua_param>.+)",
        ProductsApiPage)
    home_page = URL('', HomePage)

    def __init__(self, *args, **kwargs):
        super(AroggaBrowser, self).__init__(*args, **kwargs)
        self.set_ramdom_ua()
        self.ua_param = None
        self.save_logs = False
    
    def set_ramdom_ua(self):
        ua = UserAgent(platforms='pc', min_version=100.0)
        rua = ua.random
        print(rua)
        self.session.headers = {
            'User-Agent': rua,
            'Referer': 'https://www.arogga.com/',
            'Origin': 'https://www.arogga.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        ua_info = parse(rua)
        browser = ua_info.browser.family
        browser_version = ua_info.browser.version_string
        os = ua_info.os.family
        os_version = ua_info.os.version_string
        self.ua_param = f"b={browser}&v={browser_version}&os={os}&osv={os_version}"

    def get_subdomain(self):
        subdomain_obj = SubDomain()
        subdomain_obj.baseurl = 'https://www.arogga.com/'
        subdomain_obj.has_shop = True
        subdomain_obj.has_drugs = True
        return subdomain_obj

    def iter_meta(self):
        self.home_page.go()
        assert self.home_page.is_here()
        for meta_obj in self.page.iter_meta():
            yield meta_obj

    def get_meta(self, meta_obj):
        assert meta_obj.url
        self.location(meta_obj.url)
        assert self.category_page.is_here()
        meta_obj = self.page.get_meta(meta_obj)
        if meta_obj.is_desactivated==True:
            raise MetaDesactivated
        else:
            return meta_obj

    def iter_categories(self):
        self.home_page.stay_or_go()
        assert self.home_page.is_here()
        for category_obj in self.page.iter_categories():
            yield category_obj
        time.sleep(10)
        self.brand_list_api_page.stay_or_go()
        self.brand_list_api_page.is_here()
        for brand_category_obj in self.page.iter_brand_categories():
            yield brand_category_obj
        
    def get_category_menu_data(self,_parent_id):
        assert _parent_id
        self.category_api_page.go(_parent_id=_parent_id)
        assert self.category_api_page.is_here()
        return self.page.iter_json_category()
        
    def get_total_products(self):
        assert self.products_api_page.is_here()
        return self.page.get_total_products()

    def get_total_pages(self):
        assert self.products_api_page.is_here()
        return self.page.get_total_pages()

    @retry(CategoryDesactivated, tries=3, delay=5, backoff=2)
    @retry(ConnectionError, tries=3, delay=5, backoff=2)
    def go_subcategory(self, category_obj, page):
        #input(category_obj.url)
        self.set_ramdom_ua()
        if category_obj.meta_category=='Brands':
            brandid = category_obj.url.split('/')[-1]
            self.products_api_page.go(page=page,brandid=brandid,ua_param=self.ua_param)
            self.products_api_page.is_here()
        else:
            if '/lab-test/' in category_obj.url:
                if 'tags=' not in category_obj.url:
                    self.category_page.go(slug=category_obj.slug)
                    assert self.category_page.is_here()
                    lab_test_tag = self.page.get_lab_test_tag()
                else:
                    lab_test_tag = category_obj.slug.split('&')[-2]
                    assert lab_test_tag.count('tags=')==1
                    lab_test_tag = lab_test_tag.split('=')[-1]
                    lab_test_tag = f'["{lab_test_tag}"]'
                assert lab_test_tag is not None
                encoded_tag = quote(lab_test_tag)
                self.products_api_page.go(page=page, lab_test_tag=encoded_tag, ua_param=self.ua_param)
                self.products_api_page.is_here()
            else:
                pcategory_id = category_obj.slug.split('/')[-2]
                self.products_api_page.go(page=page, pcategory_id=pcategory_id, ua_param=self.ua_param)
                self.products_api_page.is_here()
                if self.page.empty_category():
                    raise CategoryDesactivated

    def iter_products(self):
        assert self.products_api_page.is_here()
        for product_obj, history_obj in self.page.iter_products():
            yield product_obj, history_obj

    @retry(ConnectionError, tries=20, delay=3, backoff=0)
    @retry(ReadTimeoutError, tries=20, delay=3, backoff=0)
    @retry(ChunkedEncodingError, tries=20, delay=3, backoff=0)
    @retry(InvalidChunkLength, tries=20, delay=3, backoff=0)
    @retry(ProtocolError, tries=20, delay=3, backoff=0)
    @retry(ValueError, tries=20, delay=3, backoff=0)
    @retry(TooManyProxyErrors, tries=6, delay=5, backoff=0)
    def fill_product_and_history_details(self, product_obj, history_obj):
        #time.sleep(1+random.randint(0,2))
        try:
            self.product_page.go(slug = product_obj.slug, headers=self.session.headers)
            assert self.product_page.is_here()
        except AssertionError as e:
            if  self.home_page.is_here() or self.category_page.is_here():
                raise ProductNotFound()
            elif self.url != product_obj.url:
                assert product_obj.slug not in self.url
                raise ProductNotFound()
            else:
                raise e

        self.page.fill_product_and_history_details(product_obj, history_obj)
        self.assert_product_and_history(product_obj, history_obj)

    def assert_product_and_history(self, product_obj, history_obj):
        try:
            assert product_obj.name is not None
            if product_obj.image_url:
                assert product_obj.image_url.count('https:') == 1
            assert product_obj.slug is not None
            if product_obj.sku_found:
                assert product_obj.sku is not None
            assert history_obj.price is not None
            if history_obj.availability_bool:
                assert history_obj.availability in ['Service avilable', 'In stock']
            else:
                assert history_obj.availability in ['Out of stock']
            if history_obj.crossed_out_price:
                assert history_obj.price < history_obj.crossed_out_price
                assert history_obj.discount_claim
            if history_obj.unit_crossed_out_price:
                assert history_obj.unit_price < history_obj.unit_crossed_out_price
                
        except AssertionError:
            raise Exception(f"Assertion error on {product_obj.__dict__}",
                            f"with history {history_obj.__dict__}")
