import pytest
from vsdx import VisioFile
from datetime import datetime
import os


def test_file_closure():
    filename = 'test1.vsdx'
    directory = f"./{filename.rsplit('.', 1)[0]}"
    with VisioFile(filename) as vis:
        # confirm directory exists
        assert os.path.exists(directory)
    # confirm directory is gone
    assert not os.path.exists(directory)


@pytest.mark.parametrize("filename, page_name", [("test1.vsdx","Page-1"), ("test2.vsdx", "Page-1")])
def test_get_page(filename: str, page_name: str):
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        # confirm page name as expected
        assert page.name == page_name


@pytest.mark.parametrize("filename, count", [("test1.vsdx", 1), ("test2.vsdx", 1)])
def test_get_page_shapes(filename: str, count: int):
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        print(f"shape count={len(page.shapes)}")
        assert len(page.shapes) == count


@pytest.mark.parametrize("filename, count", [("test1.vsdx", 4), ("test2.vsdx", 6)])
def test_get_page_sub_shapes(filename: str, count: int):
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shapes = page.shapes[0].sub_shapes()
        print(f"shape count={len(shapes)}")
        assert len(shapes) == count


@pytest.mark.parametrize("filename, expected_locations",
                         [("test1.vsdx","1.33,10.66 4.13,10.66 6.94,10.66 2.33,9.02 "),
                          ("test2.vsdx","2.33,8.72 1.33,10.66 4.13,10.66 5.91,8.72 1.61,8.58 3.25,8.65 ")])
def test_shape_locations(filename: str, expected_locations: str):
    print("=== list_shape_locations ===")
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shapes = page.shapes[0].sub_shapes()
        locations = ""
        for s in shapes:  # type: VisioFile.Shape
            locations+=f"{s.x:.2f},{s.y:.2f} "
        print(f"Expected:{expected_locations}")
        print(f"  Actual:{locations}")
    assert locations == expected_locations


@pytest.mark.parametrize("filename, shape_id", [("test1.vsdx", "6"), ("test2.vsdx", "6")])
def test_get_shape_with_text(filename: str, shape_id: str):
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shape = page.shapes[0].find_shape_by_text('{{date}}')  # type: VisioFile.Shape
        assert shape.ID == shape_id


@pytest.mark.parametrize("filename", ["test1.vsdx", "test2.vsdx", "test3_house.vsdx"])
def test_apply_context(filename: str):
    date_str = str(datetime.today().date())
    context = {'scenario': 'test',
               'date': date_str}
    out_file = 'out'+ os.sep + filename[:-5] + '_VISfilter_applied.vsdx'
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        original_shape = page.shapes[0].find_shape_by_text('{{date}}')  # type: VisioFile.Shape
        assert original_shape.ID
        page.apply_text_context(context)
        vis.save_vsdx(out_file)

    # open and find date_str
    with VisioFile(out_file) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        updated_shape = page.shapes[0].find_shape_by_text(date_str)  # type: VisioFile.Shape
        assert updated_shape.ID == original_shape.ID


@pytest.mark.parametrize("filename", ["test1.vsdx", "test2.vsdx", "test3_house.vsdx"])
def test_find_replace(filename: str):
    old = 'Shape'
    new = 'Figure'
    out_file = 'out'+ os.sep + filename[:-5] + '_VISfind_replace_applied.vsdx'
    with VisioFile(filename) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        original_shapes = page.find_shapes_by_text(old)  # type: VisioFile.Shape
        shape_ids = [s.ID for s in original_shapes]
        page.find_replace(old, new)
        vis.save_vsdx(out_file)

    # open and find date_str
    with VisioFile(out_file) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        # test that each shape if has 'new' str in text
        for shape_id in shape_ids:
            shape = page.find_shape_by_id(shape_id)
            assert new in shape.text


@pytest.mark.parametrize("filename", ["test2.vsdx", "test3_house.vsdx"])
def test_remove_shape(filename: str):
    out_file = 'out' + os.sep + filename[:-5] + '_shape_removed.vsdx'
    with VisioFile(filename) as vis:
        shapes = vis.page_objects[0].shapes
        # get shape to remove
        s = shapes[0].find_shape_by_text('Shape to remove')  # type: VisioFile.Shape
        assert s  # check shape found
        s.remove()
        vis.save_vsdx(out_file)

    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get shape that should have been removed
        s = shapes[0].find_shape_by_text('Shape to remove')  # type: VisioFile.Shape
        assert s is None  # check shape not found


