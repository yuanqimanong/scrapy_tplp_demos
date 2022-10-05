import json

import jsonpath_ng
from scrapy.http import TextResponse


class ResponseParser(TextResponse):

    def __init__(self, text_response):
        self.text_response = text_response
        self._cached_jsonpath_result = None

    def __getattr__(self, item):
        if hasattr(self.text_response, item):
            return getattr(self.text_response, item)

    @property
    def text(self):
        return super().text

    def jsonpath(self, jsonpath_expression: str):
        _json_data = ''
        if self._cached_jsonpath_result is None:
            _json_data = json.loads(self.text)
        elif '' != self._cached_jsonpath_result:
            _json_data = json.loads(self._cached_jsonpath_result)
        else:
            return self

        _jsonpath_expression = jsonpath_ng.parse(jsonpath_expression)
        _result_list = _jsonpath_expression.find(_json_data)
        if len(_result_list) == 0:
            self._cached_jsonpath_result = ''
            return self
        if len(_result_list) == 1:
            self._cached_jsonpath_result = json.dumps(_result_list[0].value)
            return self
        if len(_result_list) > 1:
            _list = []
            for _ in _result_list:
                _list.append(_.value)
            self._cached_jsonpath_result = json.dumps(_list)
            return self

    def get(self, default=None):
        _result = None
        if self._cached_jsonpath_result is not None and '' != self._cached_jsonpath_result:
            _result_list = json.loads(self._cached_jsonpath_result)
            if isinstance(_result_list, list) and len(_result_list) == 1:
                _result = _result_list[0]
            else:
                _result = _result_list

        if '' == self._cached_jsonpath_result or '' == _result or _result is None:
            self._cached_jsonpath_result = None
            return default or _result

        self._cached_jsonpath_result = None
        return _result
