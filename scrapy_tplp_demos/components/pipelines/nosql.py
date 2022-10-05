from itemadapter import ItemAdapter
from motor import motor_asyncio
from pymongo.errors import DuplicateKeyError
from scrapy.exceptions import NotConfigured, DropItem


class MongoDBPipeline:

    def __init__(self, mongo_db_uri, mongo_db_name, mongo_collection_name, db_mode, db_primary_key,
                 db_update_exclude_fields):
        self.client = None
        self.mongo_db_uri = mongo_db_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection_name = mongo_collection_name

        self.db_mode = db_mode
        if len(db_primary_key) > 0:
            self.db_primary_key = db_primary_key
        else:
            self.db_primary_key = ['id']

        if len(db_update_exclude_fields) > 0:
            self.db_update_exclude_fields = db_update_exclude_fields

    @classmethod
    def from_crawler(cls, crawler):
        mongo_db_uri = crawler.settings.get("MONGO_DB_URI") or ''
        mongo_db_name = crawler.settings.get("MONGO_DB_NAME") or ''
        mongo_collection_name = crawler.settings.get("MONGO_COLLECTION_NAME") or ''
        if '' == mongo_db_uri and '' == mongo_db_name and '' == mongo_collection_name:
            raise NotConfigured('请先填写存储设置！【MONGO_DB_URI】、【MONGO_DB_NAME】和【MONGO_COLLECTION_NAME】')

        db_mode = crawler.settings.get("DB_MODE") or 'insert'
        db_primary_key = list(str(x) for x in crawler.settings.get("DB_PRIMARY_KEY"))
        db_update_exclude_fields = list(str(x) for x in crawler.settings.get("DB_UPDATE_EXCLUDE_FIELDS"))

        return cls(mongo_db_uri, mongo_db_name, mongo_collection_name, db_mode, db_primary_key,
                   db_update_exclude_fields)

    def open_spider(self, spider):
        self.client = motor_asyncio.AsyncIOMotorClient(self.mongo_db_uri)

    def close_spider(self, spider):
        self.client.close()

    async def process_item(self, item, spider):
        db = self.client[self.mongo_db_name]
        collection = db[self.mongo_collection_name]
        document = ItemAdapter(item).asdict()

        try:
            if 'update' == self.db_mode:
                _id = document['id']
                for key in self.db_update_exclude_fields:
                    if key in document:
                        document.pop(key)

                await collection.update_one({'_id': _id}, {'$set': document})
                return item
            else:
                document['_id'] = document.pop('id')
                await collection.insert_one(document)
                return item
        except DuplicateKeyError:
            raise DropItem('主键重复 ==> [%s]' % item)
