# encoding: utf-8

import datetime
import logging
from typing import Any, List, Optional, Tuple
from ckan.common import config
from six import text_type
from sqlalchemy import Table, select, join, func, and_

import ckan.plugins as p
import ckan.model as model

log = logging.getLogger(__name__)
cache_enabled = p.toolkit.asbool(
    config.get('ckanext.stats.cache_enabled', False)
)

if cache_enabled:
    log.warn(
        'ckanext.stats does not support caching in current implementations'
    )

DATE_FORMAT = '%Y-%m-%d'


def table(name: str):
    return Table(name, model.meta.metadata, autoload=True)


def datetime2date(datetime_: datetime.datetime):
    return datetime.date(datetime_.year, datetime_.month, datetime_.day)


class Stats(object):

    @classmethod
    def largest_groups(
            cls, limit: int = 10) -> List[Tuple[Optional[model.Group], int]]:
        member = table('member')
        package = table('package')

        j = join(member, package, member.c.table_id == package.c.id)

        s = select(
            [member.c.group_id,
             func.count(member.c.table_id)]
        ).select_from(j).group_by(member.c.group_id).where(
            and_(
                member.c.group_id != None, member.c.table_name == 'package',
                package.c.private == False, package.c.state == 'active'
            )
        ).order_by(func.count(member.c.table_id).desc()).limit(limit)

        res_ids = model.Session.execute(s).fetchall()
        res_groups = [
            (model.Session.query(model.Group).get(text_type(group_id)), val)
            for group_id, val in res_ids
        ]
        return res_groups

    @classmethod
    def top_tags(cls, limit: int = 10,
                 returned_tag_info: str = 'object'
                 ) -> Optional[List[Any]]:  # by package
        assert returned_tag_info in ('name', 'id', 'object')
        tag = table('tag')
        package_tag = table('package_tag')
        package = table('package')
        if returned_tag_info == 'name':
            from_obj = [package_tag.join(tag)]
            tag_column = tag.c.name
        else:
            from_obj = None
            tag_column = package_tag.c.tag_id
        j = join(
            package_tag, package, package_tag.c.package_id == package.c.id
        )
        s = select([tag_column,
                    func.count(package_tag.c.package_id)],
                   from_obj=from_obj).select_from(j).where(
                       and_(
                           package_tag.c.state == 'active',
                           package.c.private == False,
                           package.c.state == 'active'
                       )
                   )
        s = s.group_by(tag_column).order_by(
            func.count(package_tag.c.package_id).desc()
        ).limit(limit)
        res_col = model.Session.execute(s).fetchall()
        if returned_tag_info in ('id', 'name'):
            return res_col
        elif returned_tag_info == 'object':
            res_tags = [
                (model.Session.query(model.Tag).get(text_type(tag_id)), val)
                for tag_id, val in res_col
            ]
            return res_tags

    @classmethod
    def top_package_creators(cls, limit: int = 10):
        userid_count = model.Session.query(
            model.Package.creator_user_id,
            func.count(model.Package.creator_user_id)
        ).filter(model.Package.state == 'active'
                 ).filter(model.Package.private == False).group_by(
                     model.Package.creator_user_id
                 ).order_by(func.count(model.Package.creator_user_id).desc()
                            ).limit(limit).all()
        user_count = [
            (model.Session.query(model.User).get(text_type(user_id)), count)
            for user_id, count in userid_count
            if user_id
        ]
        return user_count
