#!/usr/bin/env python3
"""
Listens in twitch.tv/earthsensesandbox and responds to !commands.

Route commands (!route1/2/3) dispatch the robot by calling the EarthSense
EBS (see ../ebs/), which owns the actual TSP call, the busy-lock, and the
per-user cooldown — this bot no longer talks to the robot directly.
"""

import os

import httpx
from twitchio.ext import commands

BOT_NAME = "EarthSenseBot"
VERSION = "testing"

EBS_BASE_URL = os.environ.get("EBS_BASE_URL", "http://localhost:8000")
EBS_BOT_SHARED_SECRET = os.environ["EBS_BOT_SHARED_SECRET"]

# Maps chat command name -> route id used by the EBS / overlay/js/routes.js.
ROUTE_COMMAND_MAP = {
    "route1": "route-1",
    "route2": "route-2",
    "route3": "route-3",
}


class RobotBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ["TMI_TOKEN"],
            prefix="!",
            initial_channels=[os.environ["CHANNEL"]],
        )
        self._http = httpx.AsyncClient(base_url=EBS_BASE_URL, timeout=10.0)

    async def event_ready(self):
        print(f"{BOT_NAME} v{VERSION} connected as {self.nick}")

    async def close(self):
        await self._http.aclose()
        await super().close()

    @commands.command(name="help")
    async def help(self, ctx: commands.Context):
        await ctx.send(
            "Commands: !help, !about, !route1, !route2, !route3"
        )

    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        await ctx.send(f"{BOT_NAME} v{VERSION} — a simple bot for controlling robots.")

    async def _dispatch_route(self, ctx: commands.Context, command_name: str):
        route_id = ROUTE_COMMAND_MAP[command_name]
        try:
            resp = await self._http.post(
                f"/internal/routes/{route_id}/execute",
                json={"user_id": str(ctx.author.id), "user_name": ctx.author.name},
                headers={"X-EBS-Secret": EBS_BOT_SHARED_SECRET},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", e.response.text)
            await ctx.send(f"@{ctx.author.name} couldn't dispatch {route_id}: {detail}")
            return
        except httpx.HTTPError as e:
            await ctx.send(f"@{ctx.author.name} couldn't reach the robot backend: {e}")
            return

        await ctx.send(f"@{ctx.author.name} dispatched the robot on {data['name']}.")

    @commands.command(name="route1")
    async def route1(self, ctx: commands.Context):
        await self._dispatch_route(ctx, "route1")

    @commands.command(name="route2")
    async def route2(self, ctx: commands.Context):
        await self._dispatch_route(ctx, "route2")

    @commands.command(name="route3")
    async def route3(self, ctx: commands.Context):
        await self._dispatch_route(ctx, "route3")


if __name__ == "__main__":
    RobotBot().run()
