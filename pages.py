from testgneur.core.browser.pages import HTMLPage, JsonPage
from testgneur.core.browser.filters.standard import CleanText, CleanDecimal
from testgneur.modules.practicefarma.alchemy.tables import Category, Product, History, Meta
from testgneur.core.browser.filters.json import Dict
from urllib.parse import urljoin
import time, re, json, time, math
from lxml import etree, html
from testgneur.core.browser.filters.base import ItemNotFound
from mbackend.tools.exceptions.ecommerce.exceptions import CategoryDesactivated

class HomePage(HTMLPage):

    def iter_meta(self):
        script = CleanText('//script[contains(text(),"menuData") and contains(text(),"Medicine")]')(self.doc)
        decoded_script = script.encode().decode('unicode_escape')
        json_string = re.search(r'\{.*\}', decoded_script)
        if json_string:
            json_data = json_string.group(0)
            data = json.loads(json_data)
            cat_child = Dict('children/1/3/children/1/3/children/3/children/1/3/children/1/3')(data)
            menu_data = Dict('menuData/sideMenu/data')(cat_child)
            assert menu_data
            for item in menu_data:
                meta_obj = Meta()
                id = Dict('mi_id')(item)
                name = Dict('mi_name')(item)
                meta_slug = Dict('mi_url')(item)
                input(id)
                input(meta_slug)
                assert 'https' not in meta_slug
                assert self.browser.BASEURL
                meta_obj.slug = meta_slug
                meta_obj.url = urljoin(self.browser.BASEURL, meta_slug)
                assert meta_obj.url.count('https') == 1
                yield meta_obj
        #from lxml.etree import tostring
        #input(tostring(script_item))

    def get_target_json(self, parent_id, category_menu_data):
        parent_json = list(filter(lambda item: Dict("mi_id")(item) == parent_id, category_menu_data))
        assert len(parent_json)==1
        return parent_json[0]

    def iter_categories(self):
        script = CleanText('//script[contains(text(),"menuData") and contains(text(),"Medicine")]')(self.doc)
        decoded_script = script.encode().decode('unicode_escape')
        json_string = re.search(r'\{.*\}', decoded_script)
        if json_string:
            json_data = json_string.group(0)
            data = json.loads(json_data)
            cat_child = Dict('children/1/3/children/1/3/children/3/children/1/3/children/1/3')(data)
            menu_data = Dict('menuData/sideMenu/data')(cat_child)
            assert menu_data
            for item in menu_data:
                segment_id = Dict('mi_id')(item)
                segment_name = Dict('mi_name')(item)
                segment_slug = Dict('mi_url')(item)
                assert segment_id
                category_menu_data = self.browser.get_category_menu_data(segment_id)
                for item in category_menu_data:
                    sub_segment_name = None
                    sub_sub_segment_name = None
                    sub_sub_sub_segment_name = None

                    parent_id = Dict("mi_parent_mi_id")(item)
                    if parent_id and parent_id !=segment_id:
                        parent_json = self.get_target_json(parent_id, category_menu_data)
                        parent_name = Dict("mi_name")(parent_json)

                        parent_parent_id = Dict("mi_parent_mi_id")(parent_json)
                        if parent_parent_id and parent_parent_id !=segment_id:
                            parent_parent_json = self.get_target_json(parent_parent_id, category_menu_data)
                            parent_parent_name = Dict("mi_name")(parent_parent_json)

                            parent_parent_parent_id = Dict("mi_parent_mi_id")(parent_parent_json)
                            if parent_parent_parent_id and parent_parent_parent_id !=segment_id:
                                parent_parent_parent_json = self.get_target_json(parent_parent_parent_id, category_menu_data)
                                parent_parent_parent_name = Dict("mi_name")(parent_parent_parent_json)
                                
                                parent_parent_parent_parent_id = Dict("mi_parent_mi_id")(parent_parent_parent_json)
                                if parent_parent_parent_parent_id and parent_parent_parent_parent_id !=segment_id:
                                    raise Exception(f"handle parent_parent_parent_id: {parent_parent_parent_id}")
                                else:
                                    sub_segment_name = parent_parent_parent_name
                                    sub_sub_segment_name = parent_parent_name
                                    sub_sub_sub_segment_name = parent_name

                            else:
                                sub_segment_name = parent_parent_name
                                sub_sub_segment_name = parent_name
                        else:
                            sub_segment_name = parent_name
                    
                    category_obj = Category()
                    category_obj.slug = Dict("mi_url")(item)
                    assert 'https' not in category_obj.slug
                    category_obj.url = urljoin(self.browser.BASEURL, category_obj.slug)
                    category_obj.category = Dict("mi_name")(item)
                    assert category_obj.category
                    category_obj.segment = segment_name
                    category_obj.sub_segment = sub_segment_name
                    category_obj.sub_sub_segment = sub_sub_segment_name
                    #input(category_obj.__dict__)
                    yield category_obj

