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


def is_detail_expected(self, detail: dict, expected_list: List[dict]) -> bool:
    """
    Check if the detail is in the expected format
    """

    def is_subset_dict(subset_dict: dict, main_dict: dict):
        for key, value in subset_dict.items():
            if value != main_dict[key]:
                return False
        return True

    for expected in expected_list:
        try:
            self.assertEqual(detail['action'], expected['action'])
            self.assertEqual(detail['model'], expected['model'])
            self.assertIn('ref_id', detail)

            # The expected is the bare minimum, so we need to check if the expected data is a subset of the actual data
            self.assertTrue(is_subset_dict(main_dict=detail['data'], subset_dict=expected['data']))

            return True
        except AssertionError:
            continue
    return False
