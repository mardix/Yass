
import os
import re
import yaml
import mimetypes


MIMETYPE_MAP = {
    '.js':   'application/javascript',
    '.mov':  'video/quicktime',
    '.mp4':  'video/mp4',
    '.m4v':  'video/x-m4v',
    '.3gp':  'video/3gpp',
    '.woff': 'application/font-woff',
    '.woff2': 'font/woff2',
    '.eot':  'application/vnd.ms-fontobject',
    '.ttf':  'application/x-font-truetype',
    '.otf':  'application/x-font-opentype',
    '.svg':  'image/svg+xml',
}
MIMETYPE_DEFAULT = 'application/octet-stream'


def get_mimetype(filename):
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype:
        return mimetype

    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext in MIMETYPE_MAP:
        return MIMETYPE_MAP[ext]
    return MIMETYPE_DEFAULT



class dictdot(dict):
    """
    A dict extension that allows dot notation to access the data.
    ie: dict.get('key.key2.0.keyx'). Still can use dict[key1][k2]
    To create: dictdot(my)
    """
    def get(self, key, default=None):
        """ access data via dot notation """
        try:
            val = self
            if "." not in key:
                return self[key]
            for k in key.split('.'):
                if k.isdigit():
                    k = int(k)
                val = val[k]
            return val
        except (TypeError, KeyError, IndexError) as e:
            return default


def load_conf(yml_file, conf={}):
    """
    To load the config
    :param yml_file: the config file path
    :param conf: dict, to override global config
    :return: dict
    """
    with open(yml_file) as f:
        data = yaml.load(f)
        if conf:
            data.update(conf)
        return dictdot(data)


def extract_sitename(s):
    return re.sub(r"https?://(www\.)?", '', s).replace("www.", "")


def chunk_list(items, size):
    """
    Return a list of chunks
    :param items: List
    :param size: int The number of items per chunk
    :return: List
    """
    size = max(1, size)
    return [items[i:i + size] for i in range(0, len(items), size)]



#---


