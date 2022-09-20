import httpx
from lxml import html
import pandas as pd
from config import Config
from sqlalchemy import create_engine, text

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, client_encoding="utf8")


class Crawler:
    def __init__(self):
        pass

    def get_link(self, url):
        r = httpx.get(url)
        content = html.fromstring(r.content)
        return content

    def crawl(self):
        pass

    def save(self, df):
        with engine.begin() as conn:

            sql_list = [f"('{eshop}')" for eshop in df.eshop.unique()]
            sql_str = ",".join(sql_list)
            conn.execute(
                f"""
                INSERT INTO eshop (name)
                VALUES {sql_str}
                ON CONFLICT (name)
                DO NOTHING;
                """
            )

            sql_list = [
                f"('{manufacturer}')" for manufacturer in df.manufacturer.unique()
            ]
            sql_str = ",".join(sql_list)
            conn.execute(
                f"""
                INSERT INTO manufacturer (name)
                VALUES {sql_str}
                ON CONFLICT (name)
                DO NOTHING;
                """
            )

            sql_list = [
                f"""('{title.replace("'", "''")}', '{url.replace("'", "''")}', '{manufacturer}', '{eshop}')"""
                for title, manufacturer, eshop, url, price in list(
                    df.itertuples(index=False, name=None)
                )
            ]
            sql_str = ",".join(sql_list)
            conn.execute(
                text(
                    f"""
                WITH inputvalues(name, url, manufacturer, eshop) AS (
                    VALUES {sql_str}
                )
                INSERT INTO product (name, url, manufacturer_id, eshop_id)
                SELECT d.name, d.url, manufacturer.id, eshop.id
                FROM inputvalues as d
                INNER JOIN eshop ON eshop.name = d.eshop
                INNER JOIN manufacturer ON manufacturer.name = d.manufacturer
                ON CONFLICT
                DO NOTHING;
                """
                )
            )

            sql_list = [
                f"""((SELECT id FROM product WHERE name='{title.replace("'", "''")}'), {price}, now())"""
                for title, manufacturer, eshop, url, price in list(
                    df.itertuples(index=False, name=None)
                )
            ]
            sql_str = ",".join(sql_list)
            conn.execute(
                text(
                    f"""
                WITH inputvalues(id, price, date) AS (
                    VALUES {sql_str}
                )
                INSERT INTO store (product_id, price, date)
                SELECT d.id, d.price, d.date
                FROM inputvalues as d
                WHERE d.id IS NOT NULL;
                """
                )
            )


class CrawlerEurovaistine(Crawler):
    def __init__(self):
        super().__init__()

    def crawl(self):
        df = pd.DataFrame(columns=["title", "manufacturer", "eshop", "url", "price"])
        for manufacturer in [
            "uriage",
            "bioderma",
            "filorga",
            "vichy",
            "avene",
            "la roche-posay",
            "svr",
            "apivita",
        ]:

            page = 1
            while True:
                url = f"https://www.eurovaistine.lt/paieska/rezultatai?q={manufacturer}&page={page}"
                print(f"Getting url: {url}")
                content = super().get_link(url)

                elements = content.xpath('//div[@class="product-card"]')

                for element in elements:
                    _url = element.xpath('a[@class="product-card--link"]/@href')[0]
                    _title = element.xpath(
                        'div[@class="right-content"]/div[@class="product-card--title-box"]/div[1]/div[@class="product-card--title"]/text()'
                    )[0]
                    _title = _title.strip()
                    _manufacturer = manufacturer.capitalize()
                    _price = element.xpath(
                        'div[@class="right-content"]/div[@class="product-card--price"]/text()'
                    )[0]
                    _price = (
                        _price.strip()
                        .replace(",", ".")
                        .replace("&nbsp;", "")
                        .replace("\xa0", "")
                        .replace("€", "")
                    )
                    if not _price:
                        _price = element.xpath(
                            'div[@class="right-content"]/div[@class="product-card--price"]/s/text()'
                        )[0]
                        _price = (
                            _price.strip()
                            .replace(",", ".")
                            .replace("&nbsp;", "")
                            .replace("\xa0", "")
                            .replace("€", "")
                        )
                    _price = float(_price)
                    df = pd.concat(
                        [
                            df,
                            pd.DataFrame(
                                {
                                    "title": [_title],
                                    "url": [_url],
                                    "price": [_price],
                                    "manufacturer": [_manufacturer],
                                    "eshop": ["Eurovaistine"],
                                }
                            ),
                        ]
                    )
                preprocessed_len = len(df)
                df = df.drop_duplicates().reset_index(drop=True)
                afterprocessed_len = len(df)
                page += 1
                if len(elements) < 48 or (preprocessed_len != afterprocessed_len):
                    break
        return df


