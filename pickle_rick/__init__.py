import yaml
import os
import json
from typing import Union
from io import TextIOWrapper

class BasicRick:
    """
        A base class that creates internal structures from embedded structures.

        Args:
            base (str): String (YAML or JSON, file path to YAML/JSON file), text IO stream, dict.
            deep (bool): Internalize dictionary structures in lists.
            args (dict): Intended for extended classes to handle over-riden _internalize customisation.

        Raises:
            ValueError: If the given base object can not be handled.
    """
    def _iternalize(self, dictionary : dict, deep : bool, args : dict = None):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                self.__dict__.update({k:BasicRick(v, deep)})
                continue
            if isinstance(v, list) and deep:
                new_list = list()
                for i in v:
                    if isinstance(i, dict):
                        new_list.append(BasicRick(i, deep))
                    else:
                        new_list.append(i)
                self.__dict__.update({k: new_list})
                continue

            self.__dict__.update({k:v})

    def __init__(self, base : Union[dict,str,TextIOWrapper], deep : bool = False, args : dict = None):
        if isinstance(base, dict):
            self._iternalize(base, deep, args)
            return

        if isinstance(base, TextIOWrapper):
            try:
                config_data = yaml.load(base, Loader=yaml.SafeLoader)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))
            try:
                config_data = json.load(base)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))

        if os.path.isfile(base):
            try:
                config_data = yaml.load(open(base, 'r'), Loader=yaml.SafeLoader)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))
            try:
                config_data = json.load(open(base, 'r'),)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))
        if isinstance(base, str):
            try:
                config_data = yaml.safe_load(base)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))
            try:
                config_data = json.loads(base)
                self._iternalize(config_data, deep, args)
                return
            except Exception as exc:
                print("Tried: {}".format(exc))

        raise ValueError('Base object could not be internalized, type {} not handled'.format(type(base)))

    def __repr__(self):
        keys = self.__dict__
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __setitem__(self, key, item):
        self.__dict__.update( {key : item} )

    def __getitem__(self, key):
        return self.__dict__[key]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        self.__n = 0
        return self

    def __next__(self):
        if self.__n < len(self.__dict__):
            name = list(self.__dict__.keys())[self.__n]
            if str(name).__contains__(self.__class__.__name__) or str(name).endswith('__n'):
                self.__n += 1
            if self.__n < len(self.__dict__):
                obj = self.__dict__[list(self.__dict__.keys())[self.__n]]
                self.__n += 1
                return obj
            else:
                raise StopIteration
        else:
            raise StopIteration

    def _recursive_search(self, dictionary, key):
        if key in dictionary:
            return dictionary[key]
        for k, v in dictionary.items():
            if isinstance(v, BasicRick):
                value = self._recursive_search(v.__dict__, key)
                if value:
                    return value
            if isinstance(v, dict):
                value = self._recursive_search(v, key)
                if value:
                    return value

    def items(self):
        """
        Iterate through all key value pairs.

        Yields:
            tuple: str, object.
        """
        for key in self.__dict__.keys():
            yield key, self.__dict__[key]

    def get(self, key : str, default=None):
        """
        Employs a recursive search of structure and returns the first found key-value pair.
        Searches with normal, upper, and lower case.

        Args:
            key (str): key string being searched.
            default (any): Return value if nothing is found.

        Returns:
            obj: value found, or None for nothing found.
        """
        value = self._recursive_search(self.__dict__, key)
        if not value:
            value = self._recursive_search(self.__dict__, key.lower())
            if not value:
                value = self._recursive_search(self.__dict__, key.upper())
        if not value:
            return default
        return value

    def values(self):
        """
        Gets the higher level values of the current Rick object.

        Returns:
            list: of objects.
        """
        keys = list(self.__dict__.keys())
        objects = [self.__dict__[k] for k in keys if not str(k).__contains__(self.__class__.__name__) and not str(k).endswith('__n')]

        return objects

    def keys(self):
        """
        Gets the higher level keys of the current Rick object.

        Returns:
            list: of keys.
        """
        keys = list(self.__dict__.keys())
        keys = [k for k in keys if not str(k).__contains__(self.__class__.__name__) and not str(k).endswith('__n')]

        return keys

    def dict(self):
        """
        Deconstructs the whole object into a Python dictionary.

        Returns:
            dict: of object.
        """
        d = dict()
        for key, value in self.__dict__.items():
            if isinstance(value, BasicRick):
                d[key] = value.dict()
            else:
                d[key] = value
        return d

    def has(self, key : str, deep=False) -> bool:
        """
        Checks whether the key exists in the object.

        Args:
            key (str): key string being searched.
            deep (bool): whether to search deeply.

        Returns:
            bool: if found.
        """
        if key in self.__dict__:
            return True
        if deep:
            value = self._recursive_search(self.__dict__, key)
            if value:
                return True
        return False

    def to_yaml_file(self, file_path : str):
        """
        Does a self dump to a YAML file.

        Args:
            file_path (str): File path.
        """
        self_as_dict = self.dict()
        with open(file_path, 'w', encoding='utf-8') as fs:
            yaml.safe_dump(self_as_dict, fs)

    def to_yaml_string(self):
        """
        Dumps self to YAML string.

        Returns:
            str: YAML representation.
        """
        self_as_dict = self.dict()
        return yaml.safe_dump(self_as_dict, None)

    def to_json_file(self, file_path: str):
        """
        Does a self dump to a JSON file.

        Args:
            file_path (str): File path.
        """
        self_as_dict = self.dict()
        with open(file_path, 'w', encoding='utf-8') as fs:
            json.dump(self_as_dict, fs)

    def to_json_string(self):
        """
        Dumps self to YAML string.

        Returns:
            str: JSON representation.
        """
        self_as_dict = self.dict()
        return json.dumps(self_as_dict)

class ExtendedPickleRick(BasicRick):
    """
        An extended version of the BasePickleRick that can load OS environ variables and Python Lambda functions.

        Args:
            base (str): String (YAML or JSON, file path to YAML/JSON file), text IO stream, dict.
            deep (bool): Internalize dictionary structures in lists.
            load_lambda (bool): Load lambda as code or strings.
    """

    def _iternalize(self, dictionary : dict, deep : bool, args : dict = None):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                if 'type' in v.keys() and v['type'] == 'env':
                    if 'default' in v.keys():
                        self.__dict__.update({k: os.getenv(v['load'], v['default'])})
                    else:
                        self.__dict__.update({k: os.getenv(v['load'])})
                    continue
                if 'type' in v.keys() and v['type'] == 'lambda':
                    if args and args['load_lambda']:
                        self.__dict__.update({k: eval(v['load'])})
                    else:
                        self.__dict__.update({k: v['load']})
                    continue
                self.__dict__.update({k:ExtendedPickleRick(v, deep, args['load_lambda'])})
                continue
            if isinstance(v, list) and deep:
                new_list = list()
                for i in v:
                    if isinstance(i, dict):
                        new_list.append(ExtendedPickleRick(i, deep, args['load_lambda']))
                    else:
                        new_list.append(i)
                self.__dict__.update({k: new_list})
                continue
            self.__dict__.update({k: v})

    def __init__(self, base: Union[dict, str] , deep : bool = False, load_lambda : bool = False):
        super().__init__(base, deep, {'load_lambda' : load_lambda})
