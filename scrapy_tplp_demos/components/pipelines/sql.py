import asyncio

from databases import Database
from scrapy.exceptions import NotConfigured
from scrapy.utils.defer import deferred_f_from_coro_f


class DatabaseWithTimeout(Database):
    async def __aexit__(self, exc_type, exc_value, traceback):
        return await asyncio.wait_for(
            super().__aexit__(exc_type, exc_value, traceback),
            timeout=60
        )


class SqlPipeline:

    def __init__(self, mysql_db_uri, mysql_table_name, db_mode, db_primary_key, db_update_exclude_fields):
        self.mysql_db_uri = mysql_db_uri
        self.client = DatabaseWithTimeout(mysql_db_uri)
        self.mysql_table_name = mysql_table_name
        self.db_mode = db_mode

        if len(db_primary_key) > 0:
            self.db_primary_key = db_primary_key
        else:
            self.db_primary_key = ['id']

        if len(db_update_exclude_fields) > 0:
            self.db_update_exclude_fields = db_update_exclude_fields

    @classmethod
    def from_crawler(cls, crawler):
        mysql_db_uri = crawler.settings.get("MYSQL_DB_URI") or ''
        mysql_table_name = crawler.settings.get("MYSQL_TABLE_NAME") or ''
        if '' == mysql_db_uri and '' == mysql_table_name:
            raise NotConfigured('请先填写存储设置！【MYSQL_DB_URI】和【MYSQL_TABLE_NAME】')
        db_mode = crawler.settings.get("DB_MODE") or 'insert'
        db_primary_key = list(str(x) for x in crawler.settings.get("DB_PRIMARY_KEY"))
        db_update_exclude_fields = list(str(x) for x in crawler.settings.get("DB_UPDATE_EXCLUDE_FIELDS"))
        return cls(mysql_db_uri, mysql_table_name, db_mode, db_primary_key, db_update_exclude_fields)

    @deferred_f_from_coro_f
    async def open_spider(self, spider):
        await self.client.connect()

    @deferred_f_from_coro_f
    async def close_spider(self, spider):
        await self.client.disconnect()

    async def process_item(self, item, spider):
        # if isinstance(item, ScrapyTplpDemosItem):
        #     multi_table_name = ''

        item_convert = {key: str(value) for (key, value) in item.items()}

        if 'update' == self.db_mode:
            new_item = {}
            for (key, value) in item_convert.items():
                if key not in self.db_update_exclude_fields or key in self.db_primary_key:
                    new_item.update({key: value})

            update = [F'{field}=:{field}' for field in item_convert.keys() if
                      field not in self.db_update_exclude_fields]
            where = [f'{field}=:{field}' for field in self.db_primary_key]
            sql = F'UPDATE {self.mysql_table_name} SET {",".join(update)} WHERE {" and ".join(where)};'
            await self.client.execute(sql, new_item)

        else:
            fields = ','.join(item_convert.keys())
            values = ','.join((F':{field}' for field in item_convert.keys()))
            sql = F'INSERT IGNORE INTO {self.mysql_table_name}({fields}) VALUES({values});'

            await self.client.execute(sql, dict(item_convert))
        return item
