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
from ..utils import ensure_user, generate_snowflake


router = Router()


@router.route('/guilds/{id:int}/tags', methods=['POST'])
@is_authorized
@has_permissions(administrator=True)
async def post_guilds_id_tags(request):
    data = await request.json()
    guild_id = request.path_params['id']

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
