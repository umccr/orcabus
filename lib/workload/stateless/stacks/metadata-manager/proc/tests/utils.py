from typing import List


def check_put_event_entries_format(self, entry):
    self.assertIn('Source', entry)
    self.assertIn('DetailType', entry)
    self.assertIn('Detail', entry)
    self.assertIn('EventBusName', entry)


def check_put_event_value(self, entry: dict, source: str, detail_type: str, event_bus_name: str):
    self.assertEqual(entry['Source'], source)
    self.assertEqual(entry['DetailType'], detail_type)
    self.assertEqual(entry['EventBusName'], event_bus_name)


def is_expected_event_in_output(self, expected: dict, output: List[dict]) -> bool:
    """
    Check if the expected event is in the output list
    """

    def is_subset_dict(subset_dict: dict, main_dict: dict):
        for key, value in subset_dict.items():
            if value != main_dict[key]:
                return False
        return True

    for o in output:

        try:
            self.assertEqual(expected['action'], o['action'])
            self.assertEqual(expected['model'], o['model'])
            self.assertIn('refId', o)

            # The expected is the bare minimum data, so we need to check if the expected data is a subset of the
            # actual data
            self.assertTrue(is_subset_dict(main_dict=o['data'], subset_dict=expected['data']))
            return True
        except AssertionError:
            continue

    return False
