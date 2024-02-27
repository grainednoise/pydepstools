import requests


class Client:
    _pypi_url: str

    def __init__(self, pypi_url: str = "https://pypi.org/pypi"):
        self._pypi_url = pypi_url

    @property
    def pypi_url(self):
        return self._pypi_url

    def package_info(self, package_name: str) -> dict:
        url = f"{self._pypi_url}/{package_name}/json"
        resp = requests.get(url)
        assert resp.status_code == 200
        return resp.json()
