import asyncio
from typing import Coroutine

from starlette.testclient import TestClient, WebSocketTestSession

from codejam.server import app
from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import ErrorOperations, GameOperations, TopicEnum
from codejam.server.models.phrase_generator import PhraseDifficulty


class TestUser:
    """Represents a player."""

    def __init__(self, username: str, websocket: WebSocketTestSession):
        self.username = username
        self.websocket = websocket


def test_winning_game(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    mocker,
    game_creation_message: Message,
    game_join_message: Message,
    game_start_message: Message,
    chat_message: Message
):
    async def dumy_delay_wrapper(delay: int, coro: Coroutine):
        return

    mocker.patch(
        "codejam.server.controllers.game_controller.delay_wrapper",
        dumy_delay_wrapper
    )
    mocker.patch(
        "codejam.server.controllers.chat_controller.ChatController.wait_till_next_turn",
        mocker.AsyncMock()
    )
    mocker.patch(
        "codejam.server.models.game.Game.generate_phrase",
        mocker.MagicMock(return_value="Dummy Phrase of level EASY")
    )

    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        user = TestUser(test_client, websocket=websocket)
        user.websocket.send_json(game_creation_message.dict())
        game_created = Message(**user.websocket.receive_json())
        game_id = game_created.value.game_id
        test_data.game_id = game_id

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            user2 = TestUser(second_test_client, websocket=websocket2)
            game_join_message.game_id = game_id
            user2.websocket.send_json(game_join_message.dict())

            game_joined = Message(**user2.websocket.receive_json())
            assert game_joined.topic.operation == GameOperations.JOIN.value

            game_joined = Message(**user.websocket.receive_json())
            assert game_joined.topic.operation == GameOperations.JOIN.value

            game_start_message.game_id = game_id
            user.websocket.send_json(game_start_message.dict())

            not_enough_players = Message(**user.websocket.receive_json())
            assert not_enough_players.topic.type == TopicEnum.ERROR.value

            not_enough_players = Message(**user2.websocket.receive_json())
            assert not_enough_players.topic.type == TopicEnum.ERROR.value

            with client.websocket_connect(f"/ws/third_client") as websocket3:
                game_join_message.game_id = game_id
                game_join_message.username = "third_client"
                user3 = TestUser("third_client", websocket=websocket3)
                user3.websocket.send_json(game_join_message.dict())

                game_joined = Message(**user3.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_joined = Message(**user2.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_joined = Message(**user.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_start_message.game_id = game_id
                user.websocket.send_json(game_start_message.dict())

                expected_phrase = "Dummy Phrase of level EASY"
                hashed_phrase = "**********"

                def test_turn(user: TestUser, turn: int):
                    game_joined = Message(**user.websocket.receive_json())
                    assert game_joined.topic.operation == GameOperations.TURN.value
                    assert (
                        game_joined.value.turn.phrase == expected_phrase
                        if game_joined.value.turn.drawer == user.username
                        else hashed_phrase
                    )
                    assert game_joined.value.turn.turn_no == turn
                    return game_joined.value.turn.drawer

                drawer = test_turn(user=user, turn=1)
                test_turn(user=user2, turn=1)
                test_turn(user=user3, turn=1)

                sender = None
                for u in [user, user2, user3]:
                    if u.username != drawer:
                        chat_message.username = u.username
                        chat_message.value.sender = u.username
                        chat_message.value.message = expected_phrase
                        chat_message.game_id = game_id
                        sender = u.username
                        u.websocket.send_json(chat_message.dict())
                        break

                def test_win(user: TestUser, winner: str):
                    game_won = Message(**user.websocket.receive_json())
                    assert game_won.topic.operation == GameOperations.WIN.value
                    assert (
                        game_won.value.turn.phrase == expected_phrase
                        if game_won.value.turn.drawer == user.username
                        else hashed_phrase
                    )
                    winner_score = max([val for val in game_won.value.turn.score.values()])
                    for key, value in game_won.value.turn.score.items():
                        if key == winner:
                            assert value == winner_score
                        else:
                            assert value == 0

                test_win(user=user, winner=sender)
                test_win(user=user2, winner=sender)
                test_win(user=user3, winner=sender)

                test_turn(user=user, turn=2)
                test_turn(user=user2, turn=2)
                test_turn(user=user3, turn=2)


def test_running_game(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    mocker,
    game_creation_message: Message,
    game_join_message: Message,
    game_start_message: Message,
):
    async def dumy_delay_wrapper(delay: int, coro: Coroutine):
        await asyncio.sleep(0)
        await coro

    mocker.patch(
        "codejam.server.controllers.game_controller.delay_wrapper",
        dumy_delay_wrapper
    )
    mocker.patch(
        "codejam.server.controllers.chat_controller.ChatController.wait_till_next_turn",
        mocker.AsyncMock()
    )
    mocker.patch(
        "codejam.server.models.game.Game.generate_phrase",
        mocker.MagicMock(return_value="Dummy Phrase of level EASY")
    )

    mocker.patch(
        "codejam.server.models.game.Game.get_number_of_turns",
        mocker.MagicMock(return_value=3)
    )

    client = TestClient(app)
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        user = TestUser(test_client, websocket=websocket)
        game_creation_message.value.difficulty = PhraseDifficulty.HARD.value
        user.websocket.send_json(game_creation_message.dict())
        game_created = Message(**user.websocket.receive_json())
        game_id = game_created.value.game_id
        test_data.game_id = game_id

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            user2 = TestUser(second_test_client, websocket=websocket2)
            game_join_message.game_id = game_id
            user2.websocket.send_json(game_join_message.dict())

            game_joined = Message(**user2.websocket.receive_json())
            assert game_joined.topic.operation == GameOperations.JOIN.value

            game_joined = Message(**user.websocket.receive_json())
            assert game_joined.topic.operation == GameOperations.JOIN.value

            game_start_message.game_id = game_id
            user.websocket.send_json(game_start_message.dict())

            not_enough_players = Message(**user.websocket.receive_json())
            assert not_enough_players.topic.type == TopicEnum.ERROR.value

            not_enough_players = Message(**user2.websocket.receive_json())
            assert not_enough_players.topic.type == TopicEnum.ERROR.value

            with client.websocket_connect(f"/ws/third_client") as websocket3:
                game_join_message.game_id = game_id
                game_join_message.username = "third_client"
                user3 = TestUser("third_client", websocket=websocket3)
                user3.websocket.send_json(game_join_message.dict())

                game_joined = Message(**user3.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_joined = Message(**user2.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_joined = Message(**user.websocket.receive_json())
                assert game_joined.topic.operation == GameOperations.JOIN.value

                game_start_message.game_id = game_id
                user.websocket.send_json(game_start_message.dict())

                expected_phrase = "Dummy Phrase of level EASY"
                hashed_phrase = "**********"

                def test_turn(user: TestUser, turn: int):
                    game_joined = Message(**user.websocket.receive_json())
                    assert game_joined.topic.operation == GameOperations.TURN.value
                    assert (
                        game_joined.value.turn.phrase == expected_phrase
                        if game_joined.value.turn.drawer == user.username
                        else hashed_phrase
                    )
                    assert game_joined.value.turn.turn_no == turn
                    assert game_joined.value.turn.level == game_creation_message.value.difficulty
                    return game_joined.value.turn.drawer

                test_turn(user=user, turn=1)
                test_turn(user=user2, turn=1)
                test_turn(user=user3, turn=1)

                test_turn(user=user, turn=2)
                test_turn(user=user2, turn=2)
                test_turn(user=user3, turn=2)

                test_turn(user=user, turn=3)
                test_turn(user=user2, turn=3)
                test_turn(user=user3, turn=3)

                assert Message(**user.websocket.receive_json()).topic.operation == GameOperations.END.value
                assert Message(**user2.websocket.receive_json()).topic.operation == GameOperations.END.value
                assert Message(**user3.websocket.receive_json()).topic.operation == GameOperations.END.value


def test_leaving_game_by_player(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    mocker,
    game_creation_message: Message,
    game_join_message: Message,
    game_start_message: Message,
    game_leave_message: Message
):
    mocker.patch(
        "codejam.server.controllers.chat_controller.ChatController.wait_till_next_turn",
        mocker.AsyncMock()
    )
    mocker.patch(
        "codejam.server.models.game.Game.generate_phrase",
        mocker.MagicMock(return_value="Dummy Phrase of level EASY")
    )

    mocker.patch(
        "codejam.server.models.game.Game.get_number_of_turns",
        mocker.MagicMock(return_value=2)
    )

    client = TestClient(app)
    users = []
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        user = TestUser(test_client, websocket=websocket)
        users.append(user)
        game_creation_message.value.difficulty = PhraseDifficulty.HARD.value
        user.websocket.send_json(game_creation_message.dict())
        game_created = Message(**user.websocket.receive_json())
        game_id = game_created.value.game_id
        test_data.game_id = game_id

        def assert_all_users_got_correct_message(operation):
            messages = [Message(**u.websocket.receive_json()) for u in users]
            assert all(message.topic.operation == operation for message in messages)

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            user2 = TestUser(second_test_client, websocket=websocket2)
            game_join_message.game_id = game_id
            user2.websocket.send_json(game_join_message.dict())
            users.append(user2)
            assert_all_users_got_correct_message(GameOperations.JOIN.value)

            with client.websocket_connect(f"/ws/third_client") as websocket3:
                game_join_message.game_id = game_id
                game_join_message.username = "third_client"
                user3 = TestUser("third_client", websocket=websocket3)
                user3.websocket.send_json(game_join_message.dict())
                users.append(user3)

                assert_all_users_got_correct_message(GameOperations.JOIN.value)

                with client.websocket_connect(f"/ws/4th_client") as websocket4:
                    game_join_message.game_id = game_id
                    game_join_message.username = "4th_client"
                    user4 = TestUser("4th_client", websocket=websocket4)
                    user4.websocket.send_json(game_join_message.dict())
                    users.append(user4)

                    assert_all_users_got_correct_message(GameOperations.JOIN.value)

                    game_start_message.game_id = game_id
                    user.websocket.send_json(game_start_message.dict())

                    expected_phrase = "Dummy Phrase of level EASY"
                    hashed_phrase = "**********"

                    def test_turn(user: TestUser, turn: int):
                        game_joined = Message(**user.websocket.receive_json())
                        assert game_joined.topic.operation == GameOperations.TURN.value
                        assert (
                            game_joined.value.turn.phrase == expected_phrase
                            if game_joined.value.turn.drawer == user.username
                            else hashed_phrase
                        )
                        assert game_joined.value.turn.turn_no == turn
                        assert game_joined.value.turn.level == game_creation_message.value.difficulty
                        return game_joined.value.turn.drawer

                    test_turn(user=user, turn=1)
                    test_turn(user=user2, turn=1)
                    test_turn(user=user3, turn=1)
                    test_turn(user=user4, turn=1)

                    user.websocket.send_json(game_start_message.dict())
                    assert_all_users_got_correct_message(ErrorOperations.BROADCAST.value)

                    game_leave_message.game_id = game_id
                    game_leave_message.username = user4.username
                    user4.websocket.send_json(game_leave_message.dict())

                    users.remove(user4)
                    assert_all_users_got_correct_message(GameOperations.LEAVE.value)

                    game_leave_message.game_id = game_id
                    game_leave_message.username = user3.username
                    user3.websocket.send_json(game_leave_message.dict())
                    users.remove(user3)

                    assert_all_users_got_correct_message(GameOperations.LEAVE.value)
                    assert_all_users_got_correct_message(ErrorOperations.BROADCAST.value)


def test_leaving_game_by_creator(
    test_client: str,
    second_test_client: str,
    test_data: Message,
    mocker,
    game_creation_message: Message,
    game_join_message: Message,
    game_start_message: Message,
    game_leave_message: Message
):

    mocker.patch(
        "codejam.server.controllers.chat_controller.ChatController.wait_till_next_turn",
        mocker.AsyncMock()
    )
    mocker.patch(
        "codejam.server.models.game.Game.generate_phrase",
        mocker.MagicMock(return_value="Dummy Phrase of level EASY")
    )

    mocker.patch(
        "codejam.server.models.game.Game.get_number_of_turns",
        mocker.MagicMock(return_value=2)
    )

    client = TestClient(app)
    users = []
    with client.websocket_connect(f"/ws/{test_client}") as websocket:
        user = TestUser(test_client, websocket=websocket)
        users.append(user)
        game_creation_message.value.difficulty = PhraseDifficulty.HARD.value
        user.websocket.send_json(game_creation_message.dict())
        game_created = Message(**user.websocket.receive_json())
        game_id = game_created.value.game_id
        test_data.game_id = game_id

        def assert_all_users_got_correct_message(operation):
            messages = [Message(**u.websocket.receive_json()) for u in users]
            assert all(message.topic.operation == operation for message in messages)

        with client.websocket_connect(f"/ws/{second_test_client}") as websocket2:
            user2 = TestUser(second_test_client, websocket=websocket2)
            game_join_message.game_id = game_id
            user2.websocket.send_json(game_join_message.dict())
            users.append(user2)
            assert_all_users_got_correct_message(GameOperations.JOIN.value)

            with client.websocket_connect(f"/ws/third_client") as websocket3:
                game_join_message.game_id = game_id
                game_join_message.username = "third_client"
                user3 = TestUser("third_client", websocket=websocket3)
                user3.websocket.send_json(game_join_message.dict())
                users.append(user3)

                assert_all_users_got_correct_message(GameOperations.JOIN.value)

                with client.websocket_connect(f"/ws/4th_client") as websocket4:
                    game_join_message.game_id = game_id
                    game_join_message.username = "4th_client"
                    user4 = TestUser("4th_client", websocket=websocket4)
                    user4.websocket.send_json(game_join_message.dict())
                    users.append(user4)

                    assert_all_users_got_correct_message(GameOperations.JOIN.value)

                    game_start_message.game_id = game_id
                    user.websocket.send_json(game_start_message.dict())

                    expected_phrase = "Dummy Phrase of level EASY"
                    hashed_phrase = "**********"

                    def test_turn(user: TestUser, turn: int):
                        game_joined = Message(**user.websocket.receive_json())
                        assert game_joined.topic.operation == GameOperations.TURN.value
                        assert (
                            game_joined.value.turn.phrase == expected_phrase
                            if game_joined.value.turn.drawer == user.username
                            else hashed_phrase
                        )
                        assert game_joined.value.turn.turn_no == turn
                        assert game_joined.value.turn.level == game_creation_message.value.difficulty
                        return game_joined.value.turn.drawer

                    test_turn(user=user, turn=1)
                    test_turn(user=user2, turn=1)
                    test_turn(user=user3, turn=1)
                    test_turn(user=user4, turn=1)

                    game_leave_message.game_id = game_id
                    game_leave_message.username = user.username
                    user.websocket.send_json(game_leave_message.dict())

                    assert_all_users_got_correct_message(ErrorOperations.BROADCAST.value)
