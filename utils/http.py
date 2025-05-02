import kronos, configuration, time, requests
from typing import Dict, Any, Optional


class HTTPy:
    """
    HTTPy

    A flexible HTTP client with built-in retry, timeout, and rate limiting capabilities
    Buil-in usage of Kronos.py
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[kronos.Logger] = None, rate_limiter: Optional[kronos.RateLimiter] = None):
        """
        Initialize the HTTP client with the provided configuration

        Args:
            config: Configuration dictionary following https://github.com/devKaos117/Utils.py/blob/main/documentation/schema/http.schema.json
            logger: kronos.Logger instance to use
        """
        default_config = {
            "max-retries": 3,
            "retry_status_codes": [403, 429, 500, 502, 503, 504],
            "success_status_codes": [200, 201, 202, 203, 204, 205, 206, 207, 208],
            "timeout": 10,
            "headers": {}
        }

        self._config = configuration.import_config(config, default_config)
        self._logger = logger
        self._rate_limiter = rate_limiter
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create and configure a requests Session with retry capabilities

        Returns:
            requests.Session: Configured session object
        """
        session = requests.Session()

        # Set default headers
        session.headers = self._config['headers']
        self._logger.info("Session initialized")

        return session

    def _execute_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Execute an HTTP request with the given method and parameters

        Args:
            method: HTTP method
            url: URL to send the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server or None
        """
        # Apply default timeout if not specified in kwargs
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self._config['timeout']

        # Merge default headers with any provided in kwargs
        if 'headers' in kwargs:
            merged_headers = configuration.deep_merge(kwargs['headers'], self._config['headers'].copy())
            kwargs['headers'] = merged_headers

        # Make requests
        response = None
        retries = 0

        while retries < self._config["max-retries"]:
            # Apply rate limiting if enabled
            if self._rate_limiter:
                self._rate_limiter.acquire()
            try:
                response = self._session.request(method, url, **kwargs)
                # Handle different status codes
                if response.status_code in self._config["success_status_codes"]:
                    break
                else:
                    self._handle_response_status(response)
            except requests.RequestException as e:
                self._logger.exception(f"Network error making request: {str(e)}")
                self._logger.log_http_response(response)
            except Exception as e:
                self._logger.exception(f"Error making request: {str(e)}")
                self._logger.log_http_response(response)
                time.sleep(1)

            retries += 1

        if response is None or response.status_code not in self._config["success_status_codes"]:
            self._logger.error(f"HTTP request failed after {retries - 1} retries")
        else:
            self._logger.log_http_response(response)

        return response

    def _handle_response_status(self, response: requests.Response) -> None:
        """
        Handle the response based on its status code

        Args:
            response (requests.Response): The response to handle
        """
        if 300 <= response.status_code < 400:
            self._logger.log_http_response(response)
        elif 400 <= response.status_code < 500:
            self._logger.error(f"Client error: {response.status_code} - {response.text}")

            if response.status_code == 401:
                self._logger.error("Authentication error: Check credentials")
            elif response.status_code == 403:
                self._logger.error("Forbidden: Access denied")
            elif response.status_code == 404:
                self._logger.error("Not found: Resource does not exist")
            elif response.status_code == 429:
                self._logger.error("Rate limited: Too many requests")
                time.sleep(15)
        elif 500 <= response.status_code < 600:
            self._logger.error(f"Server error ({response.status_code}): {response.text}")
            time.sleep(1)

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        Send a GET request to the specified URL

        Args:
            url : URL to send the request to
            params : Query parameters for the request
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server
        """
        return self._execute_request("GET", url, params=params, **kwargs)

    def post(self, url: str, data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,**kwargs) -> requests.Response:
        """
        Send a POST request to the specified URL

        Args:
            url: URL to send the request to
            data: Data to send in the request body
            json: JSON data to send in the request body
            **kwargs: Additional arguments to pass to the request

        Returns:
            requests.Response: Response from the server
        """
        return self._execute_request("POST", url, data=data, json=json, **kwargs)

    def close(self) -> None:
        """Close the session and release resources."""
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit that ensures session closure."""
        self.close()