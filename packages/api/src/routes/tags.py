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

import json

import asyncpg
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.routing import Router

from ..auth import is_authorized
from ..config import SHARD_COUNT
from ..permissions import has_permissions
from ..utils import build_search_query, build_update_query, ensure_user, generate_snowflake


router = Router()


@router.route('/guilds/{guild_id:int}/tags', methods=['POST'])
@is_authorized
@has_permissions(administrator=True)
async def post_guilds_guild_id_tags(request):
    data = await request.json()
    guild_id = request.path_params['guild_id']

    tag_id = generate_snowflake()

    try:
        user = data['user']

        name = data['name']
        content = data['content']
    except KeyError:
        raise HTTPException(400, 'Missing "user", "guild_id", "name", or "content" JSON field.')

    async with request.app.db.acquire() as conn:
        await ensure_user(conn, user)

        try:
            await conn.execute(
                'INSERT INTO tags (id, user_id, guild_id, name, content) VALUES ($1, $2, $3, $4, $5)',
                tag_id,
                user['id'],
                guild_id,
                name,
                content,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(400, 'Duplicate tag name provided.')

    return JSONResponse({'id': tag_id})


@router.route('/guilds/{guild_id:int}/tags', ['GET'])
@is_authorized
@has_permissions(administrator=True)
async def get_guilds_guild_id_tags(request):
    guild_id = request.path_params['guild_id']

    name = request.query_params.get('name')
    search_query = request.query_params.get('query')

    searches = ['guild_id = ']

    if name and search_query:
        raise HTTPException(400, '"name" and "query" query params are mutually exclusive.')

    if name is not None:
        name = name.lower()
        searches.append('LOWER(name) = ')

    if search_query is not None:
        search_query = f'%{search_query}%'.lower()
        searches.append('LOWER(name) LIKE ')

    query, idx = build_search_query(searches)
    args = tuple(filter(bool, (guild_id, name, search_query)))

    async with request.app.db.acquire() as conn:
        records = await conn.fetch(f'SELECT id, user_id, name, content FROM tags WHERE {query}', *args)

    if not records:
        raise HTTPException(404, 'None found.')

    return JSONResponse(list(map(dict, records)))


@router.route('/guilds/{guild_id:int}/tags/members/{member_id}', ['GET'])
@is_authorized
@has_permissions(administrator=True)
async def get_guilds_guild_id_members_member_id_tags(request):
    guild_id = request.path_params['guild_id']

    try:
        user_id = int(request.path_params['user_id'])
    except ValueError:
        raise HTTPException(400, 'Invalid "user_id" query param.')

    async with request.app.db.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT id, user_id, name, content
            FROM tags
            WHERE guild_id = $1 AND user_id = $2
            """,
            guild_id,
            user_id,
        )

    if not records:
        raise HTTPException(404, 'None found.')

    return JSONResponse(list(map(dict, records)))


@router.route('/guilds/{guild_id:int}/tags/{id:int}', methods=['PATCH'])
@is_authorized
@has_permissions(administrator=True)
async def patch_guilds_guild_id_tags_id(request):
    data = await request.json()

    tag_id = request.path_params['id']
    guild_id = request.path_params['guild_id']

    user = data.get('user')

    name = data.get('name')
    content = data.get('content')

    if user is None and name is None and content is None:
        raise HTTPException(400, 'Requires at least one of "user", "name" or "content" JSON field.')

    names = []
    updates = []

    if user is not None:
        names.append('user_id')
        updates.append(user['id'])

    if name is not None:
        names.append('name')
        updates.append(name)

    if content is not None:
        names.append('content')
        updates.append(content)

    query, idx = build_update_query(names)

    async with request.app.db.acquire() as conn:
        if user is not None:
            ensure_user(conn, user)

        record = await conn.fetchrow(
            f"""
            UPDATE tags
            SET {query}
            WHERE guild_id = ${idx} AND id = ${idx + 1}
            RETURNING id, guild_id, user_id, name, content
            """,
            *updates,
            guild_id,
            tag_id,
        )

    if record is not None:
        return JSONResponse(dict(record))

    raise HTTPException(404, 'Tag not found.')


@router.route('/guilds/{guild_id:int}/tags/{id:int}', methods=['DELETE'])
@is_authorized
@has_permissions(administrator=True)
async def delete_guilds_guild_id_tags_id(request):
    guild_id = request.path_params['guild_id']
    tag_id = request.path_params['id']

    async with request.app.db.acquire() as conn:
        status = await conn.execute('DELETE FROM tags WHERE guild_id = $1 AND id = $2', guild_id, tag_id)

    if int(status.split()[1]):
        return JSONResponse({})

    raise HTTPException(404, 'Tag not found.')
