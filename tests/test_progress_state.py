import threading

from obm.ui.progress import ProgressState


def test_snapshot_returns_counts_and_stages_in_order():
    state = ProgressState()
    state.stage("Checking for locked files")
    state.update(3, 10)
    state.stage("Compressing")

    done, total, stages = state.snapshot()

    assert (done, total) == (3, 10)
    assert stages == ["Checking for locked files", "Compressing"]


def test_snapshot_stages_are_a_copy_the_caller_cannot_corrupt():
    state = ProgressState()
    state.stage("one")

    _, _, stages = state.snapshot()
    stages.append("two")

    assert state.snapshot()[2] == ["one"]


def test_stages_from_many_threads_all_land():
    state = ProgressState()
    threads = [threading.Thread(target=state.stage, args=(str(i),)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(int(s) for s in state.snapshot()[2]) == list(range(20))