class CrawlerBenu(Crawler):
    def crawl(self):
        df = pd.DataFrame(columns=["title", "manufacturer", "eshop", "url", "price"])
        for manufacturer in [
            "uriage",
            "bioderma",
            "filorga",
            "vichy",
            "avene",
            "la roche-posay",
            "svr",
            "apivita",
        ]:
            url = f"https://www.benu.lt/paieskos-rezultatai?vars/search/{manufacturer}/pageSize/all/brand/{manufacturer}"
            r = httpx.get(url)
            print(f"Getting url: {url}")
            content = html.fromstring(r.content)
            elements = content.xpath('//div[@class="productsList__wrap"]/div/div')

            for element in elements:
                try:
                    _url = element.xpath(
                        'div/div[@class="bnProductCard__top"]/a[@class="bnProductCard__title"]/@href'
                    )[0]
                except Exception as e:
                    continue
                _title = element.xpath(
                    'div/div[@class="bnProductCard__top"]/a[@class="bnProductCard__title"]/h3/text()'
                )[0]
                _title = _title.strip()
                _manufacturer = manufacturer.capitalize()
                _price = element.xpath(
                    'div/div[@class="bnProductCard__bottom"]/div[@class="bnProductCard__price"]/span/span/span[1]/text()'
                )[0]
                _price = (
                    _price.strip()
                    .replace(",", ".")
                    .replace("&nbsp;", "")
                    .replace("\xa0", "")
                    .replace("€", "")
                )
                if not _price:
                    print(_title)
                    continue
                _price = float(_price)
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {
                                "title": [_title],
                                "url": [_url],
                                "price": [_price],
                                "manufacturer": [_manufacturer],
                                "eshop": ["Benu"],
                            }
                        ),
                    ]
                )
                df = df.drop_duplicates().reset_index(drop=True)
        return df


class CrawlerHerba(Crawler):
    def crawl(self):
        df = pd.DataFrame(columns=["title", "manufacturer", "eshop", "url", "price"])
        for manufacturer in ["uriage", "apivita"]:
            page = 1

            while True:
                url = f"https://www.herba.lt/catalogsearch/result/index/?p={page}&q={manufacturer}"
                print(f"Getting url: {url}")
                r = httpx.get(url)
                content = html.fromstring(r.content)
                elements = content.xpath('//div[@class="item-inner"]')

                titles = content.xpath('//h4[@class="product-name"]/a/text()')

                manufacturers = [manufacturer.capitalize()] * len(titles)

                urls = content.xpath('//h4[@class="product-name"]/a/@href')

                discounted_prices = content.xpath(
                    '//span[contains(@id, "product-price") and not(contains(@id, "side")) and @class!="regular-price"]/text()'
                )
                normal_prices = content.xpath(
                    '//span[@class="regular-price" and contains(@id, "product-price") and not(contains(@id, "side"))]/span/text()'
                )

                prices = [
                    price.strip()
                    .replace(",", ".")
                    .replace("&nbsp;", "")
                    .replace("\xa0", "")
                    .replace("€", "")
                    for price in discounted_prices + normal_prices
                ]
                prices = list(filter(None, prices))
                prices = list(map(float, prices))

                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {
                                "title": titles,
                                "url": urls,
                                "price": prices,
                                "manufacturer": manufacturers,
                                "eshop": ["Herba"] * len(prices),
                            }
                        ),
                    ]
                )

                preprocessed_len = len(df)
                df = df.drop_duplicates().reset_index(drop=True)
                afterprocessed_len = len(df)

                page += 1

                if len(prices) < 24 or (preprocessed_len != afterprocessed_len):
                    break

        return df


class CrawlerGintarine(Crawler):
    pass


if __name__ == "__main__":
    eurovaistine_crawler = CrawlerEurovaistine()
    temp_df = eurovaistine_crawler.crawl()
    # print(temp_df.head())
    # print(list(temp_df.itertuples(index=False, name=None)))
    eurovaistine_crawler.save(temp_df)
