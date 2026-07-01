#!/usr/bin/env python3
"""
Listens in twitch.tv/earthsensesandbox and responds to !commands.
Proof of concept for now
"""

import os

from twitchio.ext import commands

BOT_NAME = "EarthSenseBot"
VERSION = "testing"


class RobotBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ["TMI_TOKEN"],
            prefix="!",
            initial_channels=[os.environ["CHANNEL"]],
        )

    async def event_ready(self):
        print(f"{BOT_NAME} v{VERSION} connected as {self.nick}")

    @commands.command(name="help")
    async def help(self, ctx: commands.Context):
        await ctx.send(
            "Commands: !help, !about, !route1, !route2, !route3"
        )

    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        await ctx.send(f"{BOT_NAME} v{VERSION} — a simple bot for controlling robots.")

    @commands.command(name="route1")
    async def route1(self, ctx: commands.Context):
        await ctx.send(f"[TEST] @{ctx.author.name} dispatched the robot on Route 1.")

    @commands.command(name="route2")
    async def route2(self, ctx: commands.Context):
        await ctx.send(f"[TEST] @{ctx.author.name} dispatched the robot on Route 2.")

    @commands.command(name="route3")
    async def route3(self, ctx: commands.Context):
        await ctx.send(f"[TEST] @{ctx.author.name} dispatched the robot on Route 3.")


if __name__ == "__main__":
    RobotBot().run()
