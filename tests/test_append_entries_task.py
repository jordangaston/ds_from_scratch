from ds_from_scratch.raft.task import AppendEntriesTask, ElectionTask, HeartbeatTask
from ds_from_scratch.raft.state import RaftState
from ds_from_scratch.raft.util import Role, Executor, MessageGateway


def test_entries_rejected_with_state_leader(mocker):
    raft = RaftState(address='raft_node_1', role=Role.FOLLOWER, current_term=5)
    msg_gateway = MessageGateway()

    task = AppendEntriesTask(
        raft=raft,
        msg_gateway=msg_gateway,
        executor=None,
        msg={'sender': 'raft_node_2', 'senders_term': 1}
    )

    mocker.patch.object(msg_gateway, 'send_append_entries_response')

    task.run()

    msg_gateway.send_append_entries_response.assert_called_once_with(sender=raft, receiver='raft_node_2', ok=False)


def test_candidate(mocker):
    raft = RaftState(address='raft_node_1', role=Role.CANDIDATE, current_term=5)
    msg_gateway = MessageGateway()
    executor = Executor(executor=None)

    task = AppendEntriesTask(
        raft=raft,
        msg_gateway=msg_gateway,
        executor=executor,
        msg={'sender': 'raft_node_2', 'senders_term': 10}
    )

    mocker.patch.object(raft, 'become_follower')
    mocker.patch.object(raft, 'next_election_timeout')
    raft.next_election_timeout.return_value = 12
    mocker.patch.object(executor, 'cancel')
    mocker.patch.object(executor, 'schedule')
    mocker.patch.object(msg_gateway, 'send_append_entries_response')

    task.run()

    raft.become_follower.assert_called_once_with(leaders_term=10)
    executor.cancel.assert_called_once_with(HeartbeatTask)
    executor.schedule.assert_called_once()
    args = executor.schedule.call_args[1]
    assert type(args['task']) is ElectionTask
    assert args['delay'] == 12
    msg_gateway.send_append_entries_response.assert_called_once_with(sender=raft, receiver='raft_node_2', ok=True)


def test_follower(mocker):
    raft = RaftState(address='raft_node_1', role=Role.FOLLOWER, current_term=5)
    msg_gateway = MessageGateway()
    executor = Executor(executor=None)

    task = AppendEntriesTask(
        raft=raft,
        msg_gateway=msg_gateway,
        executor=executor,
        msg={'sender': 'raft_node_2', 'senders_term': 10}
    )

    mocker.patch.object(raft, 'heard_from_peer')
    mocker.patch.object(raft, 'next_election_timeout')
    raft.next_election_timeout.return_value = 12
    mocker.patch.object(executor, 'schedule')
    mocker.patch.object(executor, 'cancel')
    mocker.patch.object(msg_gateway, 'send_append_entries_response')

    task.run()

    raft.heard_from_peer.assert_called_once_with(peers_term=10)
    executor.cancel.assert_called_once_with(ElectionTask)
    executor.schedule.assert_called_once()
    args = executor.schedule.call_args[1]
    assert type(args['task']) is ElectionTask
    assert args['delay'] == 12
    msg_gateway.send_append_entries_response.assert_called_once_with(sender=raft, receiver='raft_node_2', ok=True)