class CategoryApiPage(JsonPage):

    def iter_json_category(self):
        assert Dict("status")(self.doc)=="success"
        assert Dict("total")(self.doc)>0
        print(f'TOTAL CATEGORY: {Dict("total")(self.doc)}')
        category_json_items =  Dict("data")(self.doc)
        assert category_json_items
        return category_json_items

class BrandListApiPage(JsonPage):
    def iter_brand_categories(self):
        assert Dict("status")(self.doc)=="success"
        assert Dict("total")(self.doc)>2000
        print(f'TOTAL BRANDS: {Dict("total")(self.doc)}')
        category_json_items =  Dict("data")(self.doc)
        assert category_json_items
        for item in category_json_items:
            brand_id = Dict('pb_id')(item)
            brand_name = Dict('pb_name')(item)
            brand_total_products = Dict('total_product')(item)

            category_obj = Category()
            slug = f'/brand/{str(brand_id)}'
            category_obj.slug = f'{slug}/total_products={str(brand_total_products)}'
            assert 'https' not in category_obj.slug
            category_obj.url = urljoin(self.browser.BASEURL, slug)
            category_obj.category = brand_name
            assert category_obj.category
            category_obj.meta_category = 'Brands'
            #input(category_obj.__dict__)
            yield category_obj

def clean_html(full_text):
    if full_text is None or full_text=='':
        return None
    try:
        full_text = CleanText().filter(full_text)
        doc = etree.fromstring(full_text, parser=html.HTMLParser())
        full_text = CleanText('//text()')(doc)
        return full_text
    except etree.XMLSyntaxError:
        full_text = CleanText().filter(full_text.encode('utf-8').decode('unicode_escape'))
        return full_text