@pytest.mark.parametrize(("filename", "shape_names", "shape_locations"),
                         [("test1.vsdx", {"Shape to remove"}, {(1.0,1.0)})])
def test_set_shape_location(filename: str, shape_names: set, shape_locations: set):
    out_file = 'out'+ os.sep + filename[:-5] + '_test_set_shape_location.vsdx'
    with VisioFile(filename) as vis:
        shapes = vis.page_objects[0].shapes
        # move shapes in list
        for (shape_name, x_y) in zip(shape_names, shape_locations):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x
            assert s.y
            print(f"Moving shape '{shape_name}' from {s.x}, {s.y} to {x_y}")
            s.x = x_y[0]
            s.y = x_y[1]
        vis.save_vsdx(out_file)

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get each shape that should have been moved
        for (shape_name, x_y) in zip(shape_names, shape_locations):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x == x_y[0]
            assert s.y == x_y[1]


@pytest.mark.parametrize(("filename", "shape_names", "shape_x_y_deltas"),
                         [("test1.vsdx", {"Shape to remove"}, {(1.0,1.0)}),
                          ("test4_connectors.vsdx", {"Shape B"}, {(1.0,1.0)})])
def test_move_shape(filename: str, shape_names: set, shape_x_y_deltas: set):
    out_file = 'out'+ os.sep + filename[:-5] + '_test_move_shape.vsdx'
    expected_shape_locations = dict()

    with VisioFile(filename) as vis:
        shapes = vis.page_objects[0].shapes
        # move shapes in list
        for (shape_name, x_y) in zip(shape_names, shape_x_y_deltas):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x
            assert s.y
            expected_shape_locations[shape_name] = (s.x + x_y[0], s.y + x_y[1])
            s.move(x_y[0], x_y[1])

        vis.save_vsdx(out_file)
    print(f"expected_shape_locations={expected_shape_locations}")

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get each shape that should have been moved
        for shape_name in shape_names:
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x == expected_shape_locations[shape_name][0]
            assert s.y == expected_shape_locations[shape_name][1]


@pytest.mark.parametrize(("filename", "expected_connects"),
                         [('test4_connectors.vsdx', ["from 7 to 5","from 7 to 2", "from 6 to 2", "from 6 to 1"]),
                          ])
def test_find_page_connects(filename: str, expected_connects: list):
    with VisioFile(filename) as vis:
        page = vis.page_objects[0]  # type: VisioFile.Page
        actual_connects = list()
        for c in page.connects:  # type: VisioFile.Connect
            actual_connects.append(f"from {c.from_id} to {c.to_id}")
        assert sorted(actual_connects) == sorted(expected_connects)


@pytest.mark.parametrize(("filename", "shape_id", "expected_shape_ids"),
                         [
                             ('test4_connectors.vsdx', "1", ["6"]),
                             ('test4_connectors.vsdx', "2", ["6", "7"]),
                          ])
def test_find_connected_shapes(filename: str, shape_id: str, expected_shape_ids: list):
    with VisioFile(filename) as vis:
        page = vis.page_objects[0]  # type: VisioFile.Page
        actual_connect_shape_ids = list()
        shape = page.find_shape_by_id(shape_id)
        for c_shape in shape.connected_shapes:  # type: VisioFile.Shape
            actual_connect_shape_ids.append(c_shape.ID)
        assert sorted(actual_connect_shape_ids) == sorted(expected_shape_ids)


@pytest.mark.parametrize(("filename", "shape_id", "expected_shape_ids", "expected_from", "expected_to", "expected_from_rels", "expected_to_rels"),
                         [
                             ('test4_connectors.vsdx', "1", ["6"], ["6"], ["1"], ['BeginX'], ['PinX']),
                             ('test4_connectors.vsdx', "2", ["6", "7"], ["6", "7"], ["2", "2"], ['BeginX', 'EndX'], ['PinX', 'PinX']),
                             ('test4_connectors.vsdx', "6", ["1", "2"], ["6", "6"], ["1", "2"], ['BeginX', 'EndX'], ['PinX', 'PinX']),
                             ('test4_connectors.vsdx', "7", ["5", "2"], ["7", "7"], ["5", "2"], ['BeginX', 'EndX'], ['PinX', 'PinX']),
                          ])
