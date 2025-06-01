from unittest import TestCase

from lawyer.utils import remove_citation_of_file


class UtilsTest(TestCase):
    def test_remove_citation_of_file(self):
        # given
        bad_part = """【4:article6.txt】【16:article6.txt】"""
        text = """Торговом реестре Республики Беларусь» и требования к интернет-магазинам%s""" % bad_part
        # when
        result = remove_citation_of_file(text)
        # then
        print(result)
        assert bad_part not in result

    def test_remove_citation_with_dagger(self):
        # given
        bad_part = """【4:6†article6.txt】【16:8†article8.txt】"""
        text = """Законодательство о защите прав потребителей%s и другие нормативные акты""" % bad_part
        # when
        result = remove_citation_of_file(text)
        # then
        print(result)
        assert bad_part not in result
        assert result == """Законодательство о защите прав потребителей и другие нормативные акты"""
