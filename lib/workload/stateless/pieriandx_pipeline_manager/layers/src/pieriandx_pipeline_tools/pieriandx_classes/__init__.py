#!/usr/bin/env python3

from copy import deepcopy
from typing import Dict

from pydantic import BaseModel


class BaseClass:
    _model = None

    def __init__(self, **kwargs):
        self._raw_kwargs_dict = deepcopy(kwargs)
        self.section_dict = {}
        kwargs_dict = deepcopy(kwargs)
        for key in self._model.model_fields.keys():
            if key in kwargs_dict.keys():
                setattr(self, key, kwargs.pop(key, None))

            if not hasattr(self, key) or getattr(self, key) is None:
                # Set default attribute
                setattr(self, key, self._model.model_fields[key].default)

        self.validate_model()

        self.coerce_values()

        self.build_section_dict()

    def validate_model(self):
        """
        Validate inputs against pydantic model of class
        :return:
        """
        pass #self._model.model_validate(self)

    def build_section_dict(self):
        # Collect original objects
        self.section_dict = self._model(**self.get_dict_object()).to_dict()
        self.section_dict = self.filter_dict(self.section_dict)

    def get_dict_object(self):
        def get_dict_object_recursively(dict_object):
            if isinstance(dict_object, BaseClass):
                return dict_object.get_dict_object()
            # if isinstance(dict_object, BaseModel):
            #     pass
            elif isinstance(dict_object, dict):
                return {
                    key: get_dict_object_recursively(value)
                    for key, value in dict_object.items()
                }
            elif isinstance(dict_object, list):
                return [
                    get_dict_object_recursively(value)
                    for value in dict_object
                ]
            else:
                return dict_object

        return {
            kv[0]: get_dict_object_recursively(kv[1])
            for kv in filter(
                lambda kv_iter: not kv_iter[0] in ["section_dict", "_raw_kwargs_dict"],
                self.__dict__.items()
            )
        }

    def filter_dict(self, initial_dict) -> Dict:
        """
        Filter out any values that are None
        :param initial_dict:
        :return:
        """
        return dict(
            filter(
                lambda kv: kv[1] is not None,
                initial_dict.items()
            )
        )

    def coerce_values(self):
        # Coerce with model dump
        coerced_dict = self._model(**self.get_dict_object()).model_dump()

        for key, value in coerced_dict.items():
            self.__setattr__(key, value)

    def to_dict(self) -> Dict:
        return self.section_dict