def test_find_connected_shape_relationships(filename: str, shape_id: str, expected_shape_ids: list, expected_from: list,
                                            expected_to: list, expected_from_rels: list, expected_to_rels: list):
    with VisioFile(filename) as vis:
        page = vis.page_objects[0]  # type: VisioFile.Page

        shape = page.find_shape_by_id(shape_id)
        shape_ids = [s.ID for s in shape.connected_shapes]
        from_ids = [c.from_id for c in shape.connects]
        to_ids = [c.to_id for c in shape.connects]
        from_rels = [c.from_rel for c in shape.connects]
        to_rels = [c.to_rel for c in shape.connects]

        assert sorted(shape_ids) == sorted(expected_shape_ids)
        assert sorted(from_ids) == sorted(expected_from)
        assert sorted(to_ids) == sorted(expected_to)
        assert sorted(from_rels) == sorted(expected_from_rels)
        assert sorted(to_rels) == sorted(expected_to_rels)


@pytest.mark.parametrize(("filename", "shape_a_id", "shape_b_id", "expected_connector_ids"),
                         [
                             ('test4_connectors.vsdx', "1", "2", ["6"]),
                             ('test4_connectors.vsdx', "1", "5", []),  # expect no connections
                          ])
def test_find_connectors_between_ids(filename: str, shape_a_id: str, shape_b_id: str,  expected_connector_ids: list):
    with VisioFile(filename) as vis:
        page = vis.page_objects[0]  # type: VisioFile.Page
        connectors = page.get_connectors_between(shape_a_id=shape_a_id, shape_b_id=shape_b_id)
        actual_connector_ids = sorted([c.ID for c in connectors])
        assert sorted(expected_connector_ids) == list(actual_connector_ids)


@pytest.mark.parametrize(("filename", "shape_a_text", "shape_b_text", "expected_connector_ids"),
                         [
                             ('test4_connectors.vsdx', "Shape A", "Shape B", ["6"]),
                             ('test4_connectors.vsdx', "Shape A", "Shape C", []),  # expect no connections
                          ])
def test_find_connectors_between_shapes(filename: str, shape_a_text: str, shape_b_text: str,  expected_connector_ids: list):
    with VisioFile(filename) as vis:
        page = vis.page_objects[0]  # type: VisioFile.Page
        connectors = page.get_connectors_between(shape_a_text=shape_a_text, shape_b_text=shape_b_text)
        actual_connector_ids = sorted([c.ID for c in connectors])
        assert sorted(expected_connector_ids) == list(actual_connector_ids)


@pytest.mark.parametrize(("filename", "shape_name"),
                         [("test1.vsdx", "Shape to copy"),
                          ("test4_connectors.vsdx", "Shape B")])
def test_vis_copy_shape(filename: str, shape_name: str):
    out_file = 'out'+ os.sep + filename[:-5] + '_test_vis_copy_shape.vsdx'

    with VisioFile(filename) as vis:
        page =  vis.page_objects[0]  # type: VisioFile.Page
        # find and copy shape by name
        s = page.find_shape_by_text(shape_name)  # type: VisioFile.Shape
        assert s  # check shape found
        print(f"Found shape id:{s.ID}")
        max_id = vis.page_max_ids[page.filename]

        # note = this does add the shape, but prefer Shape.copy as per next test which wraps this and returns Shape
        page.set_max_ids()
        new_shape = vis.copy_shape(shape=s.xml, page=page.xml, page_path=page.filename)

        assert new_shape  # check copy_shape returns xml
        
        print(f"created new shape {type(new_shape)} {new_shape} {new_shape.attrib['ID']}")
        assert new_shape.attrib.get('ID') > s.ID

        new_shape_id = new_shape.attrib['ID']
        vis.save_vsdx(out_file)

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        page = vis.page_objects[0]
        s = page.find_shape_by_id(new_shape_id)
        assert s


