# -*- coding: utf-8 -*-
from typing import Any, Dict
from ckan.types import Schema
from ckan.common import CKANConfig
from datetime import datetime, timedelta

import ckan.model as model
import ckan.plugins as p
import ckan.lib.api_token as api_token


def default_token_lifetime() -> int:
    return p.toolkit.asint(
        p.toolkit.config.get(u"expire_api_token.default_lifetime", 3600))


class ExpireApiTokenPlugin(p.SingletonPlugin):
    p.implements(p.IApiToken, inherit=True)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        p.toolkit.add_template_directory(config_, u"templates")

    # ITemplateHelpers

    def get_helpers(self):
        return {
            u"expire_api_token_default_token_lifetime": default_token_lifetime
        }

    # IApiToken

    def create_api_token_schema(self, schema: Schema):
        schema[u"expires_in"] = [
            p.toolkit.get_validator(u"not_empty"),
            p.toolkit.get_validator(u"is_positive_integer"),
        ]
        schema[u"unit"] = [
            p.toolkit.get_validator(u"not_empty"),
            p.toolkit.get_validator(u"is_positive_integer"),
        ]
        return schema

    def postprocess_api_token(self, data: Dict[str, Any],
                              jti: str, data_dict: Dict[str, Any]):
        seconds = data_dict.get(u"expires_in", 0) * data_dict.get(u"unit", 0)
        if not seconds:
            seconds = default_token_lifetime()
        expire_at = datetime.utcnow() + timedelta(seconds=seconds)
        data[u"exp"] = api_token.into_seconds(
            expire_at
        )
        token = model.ApiToken.get(jti)
        assert token
        token.set_extra(
            u"expire_api_token", {u"exp": expire_at.isoformat()}, True
        )
        return data

    # TODO: subscribe to signal, sent from api_token.decode and remove
    # expired tokens
