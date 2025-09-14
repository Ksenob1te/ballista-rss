from aiormq.tools import awaitable

from .service.service import RSSService
from .postgre import get_db_session, create_db_and_tables
import asyncio


async def test_main():
    await create_db_and_tables()
    async for db_session in get_db_session():
        service = RSSService(db_session)

        # h2h_example_item = {
        #     "gameweek": 1,
        #     "league_id": 1,
        #     "matches": [
        #         {
        #             "first_contender": "Ivan",
        #             "second_contender": "Vitya",
        #             "first_score": 62,
        #             "second_score": 23,
        #             "first_composition": {
        #                 {"name": "Saliba", "team": "ARS", "points": 6},
        #                 {"name": "Wood", "team": "NFO", "points": 4},
        #                 {"name": "Player3", "team": "TEAM3", "points": 10},
        #                 {"name": "Player4", "team": "TEAM4", "points": 8},
        #                 {"name": "Player5", "team": "TEAM5", "points": 12},
        #                 {"name": "Player6", "team": "TEAM6", "points": 7},
        #                 {"name": "Player7", "team": "TEAM7", "points": 5},
        #                 {"name": "Player8", "team": "TEAM8", "points": 10}
        #             },
        #             "second_composition": {
        #                 {"name": "Player1", "team": "TEAM1", "points": 4},
        #                 {"name": "Player2", "team": "TEAM2", "points": 5},
        #                 {"name": "Player3", "team": "TEAM3", "points": 3},
        #                 {"name": "Player4", "team": "TEAM4", "points": 6},
        #                 {"name": "Player5", "team": "TEAM5", "points": 5},
        #                 {"name": "Player6", "team": "TEAM6", "points": 0},
        #                 {"name": "Player7", "team": "TEAM7", "points": 0},
        #                 {"name": "Player8", "team": "TEAM8", "points": 0}
        #             }
        #         },
        #         {
        #             "first_contender": "Petr",
        #             "second_contender": "Stepan",
        #             "first_score": 77,
        #             "second_score": 23,
        #             "first_composition": {
        #                 {"name": "Saliba", "team": "ARS", "points": 6},
        #                 {"name": "Wood", "team": "NFO", "points": 4},
        #                 {"name": "Player3", "team": "TEAM3", "points": 10},
        #                 {"name": "Player4", "team": "TEAM4", "points": 8},
        #                 {"name": "Player5", "team": "TEAM5", "points": 12},
        #                 {"name": "Player6", "team": "TEAM6", "points": 7},
        #                 {"name": "Player7", "team": "TEAM7", "points": 5},
        #                 {"name": "Player8", "team": "TEAM8", "points": 10}
        #             },
        #             "second_composition": {
        #                 {"name": "Player1", "team": "TEAM1", "points": 4},
        #                 {"name": "Player2", "team": "TEAM2", "points": 5},
        #                 {"name": "Player3", "team": "TEAM3", "points": 3},
        #                 {"name": "Player4", "team": "TEAM4", "points": 6},
        #                 {"name": "Player5", "team": "TEAM5", "points": 5},
        #                 {"name": "Player6", "team": "TEAM6", "points": 0},
        #                 {"name": "Player7", "team": "TEAM7", "points": 0},
        #                 {"name": "Player8", "team": "TEAM8", "points": 0}
        #             }
        #         }
        #     ],
        #     "standings": [
        #         ["Ivan", 3],
        #         ["Petr", 3],
        #         ["Vitya", 0],
        #         ["Stepan", 0]
        #     ]
        # }
        h2h_example_item = {
            "gameweek": 1,
            "league_id": 1,
            "contenders": [
                {
                    "name": "Team I",
                    "leader": "Ivan",
                    "team_id": 1,
                    "score": 3,
                    "composition": [
                        {"name": "Saliba", "team": "ARS", "points": 6, "player_id": 1, "factor": 2},
                        {"name": "Wood", "team": "NFO", "points": 4, "player_id": 2, "factor": 2},
                        {"name": "Player3", "team": "TEAM3", "points": 10, "player_id": 3, "factor": 2},
                        {"name": "Player4", "team": "TEAM4", "points": 8, "player_id": 4, "factor": 2},
                        {"name": "Player5", "team": "TEAM5", "points": 12, "player_id": 5, "factor": 2},
                        {"name": "Player6", "team": "TEAM6", "points": 7, "player_id": 6, "factor": 2},
                        {"name": "Player7", "team": "TEAM7", "points": 5, "player_id": 7, "factor": 2},
                        {"name": "Player8", "team": "TEAM8", "points": 10, "player_id": 8, "factor": 2},
                    ]
                },
                {
                    "name": "Team S",
                    "leader": "Stephan",
                    "team_id": 2,
                    "score": 0,
                    "composition": [
                        {"name": "Player1", "team": "TEAM1", "points": 4, "player_id": 9, "factor": 1},
                        {"name": "Player2", "team": "TEAM2", "points": 5, "player_id": 10, "factor": 1},
                        {"name": "Player3", "team": "TEAM3", "points": 3, "player_id": 11, "factor": 1},
                        {"name": "Player4", "team": "TEAM4", "points": 6, "player_id": 12, "factor": 1},
                        {"name": "Player5", "team": "TEAM5", "points": 5, "player_id": 13, "factor": 1},
                        {"name": "Player6", "team": "TEAM6", "points": 0, "player_id": 14, "factor": 1},
                        {"name": "Player7", "team": "TEAM7", "points": 0, "player_id": 15, "factor": 1},
                        {"name": "Player8", "team": "TEAM8", "points": 0, "player_id": 16, "factor": 1},
                    ]
                },
                {
                    "name": "Team P",
                    "leader": "Petr",
                    "team_id": 3,
                    "score": 3,
                    "composition": [
                        {"name": "Saliba", "team": "ARS", "points": 6, "player_id": 17, "factor": 2},
                        {"name": "Wood", "team": "NFO", "points": 4, "player_id": 18, "factor": 2},
                        {"name": "Player3", "team": "TEAM3", "points": 3, "player_id": 27, "factor": 2},
                        {"name": "Player4", "team": "TEAM4", "points": 8, "player_id": 20, "factor": 2},
                        {"name": "Player5", "team": "TEAM5", "points": 12, "player_id": 21, "factor": 2},
                        {"name": "Player6", "team": "TEAM6", "points": 7, "player_id": 22, "factor": 2},
                        {"name": "Player7", "team": "TEAM7", "points": 5, "player_id": 23, "factor": 2},
                        {"name": "Player8", "team": "TEAM8", "points": 10, "player_id": 24, "factor": 2},
                    ]
                },
                {
                    "name": "Team V",
                    "leader": "Vitya",
                    "team_id": 4,
                    "score": 0,
                    "composition": [
                        {"name": "Player1", "team": "TEAM1", "points": 4, "player_id": 25, "factor": 2},
                        {"name": "Player2", "team": "TEAM2", "points": 5, "player_id": 26, "factor": 2},
                        {"name": "Player3", "team": "TEAM3", "points": 3, "player_id": 27, "factor": 2},
                        {"name": "Player4", "team": "TEAM4", "points": 6, "player_id": 28, "factor": 2},
                        {"name": "Player5", "team": "TEAM5", "points": 5, "player_id": 29, "factor": 2},
                        {"name": "Player6", "team": "TEAM6", "points": 0, "player_id": 30, "factor": 2},
                        {"name": "Player7", "team": "TEAM7", "points": 0, "player_id": 31, "factor": 2},
                        {"name": "Player8", "team": "TEAM8", "points": 0, "player_id": 32, "factor": 2},
                    ]
                }
            ],
            "matches": [
                {
                    "first_contender_id": 1,
                    "second_contender_id": 4,
                },
                {
                    "first_contender_id": 3,
                    "second_contender_id": 2,
                }
            ]
        }

        classic_example_item = {
            "gameweek": 1,
            "league_id": 1,
            "contenders": [
                {
                    "name": "Team 1",
                    "leader": "Leader 1",
                    "team_id": 1,
                    "score": 1,
                    "composition": [
                        {"name": "Player1", "team": "TEAM1", "points": 6, "player_id": 1, "factor": 1},
                        {"name": "Player2", "team": "TEAM2", "points": 4, "player_id": 2, "factor": 1},
                        {"name": "Player3", "team": "TEAM3", "points": 10, "player_id": 3, "factor": 1},
                        {"name": "Player4", "team": "TEAM4", "points": 8, "player_id": 4, "factor": 1},
                        {"name": "Player5", "team": "TEAM5", "points": 12, "player_id": 5, "factor": 1},
                        {"name": "Player6", "team": "TEAM6", "points": 7, "player_id": 6, "factor": 1},
                        {"name": "Player7", "team": "TEAM7", "points": 5, "player_id": 7, "factor": 1},
                        {"name": "Player8", "team": "TEAM8", "points": 10, "player_id": 8, "factor": 2}
                    ]
                },
                {
                    "name": "Team 2",
                    "leader": "Leader 2",
                    "team_id": 2,
                    "score": 2,
                    "composition": [
                        {"name": "Player9", "team": "TEAM1", "points": 4, "player_id": 9, "factor": 1},
                        {"name": "Player10", "team": "TEAM2", "points": 5, "player_id": 10, "factor": 1},
                        {"name": "Player11", "team": "TEAM3", "points": 3, "player_id": 11, "factor": 1},
                        {"name": "Player12", "team": "TEAM4", "points": 6, "player_id": 12, "factor": 1},
                        {"name": "Player13", "team": "TEAM5", "points": 5, "player_id": 13, "factor": 1},
                        {"name": "Player14", "team": "TEAM6", "points": 0, "player_id": 14, "factor": 1},
                        {"name": "Player15", "team": "TEAM7", "points": 0, "player_id": 15, "factor": 1},
                        {"name": "Player16", "team": "TEAM8", "points": 0, "player_id": 16, "factor": 2}
                    ]
                }
            ]
        }

        # print(await service.create_h2h_item(h2h_example_item))
        print(await service.send_webhook(645829, "classic"))
        await db_session.commit()


if __name__ == "__main__":
    from .logging_setup import setup_logging
    import logging
    setup_logging(logging.DEBUG)

    asyncio.run(test_main())
