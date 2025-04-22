import unittest

from dipt.utils import nested_dict_to_edges, rename_nodes_to_ids

class TestGraph(unittest.TestCase):
    def test_nested_dict_to_edges(self):
        test_dict = {"A": {"B": {"D": {"F": {}}}, "C": {"E": {}}}}
        self.assertEqual(set(nested_dict_to_edges(test_dict)),
                         set([("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"), ("D", "F")]))

    def test_rename_nodes_to_ids(self):
        test_dict = {"A": {"B": {"D": {"F": {}}}, "C": {"E": {}}}}
        test_edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"), ("D", "F")]
        id_edges, id_to_node, node_to_id = rename_nodes_to_ids(test_dict, test_edges)
        print(id_edges)
        print(id_to_node)
        # nodes are sorted breadth first, so we would expect A=0, B=1, ...
        expected_renaming = set([(0, 1), (0, 2), (1, 3), (2, 4), (3, 5)])
        self.assertEqual(set(id_edges), expected_renaming)

        expected_mapping = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F'}
        self.assertDictEqual(id_to_node, expected_mapping)


if __name__ == '__main__':
    unittest.main()
