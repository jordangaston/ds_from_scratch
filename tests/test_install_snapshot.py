from ds_from_scratch.raft.model.raft import Role
from ds_from_scratch.sim.testing import RingBufferRandom


def test_snapshot(simulation_builder):
    save_snapshot = lambda log: log.length() >= 2

    simulation_builder.with_raft_node(hostname='raft_node_1',
                                      role=Role.FOLLOWER,
                                      prng=RingBufferRandom([10]),
                                      save_snapshot=save_snapshot)
    simulation_builder.with_raft_node(hostname='raft_node_2',
                                      role=Role.FOLLOWER,
                                      prng=RingBufferRandom([20]),
                                      save_snapshot=save_snapshot)
    simulation_builder.with_raft_node(hostname='raft_node_3',
                                      role=Role.FOLLOWER,
                                      prng=RingBufferRandom([20]),
                                      save_snapshot=save_snapshot)
    simulation = simulation_builder.build()

    simulation.run(until=20)

    simulation.disconnect_raft_nodes('raft_node_2')

    simulation.execute_cmd(
        'raft_node_1',
        'cmd_uid_1',
        'cmd_1'
    )

    simulation.execute_cmd(
        'raft_node_1',
        'cmd_uid_2',
        'cmd_2'
    )

    simulation.run(until=40)

    simulation.execute_cmd(
        'raft_node_1',
        'cmd_uid_3',
        'cmd_3'
    )

    simulation.run(until=60)

    simulation.connect_raft_nodes('raft_node_2')

    simulation.run(until=120)

    raft_node_1 = simulation.get_raft_state('raft_node_1')
    snapshot_1 = raft_node_1.get_snapshot()

    raft_node_2 = simulation.get_raft_state('raft_node_2')
    snapshot_2 = raft_node_2.get_snapshot()

    assert snapshot_1.last_index() == snapshot_2.last_index()
    assert snapshot_1.last_term() == snapshot_2.last_term()