class ProductsApiPage(JsonPage):

    def empty_category(self):
        status = Dict('status', default=None)(self.doc)
        message = Dict('message', default=None)(self.doc)
        return bool(status=='fail' and message=='No product found')

    def get_products_per_page(self):
        if 'lab.arogga.com/lab-search' in self.url:
            return 20
        else:
            return 18

    def get_total_pages(self):
        total_results = self.get_total_products()
        products_per_page = self.get_products_per_page()
        return math.ceil(total_results/products_per_page)
    
    def get_total_products(self):
        try:
            if 'lab.arogga.com/lab-search' in self.url:
                total_results = Dict('count')(self.doc)
            else:
                total_results = Dict('total')(self.doc)
        except ItemNotFound as e:
            assert Dict('status')(self.doc)=='fail'
            assert Dict('message')(self.doc)=='No product found'
            raise CategoryDesactivated

        assert total_results is not None
        return total_results

    def formated_output(self,product_item,key):
        item_list = Dict(key)(product_item)
        item_texts = []
        for item in item_list:
            item_en = Dict('en')(item)
            item_bn = Dict('bn',default=None)(item)
            if item_bn and item_en != item_bn:
                item_en = f"{item_en} | {item_bn}"
            item_texts.append(CleanText().filter(item_en))
        return ", ".join(item_texts)

    def iter_products(self):
        assert Dict("status", default=None)(self.doc)=="success" or Dict("success", default=None)(self.doc) is True
        total_products = Dict("total", default=None)(self.doc) or Dict("count",default=None)(self.doc)
        assert total_products>0
        print(f'TOTAL PRODUCTS: {total_products}')

        if 'lab.arogga.com/lab-search' in self.url:
            return self.iter_lab_products()
        else:
            return self.iter_normal_products()
            

    def iter_lab_products(self):
        products_per_page = self.get_products_per_page()
        assert Dict("success")(self.doc)==True
        products_json_items = Dict("data/results")(self.doc)
        for position, product_item in enumerate(products_json_items, start=1):
            product_id = Dict('id')(product_item)
            name = Dict('name/en')(product_item)
            name_bn = Dict('name/bn')(product_item)
            if name !=name_bn:
                name = f"{name} | {name_bn}"

            image_url = Dict('bannerImage/web')(product_item)
            slug = Dict('slug')(product_item)
            subTitle = Dict('subTitle/en')(product_item)
            subTitle_bn = Dict('subTitle/bn', default=None)(product_item)
            if subTitle_bn and subTitle !=subTitle_bn:
                subTitle = f"{subTitle} | {subTitle_bn}"
            subTitle = CleanText().filter(subTitle)

            knownAs = self.formated_output(product_item,'knownAs') or None
            sampleRequirements = self.formated_output(product_item,'sampleRequirements') or None
            testRequirements = self.formated_output(product_item,'testRequirements') or None

            bookedCount = Dict('bookedCount')(product_item)
            testCount = Dict('testCount')(product_item)
            regularPrice = Dict('regularPrice')(product_item)
            discountPrice = Dict('discountPrice')(product_item)
            discountPercent = Dict('discountPercent')(product_item)
            reportAvailableHour = Dict('reportAvailableHour')(product_item)
            status = Dict('status')(product_item)
            product_obj = Product()
            product_obj.name = name
            product_obj.url = 'https://www.arogga.com/lab-test/tests/'+slug
            product_obj.slug = product_obj.url.split('/',3)[-1]
            product_obj.sku_found = False
            product_obj.sku = None
            product_obj.image_url = image_url
            product_obj.currency = 'BDT'
            product_obj.internal_code = product_id
            
            history_obj = History()
            history_obj.ordered_count = bookedCount
            history_obj.test_count = testCount
            history_obj.feature = f"Report in {reportAvailableHour} hours"
            history_obj.subtitle = subTitle
            history_obj.price = round(float(discountPrice), 2)
            history_obj.crossed_out_price = round(float(regularPrice), 2)
            history_obj.discount_claim = f"{round(float(discountPercent))}% OFF"
            if history_obj.price == history_obj.crossed_out_price:
                assert float(discountPercent) == 100.0 or float(discountPercent) == 0.0
                history_obj.crossed_out_price = None
                history_obj.discount_claim = None
            history_obj.availability_bool = bool(status=='active')
            if history_obj.availability_bool:
                history_obj.availability = 'Service avilable'
            history_obj.images_count = 1
            history_obj.known_as = knownAs
            history_obj.sample_requirement = sampleRequirements
            history_obj.test_requirement = testRequirements

            history_obj.position = position
            history_obj.products_per_page = products_per_page
            yield product_obj, history_obj
    
    def iter_normal_products(self):
        products_per_page = self.get_products_per_page()
        products_json_items =  Dict("data")(self.doc)
        for position, product_item in enumerate(products_json_items, start=1):
            product_obj = Product()
            history_obj = History()
            product_obj.name = Dict('p_name')(product_item)
            product_obj.generic_name = Dict('p_generic_name')(product_item)
            product_obj.product_type = Dict('p_type')(product_item)
            product_obj.brand = Dict('p_manufacturer')(product_item) or Dict('p_brand')(product_item)

            product_obj.internal_code = Dict('id')(product_item) or Dict('p_id')(product_item) #for url
            assert product_obj.internal_code

            history_obj.viewed_count = Dict('productCountViewed', default=None)(product_item)
            history_obj.ordered_count = Dict('productCountOrdered', default=None)(product_item)
            history_obj.wishlist_count = Dict('productCountWishlist', default=None)(product_item)
            product_obj.description = clean_html(Dict('p_description', default=None)(product_item)) or None
            if product_obj.description:
                history_obj.description_size = len(product_obj.description)
            history_obj.subtitle = clean_html(CleanText().filter(Dict('p_meta_description')(product_item)) or None)

            history_obj.score = Dict('p_trending_score', default=None)(product_item)

            product_info = Dict('pv')(product_item)
            assert len(product_info)==1

            image_lists = Dict('attachedFiles_p_images')(product_item) or Dict('attachedFiles_pv_images')(product_info[0])
            product_obj.image_url=None
            if len(image_lists)>0:
                product_obj.image_url = Dict('src')(image_lists[0])
                images = []
                for image in image_lists:
                    img = Dict('src')(image)
                    images.append(img)
                product_obj.image_urls = ", ".join(images)
            history_obj.images_count = len(image_lists)

            p_strength = Dict('p_strength', default=None)(product_item)
            p_form = Dict('p_form', default=None)(product_item)

            product_obj.format_full = CleanText().filter(Dict('pu_base_unit_label')(product_info[0])) or None
            pv_attributes = Dict('pv_attribute')(product_info[0])
            if pv_attributes:
                pv_attributes = pv_attributes.values()
            pv_attribute = " ".join(str(value) for value in pv_attributes) or None
            if p_strength is not None and p_strength!="":
                product_obj.format_full = f"{p_strength} ({p_form})"
            elif pv_attribute is not None and (pv_attribute != product_obj.format_full):
                if any(c.isdigit() for c in pv_attribute) and any(c.isalpha() for c in pv_attribute):
                    product_obj.format_full = f"{pv_attribute} ({product_obj.format_full})"
                else:
                    product_obj.format_full = f"{product_obj.format_full} ({pv_attribute})"

            product_obj.format = None
            product_obj.format_unit = None
            if product_obj.format_full:
                pformat = re.search(r'\d+(\.\d+)?', product_obj.format_full)
                if pformat:
                    product_obj.format = float(pformat.group())
                pformat_unit = re.search('[a-zA-ZàâäôéèëêïîçùûüÿæœÀÂÄÔÉÈËÊÏÎŸÇÙÛÜÆŒ]+', product_obj.format_full)
                if pformat_unit:
                    product_obj.format_unit = pformat_unit.group()

            product_obj.sku = Dict('pv_sku')(product_info[0])
            product_obj.sku_found = bool(product_obj.sku)

            pv_id = Dict('pv_id')(product_info[0]) #for url

            discountPrice = Dict('pv_b2c_price')(product_info[0])
            history_obj.price = round(float(discountPrice), 3)

            unit_discountPrice = Dict('pv_b2c_discounted_price')(product_info[0])
            history_obj.unit_price = round(float(unit_discountPrice), 3)
            

            regularPrice = Dict('pv_b2c_mrp')(product_info[0])
            history_obj.crossed_out_price = round(float(regularPrice), 3)

            unit_regularPrice = Dict('pv_mrp')(product_info[0])
            history_obj.unit_crossed_out_price = round(float(unit_regularPrice), 3)

            discountPercent = Dict('pv_b2c_discount_percent')(product_info[0])
            history_obj.discount_claim = f"{round(float(discountPercent))}% OFF"

            if history_obj.price == history_obj.crossed_out_price:
                history_obj.crossed_out_price = None
                history_obj.discount_claim = None
            
            if history_obj.unit_price >= history_obj.unit_crossed_out_price:
                history_obj.unit_crossed_out_price = None
                history_obj.unit_price = None
                total_items = Dict('pu_b2c_base_unit_multiplier')(product_info[0])
                if total_items>0:
                    history_obj.unit_price = round(float(history_obj.price/total_items),2)
                    if history_obj.crossed_out_price:
                        history_obj.unit_price = round(float(history_obj.crossed_out_price/total_items),2)

            product_obj.currency = 'BDT'
            
            stocks = Dict('pv_stock_status')(product_info[0])
            if int(stocks)>0:
                history_obj.availability = 'In stock'
                history_obj.availability_bool = True
            else:
                history_obj.availability = 'Out of stock'
                history_obj.availability_bool = False
            
            if (history_obj.crossed_out_price or history_obj.unit_crossed_out_price) and discountPercent:
                print(f'discount percent: {int(discountPercent)}')
                try:
                    assert 0 < int(discountPercent) < 100
                except AssertionError:
                    assert history_obj.availability_bool is False
                    history_obj.crossed_out_price = None
                    history_obj.unit_crossed_out_price = None
                    history_obj.discount_claim = None

            slug = Dict('pv_slug')(product_info[0]) #for url, optional

            history_obj.position = position
            history_obj.products_per_page = products_per_page
            product_obj.url = f'https://www.arogga.com/product/{str(product_obj.internal_code)}{"/" + slug if slug else ""}?pv_id={str(pv_id)}'
            product_obj.slug = product_obj.url.split('/',3)[-1]
            #input(product_obj.__dict__)
            #input(history_obj.__dict__)
            yield product_obj, history_obj

