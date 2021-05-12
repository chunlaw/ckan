# encoding: utf-8

import os
from typing import Any, Dict

from ckan import plugins
from ckan.lib.uploader import ResourceUpload as DefaultResourceUpload


class ExampleIUploader(plugins.SingletonPlugin):
    plugins.implements(plugins.IUploader, inherit=True)

    def get_resource_uploader(self, data_dict: Dict[str, Any]):
        return ResourceUpload(data_dict)


class ResourceUpload(DefaultResourceUpload):
    path_prefix = 'filename_prefix_'

    def get_path(self, id: str):
        directory = self.get_directory(id)
        filepath = os.path.join(
            directory, '{}_{}'.format(self.path_prefix, id[6:]))
        return filepath
