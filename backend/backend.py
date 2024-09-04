from testgneur.modules.practicefarma.alchemy.dao_manager import DaoManager
from testgneur.modules.practicefarma.alchemy.tables import Product
from testgneur.modules.practicefarma.core.backend import PharmaBackend
import argparse


class AroggaBackend(PharmaBackend):

    APPNAME = 'Application Arogga'
    VERSION = '1.0'
    COPYRIGHT = 'Copyright(C) 2024-MAHFUAR'
    DESCRIPTION = "Scraping Backend for Arogga"
    SHORT_DESCRIPTION = "Step-by-step Example of Arogga Scraping"

    def __init__(self):
        self.module_name = "arogga"
        PharmaBackend.__init__(self)
        self.has_login = False
        self.unique_product_attribute = "url"
        self.history_attributes = []
        self.setup_logging()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db")
    parser.add_argument("-t", "--test", action="store_true")
    args = parser.parse_args()

    crawler = AroggaBackend()
    crawler.set_engine_config(args.db, args.test)
    crawler.insert_template("https://www.arogga.com/", slug='arogga')
    crawler.insert_subdomain("https://www.arogga.com/")
    #crawler.insert_update_meta()
    crawler.insert_update_categories()
    #crawler.run(53)