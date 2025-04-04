import requests
import logging
import json
import time
from django.conf import settings
from datetime import datetime, timedelta
try:
    from .selenium_auth import get_auth_token_with_selenium
except ImportError:
    get_auth_token_with_selenium = None

logger = logging.getLogger(__name__)

class ExnessApiClient:
    """Client for interacting with the Exness Affiliates API"""
    
    # Try both API formats
    BASE_URL_V1 = "https://my.exnessaffiliates.com/api"
    BASE_URL_V2 = "https://my.exnessaffiliates.com/api/v2"
    LOGIN_URL = "https://my.exnessaffiliates.com/en/auth/login/"
    
    TOKEN_CACHE = {
        'token': None,
        'expires_at': None,
        'cookies': None
    }
    
    @classmethod
    def get_auth_token(cls):
        """Get an authentication token from the Exness API"""
        
        # Check if we have a valid cached token
        if cls.TOKEN_CACHE['token'] and cls.TOKEN_CACHE['expires_at'] and datetime.now() < cls.TOKEN_CACHE['expires_at']:
            return cls.TOKEN_CACHE['token']
        
        # First, try web-based authentication
        session = requests.Session()
        
        # Browser-like headers to bypass WAF
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://my.exnessaffiliates.com",
            "Referer": "https://my.exnessaffiliates.com/",
            "Content-Type": "application/json"
        }
        
        try:
            # Step 1: Visit the login page to get cookies
            logger.info("Trying web-based authentication...")
            session.get(cls.LOGIN_URL, headers=headers)
            
            # Step 2: Submit login credentials
            login_data = {
                "email": settings.EXNESS_API_EMAIL,
                "password": settings.EXNESS_API_PASSWORD
            }
            
            login_response = session.post(
                f"{cls.BASE_URL_V1}/auth/login/", 
                json=login_data,
                headers=headers
            )
            
            logger.debug(f"Web login response status: {login_response.status_code}")
            
            # Step 3: If successful, get the token
            if login_response.status_code == 200:
                try:
                    data = login_response.json()
                    if data.get('token'):
                        # Cache the token with 24-hour expiry
                        cls.TOKEN_CACHE['token'] = data['token']
                        cls.TOKEN_CACHE['expires_at'] = datetime.now() + timedelta(hours=24)
                        cls.TOKEN_CACHE['cookies'] = session.cookies
                        logger.info("Successfully obtained auth token via web login")
                        return data['token']
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse web login response: {e}")
        
        except Exception as e:
            logger.warning(f"Web-based authentication failed: {e}")
        
        # If web-based auth failed, try direct API auth methods
        auth_methods = [
            # Method 1: V2 API with login field
            {
                "url": f"{cls.BASE_URL_V2}/auth/",
                "payload": {
                    "login": settings.EXNESS_API_EMAIL,
                    "password": settings.EXNESS_API_PASSWORD
                }
            },
            # Method 2: V1 API with email field
            {
                "url": f"{cls.BASE_URL_V1}/auth/",
                "payload": {
                    "email": settings.EXNESS_API_EMAIL,
                    "password": settings.EXNESS_API_PASSWORD
                }
            },
            # Method 3: V2 API with email field
            {
                "url": f"{cls.BASE_URL_V2}/auth/",
                "payload": {
                    "email": settings.EXNESS_API_EMAIL,
                    "password": settings.EXNESS_API_PASSWORD
                }
            },
            # Method 4: Try login endpoint with V2 API
            {
                "url": f"{cls.BASE_URL_V2}/login/",
                "payload": {
                    "email": settings.EXNESS_API_EMAIL,
                    "password": settings.EXNESS_API_PASSWORD
                }
            }
        ]
        
        for method in auth_methods:
            try:
                logger.info(f"Authenticating with Exness API using URL: {method['url']}")
                logger.debug(f"Auth payload: {json.dumps(method['payload']).replace(method['payload']['password'], '********')}")
                
                # Add headers to request
                response = requests.post(method['url'], json=method['payload'], headers=headers)
                logger.debug(f"Auth response status: {response.status_code}")
                logger.debug(f"Auth response content: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('token')
                    if token:
                        # Cache the token with 24-hour expiry
                        cls.TOKEN_CACHE['token'] = token
                        cls.TOKEN_CACHE['expires_at'] = datetime.now() + timedelta(hours=24)
                        logger.info("Successfully obtained auth token")
                        return token
                    else:
                        logger.warning(f"Token not found in response: {data}")
                else:
                    logger.warning(f"Auth method failed: {response.status_code} - {response.text}")
                
                # Add a small delay between attempts
                time.sleep(1)
                
            except requests.RequestException as e:
                logger.warning(f"Error during API authentication method: {str(e)}")
                continue
        
        # If all API methods fail, try Selenium as a last resort
        if get_auth_token_with_selenium:
            try:
                logger.info("All API methods failed. Attempting Selenium authentication as last resort.")
                selenium_result = get_auth_token_with_selenium(
                    settings.EXNESS_API_EMAIL, 
                    settings.EXNESS_API_PASSWORD
                )
                
                if selenium_result and selenium_result.get('token'):
                    # Cache the token with 24-hour expiry
                    cls.TOKEN_CACHE['token'] = selenium_result['token']
                    cls.TOKEN_CACHE['expires_at'] = datetime.now() + timedelta(hours=24)
                    cls.TOKEN_CACHE['cookies'] = selenium_result.get('cookies')
                    logger.info("Successfully obtained auth token via Selenium")
                    return selenium_result['token']
                elif selenium_result and selenium_result.get('cookies'):
                    # We have cookies but no token
                    logger.info("No token obtained but got cookies via Selenium")
                    cls.TOKEN_CACHE['cookies'] = selenium_result['cookies']
            except Exception as e:
                logger.error(f"Selenium authentication failed: {e}")
        
        logger.error("All authentication methods failed")
        return None
    
    @classmethod
    def check_client_registration(cls, client_id=None, email=None):
        """Check if a client is registered under the affiliate account"""
        
        token = cls.get_auth_token()
        if not token:
            return {"error": "Failed to authenticate with the Exness API"}
        
        # Create a session and use stored cookies if available
        session = requests.Session()
        if cls.TOKEN_CACHE.get('cookies'):
            session.cookies.update(cls.TOKEN_CACHE['cookies'])
        
        # Browser-like headers for API requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://my.exnessaffiliates.com",
            "Referer": "https://my.exnessaffiliates.com/en/reports/",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Try both API versions
        api_versions = [cls.BASE_URL_V1, cls.BASE_URL_V2]
        
        for base_url in api_versions:
            # The reports/clients endpoint can be used to check client data
            if client_id:
                url = f"{base_url}/reports/clients/?client_account={client_id}"
            elif email:
                # Assuming the API allows searching by email
                url = f"{base_url}/reports/clients/?email={email}"
            else:
                return {"error": "Either client_id or email must be provided"}
            
            try:
                logger.info(f"Checking client registration using URL: {url}")
                response = session.get(url, headers=headers)
                logger.debug(f"Client check response status: {response.status_code}")
                logger.debug(f"Client check response content: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if the client exists in the response data
                    if data.get('data') and len(data['data']) > 0:
                        # Return the client data
                        return {
                            "status": "success",
                            "is_registered": True,
                            "client_data": data['data'][0]
                        }
                    else:
                        # Client not found
                        return {
                            "status": "success",
                            "is_registered": False,
                            "client_data": None
                        }
                
                # If auth failed, try refreshing the token once
                elif response.status_code == 401 and base_url == api_versions[-1]:  # Only try token refresh on last API version
                    # Clear the cached token
                    cls.TOKEN_CACHE['token'] = None
                    cls.TOKEN_CACHE['expires_at'] = None
                    
                    # Try again with a new token
                    new_token = cls.get_auth_token()
                    if new_token:
                        headers["Authorization"] = f"Bearer {new_token}"
                        retry_response = session.get(url, headers=headers)
                        
                        if retry_response.status_code == 200:
                            retry_data = retry_response.json()
                            is_registered = retry_data.get('data') and len(retry_data['data']) > 0
                            client_data = retry_data['data'][0] if is_registered else None
                            
                            return {
                                "status": "success",
                                "is_registered": is_registered,
                                "client_data": client_data
                            }
                
                # Continue to try the next API version if this one failed
                logger.warning(f"API request failed with {base_url}: {response.status_code}")
                if base_url != api_versions[-1]:  # If not the last API version, try the next one
                    continue
                
                logger.error(f"All API requests failed: {response.status_code} - {response.text}")
                return {"error": f"API request failed with status code: {response.status_code}"}
                
            except requests.RequestException as e:
                logger.error(f"Error checking client registration: {str(e)}")
                if base_url != api_versions[-1]:  # If not the last API version, try the next one
                    continue
                return {"error": f"Error checking client registration: {str(e)}"}
                
    @classmethod
    def check_client_affiliation(cls, email):
        """
        Check if a client with the given email is affiliated with the agent using
        the /api/v1/referral-agents/affiliation/ endpoint.
        
        Args:
            email (str): The email address to check
            
        Returns:
            dict: Response with affiliation status
        """
        token = cls.get_auth_token()
        if not token:
            return {"error": "Failed to authenticate with the Exness API"}
        
        # Create a session and use stored cookies if available
        session = requests.Session()
        if cls.TOKEN_CACHE.get('cookies'):
            session.cookies.update(cls.TOKEN_CACHE['cookies'])
        
        # Browser-like headers for API requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://my.exnessaffiliates.com",
            "Referer": "https://my.exnessaffiliates.com/api/partner/affiliation/",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Prepare the payload with the email
        payload = {
            "email": email
        }
        
        # Use the specific endpoint requested by the user
        url = f"{cls.BASE_URL_V1}/api/partner/affiliation/"
        
        try:
            logger.info(f"Checking client affiliation using URL: {url}")
            response = session.post(url, json=payload, headers=headers)
            logger.debug(f"Affiliation check response status: {response.status_code}")
            logger.debug(f"Affiliation check response content: {response.text}")
            
            # Check for a successful response (HTTP 200)
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"Received valid JSON response: {data}")
                    
                    # Get the is_affiliated value and convert to bool if needed
                    # The API might return a boolean, string, or have a different structure
                    is_affiliated = False
                    
                    # If API explicitly provides is_affiliated field
                    if 'is_affiliated' in data:
                        # Handle different possible formats (boolean or string)
                        if isinstance(data['is_affiliated'], bool):
                            is_affiliated = data['is_affiliated']
                        elif isinstance(data['is_affiliated'], str):
                            is_affiliated = data['is_affiliated'].lower() == 'true'
                    
                    # Alternatively, check if there are accounts or other indicators of affiliation
                    elif 'accounts' in data and data['accounts'] and len(data['accounts']) > 0:
                        is_affiliated = True
                    
                    # Check for link_code as another potential indicator
                    elif 'link_code' in data and data['link_code']:
                        is_affiliated = True
                    
                    return {
                        "status": "success",
                        "is_affiliated": is_affiliated,
                        "link_code": data.get('link_code', ''),
                        "accounts": data.get('accounts', [])
                    }
                except (ValueError, KeyError) as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return {
                        "status": "error",
                        "message": f"Failed to parse API response: {e}",
                        "is_affiliated": False
                    }
            
            # For 404, we can confidently say the client is not affiliated
            elif response.status_code == 404:
                return {
                    "status": "success",
                    "is_affiliated": False,
                    "message": "Client not found or not affiliated"
                }
            
            # If auth failed, try refreshing the token once
            elif response.status_code == 401:
                # Clear the cached token
                cls.TOKEN_CACHE['token'] = None
                cls.TOKEN_CACHE['expires_at'] = None
                
                # Try again with a new token
                new_token = cls.get_auth_token()
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    retry_response = session.post(url, json=payload, headers=headers)
                    
                    if retry_response.status_code == 200:
                        try:
                            retry_data = retry_response.json()
                            # Apply the same logic as above
                            is_affiliated = False
                            
                            if 'is_affiliated' in retry_data:
                                if isinstance(retry_data['is_affiliated'], bool):
                                    is_affiliated = retry_data['is_affiliated']
                                elif isinstance(retry_data['is_affiliated'], str):
                                    is_affiliated = retry_data['is_affiliated'].lower() == 'true'
                            elif 'accounts' in retry_data and retry_data['accounts'] and len(retry_data['accounts']) > 0:
                                is_affiliated = True
                            elif 'link_code' in retry_data and retry_data['link_code']:
                                is_affiliated = True
                                
                            return {
                                "status": "success",
                                "is_affiliated": is_affiliated,
                                "link_code": retry_data.get('link_code', ''),
                                "accounts": retry_data.get('accounts', [])
                            }
                        except (ValueError, KeyError) as e:
                            logger.error(f"Failed to parse JSON response on retry: {e}")
                    
                    # Not affiliated case after token refresh
                    if retry_response.status_code == 404:
                        return {
                            "status": "success",
                            "is_affiliated": False,
                            "message": "Client not found or not affiliated (after token refresh)"
                        }
            
            # For all other status codes, log the error and assume not affiliated
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"API request failed with status code: {response.status_code}",
                "is_affiliated": False
            }
            
        except requests.RequestException as e:
            logger.error(f"Error checking client affiliation: {str(e)}")
            return {
                "status": "error", 
                "message": f"Error checking client affiliation: {str(e)}",
                "is_affiliated": False
            } 