class CategoryPage(HTMLPage):

    PRODUCTS_PER_PAGE = 48

    def get_lab_test_tag(self):
        script = CleanText("//script[contains(text(),'\\\"tag\\\":')]")(self.doc)
        decoded_script = script.encode().decode('unicode_escape')
        json_string = re.search(r'\{.*\}', decoded_script)
        if json_string:
            json_data = json_string.group(0)
            data = json.loads(json_data)
            all_tags = Dict("allTags")(data)
            formatted_tags = json.dumps(all_tags, separators=(',', ':'))
            assert formatted_tags
            return formatted_tags

    def get_meta(self, meta_obj):
        products_per_page = len(self.doc.xpath("//div[@id='products']/div"))
        page_elems = self.doc.xpath("//ul[@class='pagination']/li/a/text()")
        if len(page_elems)>0:
            total_pages = max(map(int, filter(lambda x: x.isdigit(), page_elems)))
            assert total_pages
            meta_obj.total_products = total_pages * products_per_page
        else:
            #empty meta_page. i.e: 0 products
            assert meta_obj.slug == '/fr/taxons/parapharmacie/dermocosmetique'
            meta_obj.is_desactivated = True
        self.logger.warning(meta_obj.__dict__)
        return meta_obj

    def get_total_pages(self):
        total_pages = CleanDecimal('//li[contains(@class, "page-item") and position()=last()-1]/a', default=1)(self.doc)
        return total_pages

    def iter_urls(self):
        for product_div in self.doc.xpath('//div[contains(@class, "product-box")]'):
            url = urljoin(self.browser.BASEURL, CleanText('./a[contains(@class, "card")]/@href')(product_div))
            yield url

    def iter_products(self):
        position = 0
        for product_div in self.doc.xpath('//div[contains(@class, "product-box")]'):
            product_obj = Product()
            position += 1

            slug = CleanText('./a[contains(@class, "card")]/@href')(product_div)
            slug = slug[1:]
            product_obj.slug = slug
            product_obj.url = urljoin(self.browser.BASEURL, CleanText('./a[contains(@class, "card")]/@href')(product_div))

            history_obj = History()
            history_obj.position = position
            history_obj.products_per_page = self.PRODUCTS_PER_PAGE
            yield product_obj, history_obj


