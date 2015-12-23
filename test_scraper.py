
def test_auth():
    """Very quickly make sure we can get something back that isn't an error.
    """
    from scraper import test_facebook_page_data
    print(test_facebook_page_data("nytimes"))
