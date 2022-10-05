import re

import ddddocr
from PIL import UnidentifiedImageError


class OcrUtil:

    @staticmethod
    def fix_b64img(img):
        return re.sub(r'data:image/.*?;base64,', '', img)

    @staticmethod
    def arithmetic(code, number_of_digit=(1, 1)):
        number_convertor = {'=': ['=', '等'],
                            '+': ['+', '加', 't'],
                            '-': ['-', '减', 'E'],
                            '*': ['*', '乘', 'X', 'x'],
                            '/': ['/', '除'],
                            '0': ['0', '〇', '零'],
                            '1': ['1', '一', '壹'],
                            '2': ['2', '二', '贰'],
                            '3': ['3', '三', '叁'],
                            '4': ['4', '四', '肆'],
                            '5': ['5', '五', '伍'],
                            '6': ['6', '六', '陆'],
                            '7': ['7', '七', '柒'],
                            '8': ['8', '八', '捌'],
                            '9': ['9', '九', '玖'],
                            '10': ['十', '拾'],
                            }
        convert_result = ''
        for _char in code:
            for key, value in number_convertor.items():
                if _char in value:
                    convert_result += key

        arithmetic_reg = ''
        for i in range(len(number_of_digit)):
            if i < len(number_of_digit) - 1:
                arithmetic_reg += r'(\d{1,' + str(number_of_digit[i]) + '})' + r'(\D)'
            else:
                arithmetic_reg += r'(\d{1,' + str(number_of_digit[i]) + '})'

        reg_result = re.match(r'^' + arithmetic_reg, convert_result)
        if reg_result:
            try:
                return eval(reg_result.group(0))
            except SyntaxError:
                return ''
        return ''

    @staticmethod
    def detect_character(img, old=False, use_gpu=False, gpu_device_id=0, import_onnx_path='', charsets_path=''):
        try:
            if use_gpu:
                ocr = ddddocr.DdddOcr(show_ad=False, det=False, old=old, use_gpu=True, device_id=gpu_device_id,
                                      import_onnx_path=import_onnx_path,
                                      charsets_path=charsets_path)
                return ocr.classification(img)
            else:
                ocr = ddddocr.DdddOcr(show_ad=False, det=False, old=old, use_gpu=False,
                                      import_onnx_path=import_onnx_path,
                                      charsets_path=charsets_path)
                return ocr.classification(img)
        except UnidentifiedImageError:
            return ''
