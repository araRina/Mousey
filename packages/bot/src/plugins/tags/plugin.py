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
    @group(usage='<tag name>')
    async def tag(self, ctx, tag: Tag):
        """
        View an existing tag on a server.

        Example: `{prefix}tag "rule 1"`
        \u200b
        """

        await ctx.send(f'\N{INFORMATION SOURCE} {tag.content}')

    @tag.command('create')
    async def tag_create(self, ctx, name: tag_name, *, content: tag_content):
        """
        Make a new tag with the specified description.

        Name can be any string up to 100 characters in length.
          Note: The name must not be taken by any other tags on the server.
        Content can be any string up to 1998 characters in length.

        Example: `{prefix}tag create "rule 1" Be nice to others.`
        \u200b
        """

        data = {'user': serialize_user(ctx.author), 'name': name, 'content': content}
        await self.mousey.api.create_tag(ctx.guild.id, data)

        await ctx.send('Tag successfully created!')

    @tag.command('list')
    async def tag_list(self, ctx, user: discord.User = None):
        """
        View all tags in the current server.
        You may provide a user to see all tags from them.

        User can be specified as a mention, ID, DiscordTag, or name.

        Example: `{prefix}tag list`
        Example: `{prefix}tag list @Rina#5251`
        \u200b
        """

        try:
            if user is None:
                tags = await self.mousey.api.get_tags(ctx.guild.id)
            else:
                tags = await self.mousey.api.get_member_tags(ctx.guild.id, user.id)
        except NotFound:
            if user is None:
                await ctx.send('There are no tags in this server!')
            else:
                await ctx.send('This user has not made any tags!')
        else:
            paginator = commands.Paginator(
                max_size=1000, prefix=f"{user}'s tags\n" if user else 'Server tags', suffix=None
            )

            for tag in tags:
                paginator.add_line(f'**{tag["name"]}**:\n{shorten_content(tag["content"])}')

            interface = PaginatorInterface(self.mousey, paginator, owner=ctx.author, timeout=600)

            await interface.send_to(ctx.channel)
            close_interface_context(ctx, interface)

    @tag.command('delete')
    async def tag_delete(self, ctx, tag: Tag):
        """
        Delete one of your own tags.
        If you have the manage messages permission, you can delete others' tags.

        Tag must be specified by its name.

        `Example: {prefix}tag delete "rule 1"`
        \u200b
        """

        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            await self.mousey.api.delete_tag(ctx.guild.id, tag.id)

            await ctx.send(f'Tag {tag.name} successfully deleted.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('rename', usage='<tag> <new name>')
    async def tag_rename(self, ctx, tag: Tag, new_name: tag_name):
        """
        Rename one of your own tags.
        If you have the manage messages permission, you can rename others' tags.

        Tag must be specified by its name.
        New name can be any string up to 100 characters long.
          Note: The name must not be taken by any other tags on the server.

        `Example: {prefix}tag rename SnowyLuma LostLuma`
        \u200b
        """

        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'name': new_name}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully renamed to {new_name}.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('edit')
    async def tag_edit(self, ctx, tag: Tag, *, content: tag_content):
        """
        Edit the content of one of your own tags
        If you have the manage messages permission, you can also edit others' tags.

        Tag must be specified by its name.
        Content can be any string up to 1998 characters long.

        `Example: {prefix}tag edit "Planned events" No events are planned currently.`
        \u200b
        """

        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'content': content}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully edited to have new content: {shorten_content(content)}.')
        else:
            await ctx.send('You do not own this tag!')

    @tag.command('transfer')
    async def tag_transfer(self, ctx, tag: Tag, user: discord.Member):
        """
        Transfer a tag you own to someone else.
        If you have the manage messages permission, you can transfer others' tags.

        Tag must be specified by its name.
        User must be specified as a mention, ID, DiscordTag, or name.

        `Example: {prefix}tag transfer "rule 1" Rina#5251`
        \u200b
        """

        if tag.owner_id == ctx.author.id or ctx.author.guild_permissions.manage_messages:
            data = {'user': serialize_user(user)}
            await self.mousey.api.update_tag(ctx.guild.id, tag.id, data)

            await ctx.send(f'Tag {tag.name} successfully transferred to {user}.')
        else:
            await ctx.send('You do not own this tag!')
