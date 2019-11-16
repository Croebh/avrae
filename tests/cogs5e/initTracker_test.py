import discord
import pytest

from tests.conftest import end_init, start_init
from tests.utils import D20_PATTERN, active_character, active_combat

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("init_fixture")
class TestInitiativeSimple:
    async def test_init_begin(self, avrae, dhttp):
        dhttp.clear()
        avrae.message("!init begin")
        await dhttp.receive_delete()
        await dhttp.receive_message("```Awaiting combatants...```")
        await dhttp.receive_edit("```markdown\nCurrent initiative: 0 (round 0)\n===============================\n```",
                                 regex=False)
        await dhttp.receive_pin()
        await dhttp.receive_message("Everyone roll for initiative!\nIf you have a character set up with SheetManager: "
                                    "`!init join`\nIf it's a 5e monster: `!init madd <monster name>`\nOtherwise: "
                                    "`!init add <modifier> <name>`", regex=False)

    async def test_init_end(self, avrae, dhttp):
        dhttp.clear()
        avrae.message("!init end")
        await dhttp.receive_delete()
        await dhttp.receive_message("Are you sure you want to end combat? (Reply with yes/no)", regex=False)
        avrae.message("y")
        await dhttp.receive_delete()
        await dhttp.receive_delete()
        await dhttp.receive_message("OK, ending...")
        await dhttp.receive_message(r"End of combat report: \d+ rounds "
                                    r"```markdown\nCurrent initiative: \d+ \(round \d+\)\n"
                                    r"===============================\n```.*", dm=True)
        await dhttp.receive_edit(r"[\s\S]*```-----COMBAT ENDED-----```")
        await dhttp.receive_unpin()
        await dhttp.receive_edit("Combat ended.")


@pytest.mark.usefixtures("init_fixture", "character")
class TestInitiativeWithCharacters:
    async def test_init_begin(self, avrae, dhttp):
        await start_init(avrae, dhttp)

    async def test_init_join(self, avrae, dhttp):
        dhttp.clear()
        avrae.message("!init join")
        await dhttp.receive_delete()
        await dhttp.receive_edit()
        join_embed = discord.Embed(
            title=rf".+ makes an Initiative check!",
            description=D20_PATTERN
        )
        join_embed.set_footer(text="Added to combat!")
        await dhttp.receive_message(embed=join_embed)

    async def test_init_end(self, avrae, dhttp):
        await end_init(avrae, dhttp)


@pytest.mark.usefixtures("init_fixture", "character")
class TestYourStandardInitiative:
    async def test_standard_init_setup(self, avrae, dhttp):
        await start_init(avrae, dhttp)
        avrae.message("!init join -p 50")
        await dhttp.drain()
        avrae.message("!init madd kobold -n 5")
        await dhttp.drain()
        avrae.message("!init add 0 TEST1")
        await dhttp.drain()
        avrae.message("!init add 0 TEST2")
        await dhttp.drain()
        avrae.message("!init next")
        await dhttp.drain()

    async def test_attacking(self, avrae, dhttp):
        character = await active_character(avrae)
        for combatant in (character.name, "KO1", "TEST1", "TEST2"):
            avrae.message(f"!i a \"{character.attacks[0].name}\" -t \"{combatant}\" hit")
            await dhttp.drain()
            c = (await active_combat(avrae)).get_combatant(combatant)
            if c.hp is not None:
                assert c.hp < c.max_hp

    async def test_hp_modifications(self, avrae, dhttp):
        character = await active_character(avrae)
        for combatant in (character.name, "KO1", "TEST1", "TEST2"):
            avrae.message(f"!i hp \"{combatant}\" max 100")
            await dhttp.drain()
            assert (await active_combat(avrae)).get_combatant(combatant).max_hp == 100

            avrae.message(f"!i hp \"{combatant}\" set 100")
            await dhttp.drain()
            assert (await active_combat(avrae)).get_combatant(combatant).hp == 100

            avrae.message(f"!i a \"{character.attacks[0].name}\" -t \"{combatant}\" hit")
            await dhttp.drain()
            assert (await active_combat(avrae)).get_combatant(combatant).hp < 100

    async def test_standard_init_teardown(self, avrae, dhttp):
        await end_init(avrae, dhttp)
