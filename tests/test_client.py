import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from flipper import Condition, FeatureFlagClient, MemoryFeatureFlagStore
from flipper.bucketing import Percentage, PercentageBucketer
from flipper.contrib.storage import FeatureFlagStoreMeta
from flipper.flag import FeatureFlag, FlagDoesNotExistError


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.store = MemoryFeatureFlagStore()
        self.client = FeatureFlagClient(self.store)

    def txt(self):
        return uuid4().hex


class TestIsEnabled(BaseTest):
    def test_returns_true_when_feature_enabled(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.enable(feature_name)

        self.assertTrue(self.client.is_enabled(feature_name))

    def test_returns_false_when_feature_disabled(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.disable(feature_name)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_returns_false_when_feature_does_not_exist(self):
        feature_name = self.txt()

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_returns_true_if_condition_specifies(self):
        feature_name = self.txt()

        self.client.create(feature_name, is_enabled=True)
        self.client.add_condition(feature_name, Condition(foo=True))

        self.assertTrue(self.client.is_enabled(feature_name, foo=True))

    def test_returns_false_if_condition_specifies(self):
        feature_name = self.txt()

        self.client.create(feature_name, is_enabled=True)
        self.client.add_condition(feature_name, Condition(foo=True))

        self.assertFalse(self.client.is_enabled(feature_name, foo=False))

    def test_returns_false_if_feature_disabled_despite_condition(self):
        feature_name = self.txt()

        self.client.create(feature_name, is_enabled=False)
        self.client.add_condition(feature_name, Condition(foo=True))

        self.assertFalse(self.client.is_enabled(feature_name, foo=True))

    def test_returns_false_if_bucketer_check_returns_false(self):
        feature_name = self.txt()

        bucketer = MagicMock()
        bucketer.check.return_value = False

        self.client.create(feature_name, is_enabled=True)
        self.client.set_bucketer(feature_name, bucketer)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_returns_true_if_bucketer_check_returns_true(self):
        feature_name = self.txt()

        bucketer = MagicMock()
        bucketer.check.return_value = True

        self.client.create(feature_name, is_enabled=True)
        self.client.set_bucketer(feature_name, bucketer)

        self.assertTrue(self.client.is_enabled(feature_name))

    def test_forwards_conditions_to_bucketer(self):
        feature_name = self.txt()

        bucketer = MagicMock()

        self.client.create(feature_name, is_enabled=True)
        self.client.set_bucketer(feature_name, bucketer)

        self.client.is_enabled(feature_name, foo=True)

        bucketer.check.assert_called_with(foo=True)


class TestCreate(BaseTest):
    def test_creates_and_returns_instance_of_feature_flag_class(self):
        feature_name = self.txt()

        flag = self.client.create(feature_name)

        self.assertTrue(isinstance(flag, FeatureFlag))

    def test_creates_flag_with_correct_name(self):
        feature_name = self.txt()

        flag = self.client.create(feature_name)

        self.assertEqual(feature_name, flag.name)

    def test_is_enabled_defaults_to_false(self):
        feature_name = self.txt()

        self.client.create(feature_name)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_flag_can_be_enabled_on_create(self):
        feature_name = self.txt()

        self.client.create(feature_name, is_enabled=True)

        self.assertTrue(self.client.is_enabled(feature_name))


class TestGet(BaseTest):
    def test_returns_instance_of_feature_flag_class(self):
        feature_name = self.txt()

        self.client.create(feature_name)

        flag = self.client.get(feature_name)

        self.assertTrue(isinstance(flag, FeatureFlag))

    def test_returns_flag_with_correct_name(self):
        feature_name = self.txt()

        self.client.create(feature_name)

        flag = self.client.get(feature_name)

        self.assertEqual(feature_name, flag.name)


class TestDestroy(BaseTest):
    def test_get_will_return_instance_of_flag(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.destroy(feature_name)

        flag = self.client.get(feature_name)

        self.assertTrue(isinstance(flag, FeatureFlag))

    def test_status_switches_to_disabled(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.enable(feature_name)
        self.client.destroy(feature_name)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()

        with self.assertRaises(FlagDoesNotExistError):
            self.client.destroy(feature_name)


class TestEnable(BaseTest):
    def test_is_enabled_will_be_true(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.enable(feature_name)

        self.assertTrue(self.client.is_enabled(feature_name))

    def test_is_enabled_will_be_true_if_disable_was_called_earlier(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.disable(feature_name)
        self.client.enable(feature_name)

        self.assertTrue(self.client.is_enabled(feature_name))

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()

        with self.assertRaises(FlagDoesNotExistError):
            self.client.enable(feature_name)


class TestDisable(BaseTest):
    def test_is_enabled_will_be_false(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.disable(feature_name)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_is_enabled_will_be_false_if_enable_was_called_earlier(self):
        feature_name = self.txt()

        self.client.create(feature_name)
        self.client.enable(feature_name)
        self.client.disable(feature_name)

        self.assertFalse(self.client.is_enabled(feature_name))

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()

        with self.assertRaises(FlagDoesNotExistError):
            self.client.disable(feature_name)


class TestExists(BaseTest):
    def test_exists_is_false_when_feature_does_not_exist(self):
        feature_name = self.txt()

        self.assertFalse(self.client.exists(feature_name))

    def test_exists_is_true_when_feature_does_exist(self):
        feature_name = self.txt()
        self.client.create(feature_name)

        self.assertTrue(self.client.exists(feature_name))


class TestList(BaseTest):
    def test_calls_backend_with_correct_args(self):
        self.store.list = MagicMock()

        limit, offset = 10, 25
        list(self.client.list(limit=limit, offset=offset))

        self.store.list.assert_called_once_with(limit=limit, offset=offset)

    def test_returns_flag_objects(self):
        feature_name = self.txt()

        self.client.create(feature_name)

        flag = next(self.client.list())

        self.assertIsInstance(flag, FeatureFlag)

    def test_returns_correct_flag_objects(self):
        feature_name = self.txt()

        expected = self.client.create(feature_name)

        actual = next(self.client.list())

        self.assertEqual(expected.name, actual.name)

    def test_returns_correct_count_of_flag_objects(self):
        feature_names = [self.txt() for _ in range(10)]

        for feature_name in feature_names:
            self.client.create(feature_name)

        actual = list(self.client.list())

        self.assertEqual(len(feature_names), len(actual))


class TestSetClientData(BaseTest):
    def test_calls_backend_with_correct_feature_name(self):
        self.store.set_meta = MagicMock()

        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name)
        self.client.set_client_data(feature_name, client_data)

        [actual, _] = self.store.set_meta.call_args[0]

        self.assertEqual(feature_name, actual)

    def test_calls_backend_with_instance_of_meta(self):
        self.store.set_meta = MagicMock()

        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name)
        self.client.set_client_data(feature_name, client_data)

        [_, meta] = self.store.set_meta.call_args[0]

        self.assertIsInstance(meta, FeatureFlagStoreMeta)

    def test_calls_backend_with_correct_meta_client_data(self):
        self.store.set_meta = MagicMock()

        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name)
        self.client.set_client_data(feature_name, client_data)

        [_, meta] = self.store.set_meta.call_args[0]

        self.assertEqual(client_data, meta.client_data)

    def test_calls_backend_with_non_null_meta_created_date(self):
        self.store.set_meta = MagicMock()

        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name)
        self.client.set_client_data(feature_name, client_data)

        [_, meta] = self.store.set_meta.call_args[0]

        self.assertIsNotNone(meta.created_date)

    def test_calls_backend_exactly_once(self):
        self.store.set_meta = MagicMock()

        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name)
        self.client.set_client_data(feature_name, client_data)

        self.assertEqual(1, self.store.set_meta.call_count)

    def test_merges_new_values_with_existing(self):
        feature_name = self.txt()
        existing_data = {"existing_key": self.txt()}

        self.store.create(feature_name, client_data=existing_data)

        new_data = {"new_key": self.txt()}
        self.client.set_client_data(feature_name, new_data)

        item = self.store.get(feature_name)

        self.assertEqual({**existing_data, **new_data}, item.meta["client_data"])

    def test_can_override_existing_values(self):
        feature_name = self.txt()
        existing_data = {"existing_key": self.txt()}

        self.store.create(feature_name, client_data=existing_data)

        new_data = {"existing_key": self.txt(), "new_key": self.txt()}
        self.client.set_client_data(feature_name, new_data)

        item = self.store.get(feature_name)

        self.assertEqual(new_data, item.meta["client_data"])

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        with self.assertRaises(FlagDoesNotExistError):
            self.client.set_client_data(feature_name, client_data)


class TestGetClientData(BaseTest):
    def test_gets_expected_key_value_pairs(self):
        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name, client_data=client_data)

        result = self.client.get_client_data(feature_name)

        self.assertEqual(client_data, result)

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()

        with self.assertRaises(FlagDoesNotExistError):
            self.client.get_client_data(feature_name)


class TestGetMeta(BaseTest):
    def test_includes_created_date(self):
        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name, client_data=client_data)

        meta = self.client.get_meta(feature_name)

        self.assertTrue("created_date" in meta)

    def test_includes_client_data(self):
        feature_name = self.txt()
        client_data = {self.txt(): self.txt()}

        self.client.create(feature_name, client_data=client_data)

        meta = self.client.get_meta(feature_name)

        self.assertEqual(client_data, meta["client_data"])

    def test_raises_for_nonexistent_flag(self):
        feature_name = self.txt()

        with self.assertRaises(FlagDoesNotExistError):
            self.client.get_meta(feature_name)


class TestAddCondition(BaseTest):
    def test_condition_gets_included_in_meta(self):
        feature_name = self.txt()
        condition_checks = {self.txt(): True}
        condition = Condition(**condition_checks)

        self.client.create(feature_name)
        self.client.add_condition(feature_name, condition)

        meta = self.client.get_meta(feature_name)

        self.assertTrue(condition.to_dict() in meta["conditions"])

    def test_condition_gets_appended_to_meta(self):
        feature_name = self.txt()
        condition_checks = {self.txt(): True}
        condition = Condition(**condition_checks)

        self.client.create(feature_name)
        self.client.add_condition(feature_name, condition)
        self.client.add_condition(feature_name, condition)

        meta = self.client.get_meta(feature_name)

        self.assertEqual(2, len(meta["conditions"]))


class TestSetBucketer(BaseTest):
    def test_bucketer_gets_included_in_meta(self):
        feature_name = self.txt()

        percentage_value = 0.1
        bucketer = PercentageBucketer(percentage=Percentage(percentage_value))

        self.client.create(feature_name)
        self.client.set_bucketer(feature_name, bucketer)

        meta = self.client.get_meta(feature_name)

        self.assertEqual(bucketer.to_dict(), meta["bucketer"])
