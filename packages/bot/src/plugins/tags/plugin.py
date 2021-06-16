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

import discord
from discord.ext import commands

from ... import NotFound, Plugin, group
from ...utils import PaginatorInterface, close_interface_context, serialize_user
from .converter import Tag, tag_content, tag_name


def shorten_content(content):
    if len(content) > 30:
        content = f'{content[0:29]}...'
    return content


class Tags(Plugin):
    @group()
    async def tag(self, ctx, tag: Tag):
        await ctx.send(f':information_source: {tag.content}')

    @tag.command('create')
    async def tag_create(self, ctx, name: tag_name, *, content: tag_content):
        data = {'user': serialize_user(ctx.author), 'name': name, 'content': content}

        await self.mousey.api.create_tag(ctx.guild.id, data)

        await ctx.send('Tag successfully created!')

    @tag.command('list')
    async def tag_list(self, ctx, tag_owner: discord.User = None):
        try:
            if tag_owner is None:
                tags = await self.mousey.api.get_tags(ctx.guild.id)
            else:
                tags = await self.mousey.api.get_member_tags(ctx.guild.id, tag_owner.id)
        except NotFound:
            if tag_owner is None:
                await ctx.send('There are no tags in this server!')
            else:
                await ctx.send('This user has not made any tags!')
        else:
            paginator = commands.Paginator(
                max_size=1000, prefix=f"{tag_owner}'s tags\n" if tag_owner else 'Server tags', suffix=None
            )

            for tag in tags:

                paginator.add_line(f'**{tag["name"]}**:\n{shorten_content(tag["content"])}')

            interface = PaginatorInterface(self.mousey, paginator, owner=ctx.author, timeout=600)

            await interface.send_to(ctx.channel)
            close_interface_context(ctx, interface)

    @tag.command('delete')
    async def tag_delete(self, ctx, tag: Tag):
        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            await self.mousey.api.delete_tag(ctx.guild.id, tag.id)

            await ctx.send(f'Tag {tag.name} successfully deleted.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('rename')
    async def tag_rename(self, ctx, tag: Tag, new_name: tag_name):
        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'name': new_name}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully renamed to {new_name}.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('edit')
    async def tag_edit(self, ctx, tag: Tag, new_content: tag_content):
        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'content': new_content}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully edited to have new content: {shorten_content(new_content)}.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('transfer')
    async def tag_transfer(self, ctx, tag: Tag, new_owner: discord.Member):
        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'user': serialize_user(new_owner)}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully transferred to {new_owner}.')
        else:
            await ctx.send('You do not own this tag!')