@pytest.mark.parametrize(("filename", "shape_name"),
                         [("test1.vsdx", "Shape to copy"),])
def test_copy_shape_other_page(filename: str, shape_name: str):
    out_file = 'out'+ os.sep + filename[:-5] + '_test_copy_shape_other_page.vsdx'

    with VisioFile(filename) as vis:
        page =  vis.page_objects[0]  # type: VisioFile.Page
        page2 = vis.page_objects[1]  # type: VisioFile.Page
        # find and copy shape by name
        s = page.find_shape_by_text(shape_name)  # type: VisioFile.Shape
        assert s  # check shape found
        print(f"Found shape id:{s.ID}")
        max_id = vis.page_max_ids[page2.filename]

        new_shape = vis.copy_shape(shape=s.xml, page=page2.xml, page_path=page2.filename)
        assert new_shape  # check copy_shape returns xml
        assert new_shape.attrib.get('ID') == str(max_id + 1)
        print(f"created new shape {type(new_shape)} {new_shape} {new_shape.attrib['ID']}")
        new_shape_id = new_shape.attrib['ID']
        vis.save_vsdx(out_file)

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        page = vis.page_objects[1]
        s = page.find_shape_by_id(new_shape_id)
        assert s


@pytest.mark.parametrize(("filename", "shape_name"),
                         [("test1.vsdx", "Shape to copy"),
                          ("test4_connectors.vsdx", "Shape B")])
def test_shape_copy(filename: str, shape_name: str):
    out_file = 'out'+ os.sep + filename[:-5] + '_test_shape_copy.vsdx'

    with VisioFile(filename) as vis:
        page =  vis.page_objects[0]  # type: VisioFile.Page
        # find and copy shape by name
        s = page.find_shape_by_text(shape_name)  # type: VisioFile.Shape
        assert s  # check shape found
        print(f"found {s.ID}")
        max_id = vis.page_max_ids[page.filename]

        new_shape = s.copy()
        assert new_shape  # check new shape exists
        
        print(f"original shape {type(s)} {s} {s.ID}")
        print(f"created new shape {type(new_shape)} {new_shape} {new_shape.ID}")
        assert new_shape.ID > s.ID  # and new shape has > ID than original
        updated_text = s.text + " (new copy)"
        new_shape.text = updated_text  # update text of new shape

        new_shape_id = new_shape.ID
        vis.save_vsdx(out_file)

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        page = vis.page_objects[0]
        s = page.find_shape_by_id(new_shape_id)
        assert s
        # check that new shape has expected text
        assert s.text == updated_text


@pytest.mark.parametrize(("filename", "expected_length"),
                         [('test5_master.vsdx', 1)])
def test_load_master_file(filename: str, expected_length: int):
    with VisioFile(os.path.join(filename)) as vis:
        assert len(vis.master_pages) == expected_length


@pytest.mark.parametrize(("filename", "shape_text"),
                         [('test5_master.vsdx', "Shape B")])
def test_find_master_shape(filename: str, shape_text: str):
    with VisioFile(os.path.join(filename)) as vis:
        master_page =  vis.master_page_objects[0]  # type: VisioFile.Page
        s = master_page.find_shape_by_text(shape_text)
        assert s


@pytest.mark.skip('master inheritence not yet implemented')
@pytest.mark.parametrize(("filename"),
                         [('test5_master.vsdx')])
def test_master_inheritance(filename: str):
    with VisioFile(os.path.join(filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        master_page = vis.master_page_objects[0]  # type: VisioFile.Page
        shape_a = page.find_shapes_by_text('Shape A')  # type: VisioFile.Shape
        shape_b = page.find_shapes_by_text('Shape B')  # type: VisioFile.Shape

        for s in page.shapes[0].sub_shapes():
            print(f"\n\nshape {s.ID} '{s.text}' MasterID:{s.master_shape_ID}")
            for sub in s.sub_shapes():
                print(f"\nsubshape {sub.ID} '{sub.text}' MasterID:{sub.master_shape_ID}")
                # nte this is not the correct link to master shape
                master_shape = master_page.find_shape_by_id(sub.master_shape_ID)
                print(f"master={master_shape}")

        # these tests fail until master shape link in place for Shape.text
        assert shape_a
        assert shape_b
