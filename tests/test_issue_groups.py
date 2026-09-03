from obm.models import ScanIssue
from obm.scan.issues import group_by_root, relative_to


def _issue(path, size=0):
    return ScanIssue(path=path, kind="denied", size=size)


def test_one_folder_and_all_its_subfolders_collapse_into_a_single_group():
    issues = [
        _issue("C:\\Users\\me\\AppData\\Local\\Temp\\a.tmp", 10),
        _issue("C:\\Users\\me\\AppData\\Local\\Temp\\deep\\b.tmp", 20),
        _issue("C:\\Users\\me\\AppData\\Roaming\\c.tmp", 30),
    ]

    groups = group_by_root(issues)

    assert len(groups) == 1
    assert groups[0].root == "C:\\Users\\me\\AppData"
    assert groups[0].total_size == 60


def test_the_label_is_the_deepest_folder_the_group_really_shares():
    issues = [
        _issue("C:\\Users\\me\\AppData\\Local\\Temp\\a.tmp"),
        _issue("C:\\Users\\me\\AppData\\Local\\Temp\\sub\\b.tmp"),
    ]

    assert group_by_root(issues)[0].root == "C:\\Users\\me\\AppData\\Local\\Temp"


def test_separate_roots_stay_separate_and_the_biggest_comes_first():
    issues = [
        _issue("C:\\Users\\me\\Documents\\small.doc", 5),
        _issue("D:\\Media\\huge.mkv", 900),
    ]

    groups = group_by_root(issues)

    assert [g.root for g in groups] == ["D:\\Media", "C:\\Users\\me\\Documents"]


def test_issues_inside_a_group_are_ordered_biggest_first():
    issues = [
        _issue("C:\\Users\\me\\Docs\\small.doc", 5),
        _issue("C:\\Users\\me\\Docs\\big.doc", 500),
    ]

    assert [i.size for i in group_by_root(issues)[0].issues] == [500, 5]


def test_grouping_is_case_insensitive():
    issues = [
        _issue("C:\\Users\\Me\\Docs\\a.doc"),
        _issue("c:\\users\\me\\docs\\b.doc"),
    ]

    assert len(group_by_root(issues)) == 1


def test_a_file_at_a_drive_root_still_groups():
    groups = group_by_root([_issue("C:\\loose.txt")])

    assert len(groups) == 1
    assert groups[0].root == "C:\\"


def test_relative_to_strips_the_group_root():
    assert relative_to("C:\\Users\\me", "C:\\Users\\me\\Docs\\a.doc") == "Docs\\a.doc"
    assert relative_to("C:\\", "C:\\loose.txt") == "loose.txt"


def test_relative_to_leaves_an_unrelated_path_alone():
    assert relative_to("C:\\Users\\me", "D:\\other.txt") == "D:\\other.txt"


def test_no_issues_means_no_groups():
    assert group_by_root([]) == []
