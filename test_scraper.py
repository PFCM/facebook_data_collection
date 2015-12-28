
def auth_test():
    """Very quickly make sure we can get something back that isn't an error.
    """
    from scraper import ping_fb_page
    print('testing auth is present and functioning')
    print(ping_fb_page("nytimes"))
