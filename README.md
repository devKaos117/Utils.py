# Utils.py ![v0](https://img.shields.io/badge/version-0-informational)
<a href="https://www.github.com/devKaos117" target="_blank">![Static Badge](https://img.shields.io/badge/License-%23FFFFFF?style=flat&label=MIT&labelColor=%23000000&color=%23333333&link=https%3A%2F%2Fwww.github.com%2FdevKaos117)</a>
## Index

## About <a name = "about"></a>

### Summary <a name = "about-summary"></a>
This repository contains a variety of utility functions for common programming tasks, alongside specialized modules designed for specific use cases

### Tools <a name = "about-features"></a>

#### import_libs.py
A tool for importing packages locally without installation
```python
from .utils.import_libs import import_libs

import_libs(libs_path="libs", verbose=True)
```

#### configuration.py
A tool for importing configurations with default values
```python
from .utils import configuration

class LoremIpsum:
    
    _DEFAULT_CONFIGURATIONS = {
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US, en",
            "Referer": "https://www.google.com/",
            "DNT": "1"
        },
        "max-retries": 3,
        "timeout": 10
    }

    def __init__(self, config: Dict[str, Any] = {}):
        self._config = configuration.import_config(config, _DEFAULT_CONFIGURATIONS)

    def dolor_sit_amet(self)
        print(f"Sending HTTP request with a timeout limit of {self._config["timeout"]}")
        # ...
```

#### http.py
A http client for requests
```python
import kronos
from .utils.http import HTTPy

config = {
    "max_retries": 3,
    "retry_backoff_factor": 0.5,
    "retry_status_codes": [429, 500, 502, 503, 504],
    "timeout": 10,
    "headers": {
        "User-Agent": "HTTPy/1.0",
        "Accept": "application/json"
    }
}

logger = kronos.Logger(level="debug", log_directory="log")
rate_limiter = kronos.RateLimiter(limit=10, time_period=5, multiprocessing_mode=False, logger=logger)

client = HTTPy(config, logger, rate_limiter)

try:
        # Example GET request
        logger.info("Making GET request to example API")
        response = client.get("https://api.example.com/data")
        logger.info(f"GET request completed with status: {response.status_code}")

        # Example POST request
        post_data = {"key": "value"}
        logger.info(f"Making POST request to example API with data: {post_data}")
        response = client.post("https://api.example.com/create", json=post_data)
        logger.info(f"POST request completed with status: {response.status_code}")

    except Exception as e:
        # Log any exceptions
        logger.exception(e)

    finally:
        # Ensure the client is closed properly
        client.close()
        logger.info("HTTP client closed")
```

#### version.py