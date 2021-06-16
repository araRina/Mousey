# -*- coding: utf-8 -*-
"""
Mousey: Discord Moderation Bot
Copyright (C) 2016 - 2021 Lilly Rose Berner

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from discord.ext import commands

from ... import NotFound


def tag_description(argument):
    if len(argument) <= 250:
        return argument

    raise commands.BadArgument('Description must be 250 or fewer characters.')


class Tag:
    def __init__(self, name, content, owner_id, tag_id):
        self.name = name
        self.content = content
        self.owner_id = owner_id
        self.id = tag_id

    @classmethod
    async def convert(cls, ctx, argument):
        try:
            resp = await ctx.bot.api.get_tags(ctx.guild.id, name=argument)
        except NotFound:
            raise commands.BadArgument(f'Tag "{argument}" not found.')

        found_tag = resp[0]

        return cls(found_tag['name'], found_tag['content'], found_tag['user_id'], found_tag['id'])


def tag_content(argument):
    if len(argument) > 1998:
        raise commands.BadArgument('Message must be 1998 or fewer characters.')

    return argument


def tag_name(argument):
    if len(argument) > 100:
        raise commands.BadArgument('Tag name must be 100 or fewer characters.')

    return argument
