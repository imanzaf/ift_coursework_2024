class TestSearchResultValidator:

    def test_validated_results(self, validator_with_results, multiple_search_results):
        # test that only first result returned
        assert validator_with_results.validated_results[0] == multiple_search_results[0]
        assert len(validator_with_results.validated_results) == 2
