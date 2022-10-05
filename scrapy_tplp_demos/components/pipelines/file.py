import os.path
import uuid

import aiofiles
from itemadapter import ItemAdapter
from scrapy.utils.defer import deferred_f_from_coro_f

from scrapy_tplp_demos.components.utils import CommonUtil
from scrapy_tplp_demos.components.utils.secure import SecureUtil


class FilePipeline:

    @deferred_f_from_coro_f
    async def process_item(self, item, spider):
        item = ItemAdapter(item).asdict()
        path = item['path'] or 'files'
        filename = item['filename'] or SecureUtil.md5(str(uuid.uuid1()) + str(uuid.uuid4()))
        content = item['content'] or ''
        encoding = item['encoding'] or 'UTF-8'

        filepath = os.path.abspath(os.path.join(path, filename))
        CommonUtil.mk_dir(filepath)

        if isinstance(content, str):
            file = await aiofiles.open(filepath, "w", encoding=encoding)
            await file.write(content)
            await file.flush()
            await file.close()
        else:
            file = await aiofiles.open(filepath, "wb")
            await file.write(content)
            await file.flush()
            await file.close()

        return item
