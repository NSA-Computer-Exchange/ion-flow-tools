import os
import requests
from dotenv import load_dotenv
from security.iontoken import get_token

load_dotenv()


def get_base_url() -> str:
    """
    Build the tenant-specific ION API base URL from .env.

    Uses:
      ION_API_URL
      ION_TENANT

    Example result:
      https://mingle-ionapi.inforcloudsuite.com/NSACOM_DEM
    """
    ion_api_url = os.getenv("ION_API_URL", "").rstrip("/")
    tenant = os.getenv("ION_TENANT", "").strip()

    if not ion_api_url:
        raise ValueError("Missing ION_API_URL in .env")

    if not tenant:
        raise ValueError("Missing ION_TENANT in .env")

    return f"{ion_api_url}/{tenant}"


def export_dataflow(flow_name):
    token = get_token()

    url = f"{os.getenv('ION_API_URL', '').rstrip('/')}/iondesk/dataflows/{flow_name}/export"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml",
        "X-Infor-TenantId": os.getenv('ION_TENANT', '').strip()
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise Exception(f"Failed to export dataflow: {r.text}")

    return r.text


class IONClient:
    def __init__(self):
        self.base_url = get_base_url()
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _auth_headers(self) -> dict:
        token = get_token()
        return {
            "Authorization": f"Bearer {token}"
        }

    def _build_url(self, endpoint: str) -> str:
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return f"{self.base_url}{endpoint}"

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._auth_headers()
        resp = self.session.get(url, headers=headers, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp

    def post(self, endpoint: str, json_body=None, data=None, **kwargs) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._auth_headers()
        resp = self.session.post(
            url,
            headers=headers,
            json=json_body,
            data=data,
            timeout=60,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    def put(self, endpoint: str, json_body=None, data=None, **kwargs) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._auth_headers()
        resp = self.session.put(
            url,
            headers=headers,
            json=json_body,
            data=data,
            timeout=60,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._auth_headers()
        resp = self.session.delete(url, headers=headers, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp

    def get_json(self, endpoint: str, **kwargs):
        return self.get(endpoint, **kwargs).json()
    
    def get_raw(self, endpoint):

        token = get_token()

        url = f"{os.getenv('ION_TENANT_URL').rstrip('/')}{endpoint}";print(url)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "Application/json"
            #"Accept": "*/*",
            #"X-Infor-TenantId": os.getenv("ION_TENANT")
        }

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            raise Exception(f"{endpoint} failed: {r.text}")

        return r.text

        
