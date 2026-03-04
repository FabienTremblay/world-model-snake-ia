
def test_lineage():
    parent_hash="abc"
    child_hash="def"

    lineage={
        "parent":{"hash":parent_hash},
        "enfant":{"hash":child_hash}
    }

    assert lineage["parent"]["hash"]=="abc"
    assert lineage["enfant"]["hash"]=="def"