""" class EmptyProductPage(HTMLPage):
    def is_here(self):
        products_container = self.doc.xpath('//div[@id="main-content"]')[0]
        container = products_container.xpath('./div[@class="container"]')
        return bool(container) """

class ProductPage(HTMLPage):
    def is_here(self):
        products_container = self.doc.xpath('//div[contains(@class,"TestDetails_testDetails_body") or contains(@class,"product_product_details")]')
        return bool(products_container)
    
    def get_from_html(self, doc, div_id):
        print(div_id)
        short_text = self.doc.xpath(f'//div[@id="id_risk_assessments"]//div[@id="{div_id}"]/div[contains(@class,"TestDetailsOverviewCard_description")]//text()')
        short_text = ''.join(short_text).splitlines() #join all texts and splited by new lines
        short_text = CleanText().filter(max(short_text, key=len)) # get sentance with max length
        short_text = re.split(r'[.:"*?]', short_text)
        short_text = CleanText().filter(max(short_text, key=len))
        short_text = short_text.replace('>','\\u003e').replace('<','\\u003c').replace('<','\\u0026')
        #short_text = str(short_text.encode())[2:-1].replace('>','\\u003e').replace('<','\\u003c').replace('\\xe2\\x80\\x99', '’')
        full_text = CleanText(f'//script[contains(text(),"{short_text}")]')(self.doc)
        full_text = re.search(r'\"(.*)\"', full_text).group(1)
        assert short_text in full_text
        return clean_html(full_text)

    def fill_product_and_history_details(self, product_obj, history_obj):
        if 'arogga.com/lab-test/tests/' in self.url:
            return self.fill_labs_products(product_obj, history_obj)
        else:
            return self.fill_normal_products(product_obj, history_obj)

    def fill_labs_products(self, product_obj, history_obj):
        product_script = CleanText(f'//script[contains(text(),"{product_obj.internal_code}")]')(self.doc)
        decoded_script = product_script.encode().decode('unicode_escape').encode('latin1').decode('utf-8')
        json_string = re.search(r'\{.*\}', decoded_script)
        assert json_string
        #if json_string:
        json_data = json_string.group(0)
        data = json.loads(json_data)
        labTestsDetails = Dict('labTestsDetails')(data)
        assert labTestsDetails

        bannerImages = Dict('bannerImages')(labTestsDetails)
        image_lists = []
        for bannerImage in bannerImages:
            image = Dict('src')(bannerImage)
            image_lists.append(image)
        if not image_lists:
            image_lists.append(Dict('bannerImage/web')(labTestsDetails))
        image_urls = ", ".join(image_lists)

        fastingRequired = Dict('fastingRequired')(labTestsDetails)

        short_description = Dict('description/en')(labTestsDetails)
        short_description_bn = Dict('description/bn')(labTestsDetails)
        if short_description != short_description_bn:
            short_description = f"{short_description} | {short_description_bn}"
        
        itemType = Dict('itemType')(labTestsDetails)
        
        overview = risk_assessment = ranges = requirement_interpretation = sample_types = ''

        riskAssessments = Dict('riskAssessments')(data)
        for riskAssessment in riskAssessments:
            full_text = CleanText().filter(Dict('description/en')(riskAssessment))
            if Dict('detailsType')(riskAssessment) == 'overview':
                overview = full_text if not full_text.startswith('$') else self.get_from_html(self.doc, 'overview')
            if Dict('detailsType')(riskAssessment) == 'risk_assessment':
                risk_assessment = full_text if not full_text.startswith('$') else self.get_from_html(self.doc, 'risk_assessment')
            if Dict('detailsType')(riskAssessment) == 'ranges':
                ranges = full_text if not full_text.startswith('$') else self.get_from_html(self.doc, 'ranges')
            if Dict('detailsType')(riskAssessment) == 'requirement_interpretation':
                requirement_interpretation = full_text if not full_text.startswith('$') else self.get_from_html(self.doc, 'requirement_interpretation')
            if Dict('detailsType')(riskAssessment) == 'sample_types':
                sample_types = full_text if not full_text.startswith('$') else self.get_from_html(self.doc, 'sample_types')
        description_dict = f"{{short_description: {short_description}, overview: {overview}, risk_assessment: {risk_assessment}, requirement_interpretation: {requirement_interpretation}, sample_types: {sample_types}}}"

        product_obj.image_urls = image_urls
        product_obj.description = description_dict
        product_obj.product_type = itemType
        history_obj.images_count = len(image_lists)
        history_obj.fasting_required = fastingRequired
        history_obj.description_size = len(product_obj.description)
    
    def fill_normal_products(self, product_obj, history_obj):
        product_script = CleanText('//script[contains(text(), \'"@type":"Product"\')]/text()')(self.doc)
        product_dict = json.loads(product_script)
        product_obj.name = Dict('name',default=None)(product_dict) or product_obj.name

        image_url = Dict('image',default=None)(product_dict)
        if isinstance(image_url, dict):
            assert product_obj.image_url is None
            image_url = Dict('src',default=None)(image_url)
        else:
            image_url = CleanText('//div[contains(@class,"product_details_body")]//div[@class="swiper"]//div[@class="swiper-slide"]//img/@src')(self.doc) or None
        image_url = 'https://www.arogga.com' + image_url if image_url and 'https:' not in image_url else image_url
        
        if product_obj.image_url is None:
            product_obj.image_url =  image_url
        if product_obj.image_url and product_obj.image_urls is None:
            product_obj.image_urls = ','.join([product_obj.image_url])
            history_obj.images_count = 1

        sku = Dict('sku',default=None)(product_dict)
        if not product_obj.sku_found:
            assert product_obj.sku is None
            product_obj.sku = sku
        if product_obj.sku is not None:
            product_obj.sku_found = True

        product_obj.brand = Dict('brand/name',default=None)(product_dict) or product_obj.brand
        history_obj.rating = float(Dict('aggregateRating/ratingValue',default=None)(product_dict))
        history_obj.rating_count = int(Dict('aggregateRating/reviewCount',default=None)(product_dict))

        product_obj.currency = Dict('offers/priceCurrency',default=None)(product_dict) or product_obj.currency
        price = Dict('offers/price',default=None)(product_dict)
        #assert round(float(price), 2) == history_obj.price
        availability = Dict('offers/availability',default=None)(product_dict)
        """ if availability == 'https://schema.org/InStock':
            assert history_obj.availability_bool
            assert history_obj.availability == 'In stock'
        else:
            assert history_obj.availability == 'Out of stock' """
        
        history_obj.seller_name = Dict('offers/seller/name',default=None)(product_dict)
        shippingLabel = Dict('offers/shippingDetails/shippingLabel',default=None)(product_dict)
        deliveryTime = Dict('offers/shippingDetails/deliveryTime/shippingTime',default=None)(product_dict)
        history_obj.feature = f'{shippingLabel}{" | "+deliveryTime if deliveryTime else ""}'

        product_obj.original_url = Dict('url',default=None)(product_dict) or Dict('offers/url',default=None)(product_dict)
        #input(product_obj.__dict__)
        #input(history_obj.__dict__)


class MetaPage(HTMLPage):
   def iter_meta(self):
       return Meta()

   def get_meta(self, meta_obj):
        _products_per_page = self.doc.xpath(".//div[@class='ui right floated small header']//div[@class='ui inline dropdown sylius-paginate']//text()")
        _products_per_page = [CleanText().filter(i) for i in _products_per_page if i != '']
        if _products_per_page:
            _products_per_page = CleanDecimal().filter(_products_per_page[0])
            _total_pages = self.doc.xpath(".//ul[@class='pagination']/li[@class='page-item']/a//text()")[-1]
            _total_products = int(_total_pages) * int(_products_per_page)
            assert _total_products
            meta_obj.total_products = _total_products
            return meta_obj
        else:
            raise Exception(
                    'No total_products in meta',
                    vars(meta_obj)
                    )
            return 0


class BrandPage(HTMLPage):
    pass
