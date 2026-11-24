from backend.services.normalization import normalize_name, normalize_domain
def test_normalize_name(): assert normalize_name("ABC Engg. College") == "abcenggcollege"
def test_normalize_domain(): assert normalize_domain("https://www.example.com/about") == "example.com"
