from .service.service import RSSService
from .postgre import get_db_session, create_db_and_tables
import asyncio


async def test_main():
    await create_db_and_tables()
    async for db_session in get_db_session():
        service = RSSService(db_session)

        h2h_example_item = {
            "gameweek": 1,
            "league_id": 1,
            "matches": [
                {
                    "first_contender": "Ivan",
                    "second_contender": "Vitya",
                    "first_score": 62,
                    "second_score": 23,
                    "first_standings": {
                        "Saliba (ARS)": 6,
                        "Wood (NFO)": 4,
                        "Player3": 10,
                        "Player4": 8,
                        "Player5": 12,
                        "Player6": 7,
                        "Player7": 5,
                        "Player8": 10
                    },
                    "second_standings": {
                        "Ronaldo (MUN)": 2,
                        "Mbappe (PSG)": 5,
                        "Player3": 6,
                        "Player4": 3,
                        "Player5": 4,
                        "Player6": 1,
                        "Player7": 1,
                        "Player8": 1
                    }
                },
                {
                    "first_contender": "Petr",
                    "second_contender": "Stepan",
                    "first_score": 77,
                    "second_score": 23,
                    "first_standings": {
                        "PlayerA": 10,
                        "PlayerB": 12,
                        "PlayerC": 8,
                        "PlayerD": 15,
                        "PlayerE": 7,
                        "PlayerF": 5,
                        "PlayerG": 10,
                        "PlayerH": 10
                    },
                    "second_standings": {
                        "Player1": 4,
                        "Player2": 5,
                        "Player3": 3,
                        "Player4": 6,
                        "Player5": 5,
                        "Player6": 0,
                        "Player7": 0,
                        "Player8": 0
                    }
                }
            ],
            "standings": [
                ["Ivan", 3],
                ["Petr", 3],
                ["Vitya", 0],
                ["Stepan", 0]
            ]
        }

        classic_example_item = {
            "gameweek": 1,
            "league_id": 1,
            "contenders": [
                {
                    "name": "Ivan",
                    "score": 62,
                    "standings": {
                        "Saliba (ARS)": 6,
                        "Wood (NFO)": 4,
                        "Player3": 10,
                        "Player4": 8,
                        "Player5": 12,
                        "Player6": 7,
                        "Player7": 5,
                        "Player8": 10
                    }
                },
                {
                    "name": "Stepan",
                    "score": 23,
                    "standings": {
                        "Player1": 4,
                        "Player2": 5,
                        "Player3": 3,
                        "Player4": 6,
                        "Player5": 5,
                        "Player6": 0,
                        "Player7": 0,
                        "Player8": 0
                    }
                }
            ]
        }

        print(await service.create_classic_item(classic_example_item))
        await db_session.commit()


if __name__ == "__main__":
    from .logging_setup import setup_logging
    setup_logging()

    asyncio.run(test_main())
