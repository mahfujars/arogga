from testgneur.core.tools.backend import Module
from .browser import AroggaBrowser

__all__ = ['AroggaBrowser']

class AroggaModule(Module):
    NAME = 'Arogga'
    MAINTAINER = u'Noyon'
    EMAIL = 'mrnoyon.cse@gmail.com'
    VERSION = '1'
    DESCRIPTION = u'Arogga data scraping test project'
    LICENSE = 'AGPL'
    BROWSER = AroggaBrowser

    """ def get_subdomain(self):
        return self.browser.get_subdomain()

    def iter_meta(self):
        return self.browser.iter_meta()

    def get_meta(self,meta_obj):
         return self.browser.get_meta(meta_obj) """

    def iter_categories(self):
        return self.browser.iter_categories()

    def go_subcategory(self, category_obj, page):
        return self.browser.go_subcategory(category_obj, page)

    def get_total_pages(self):
        return self.browser.get_total_pages()

    def get_total_products(self):
        return self.browser.get_total_products()

    def iter_products(self, *args, **kwargs):
        return self.browser.iter_products()

    def fill_product_and_history_details(self, product_obj, history_obj):
        return self.browser.fill_product_and_history_details(product_obj, history_obj)

    def has_feedbacks(self):
        return False
