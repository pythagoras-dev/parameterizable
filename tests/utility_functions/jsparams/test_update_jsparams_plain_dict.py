
from mixinforge.utility_functions.json_processor import dumpjs, loadjs, update_jsparams


def test_update_jsparams_on_plain_dict_updates_DICT_block():
    js = dumpjs({"a": 1})
    js2 = update_jsparams(js, b=2, a=5)

    data = loadjs(js2)
    assert data == {"a": 5, "b": 2}
