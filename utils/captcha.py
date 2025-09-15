# utils/captcha.py - CAPTCHA Validation Utility
import requests
from flask import current_app, request
import json

class CaptchaValidator:
    """CAPTCHA validation utility for reCAPTCHA integration"""
    
    @staticmethod
    def verify_recaptcha(captcha_response):
        """
        Verify reCAPTCHA response with Google's API
        
        Args:
            captcha_response: The response token from reCAPTCHA widget
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not captcha_response:
            return False, "Please complete the CAPTCHA verification"
        
        # Check if reCAPTCHA is configured
        secret_key = current_app.config.get('RECAPTCHA_PRIVATE_KEY')
        if not secret_key:
            return True, None  # Allow through if not configured (for development)
        
        # reCAPTCHA verification endpoint
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        
        # Prepare verification data
        verify_data = {
            'secret': secret_key,
            'response': captcha_response,
            'remoteip': request.remote_addr
        }
        
        try:
            # Send verification request to Google
            response = requests.post(verify_url, data=verify_data, timeout=10)
            result = response.json()
            
            if result.get('success'):
                return True, None
            else:
                error_codes = result.get('error-codes', [])
                
                # Handle specific error codes
                if 'timeout-or-duplicate' in error_codes:
                    return False, "CAPTCHA has expired. Please try again."
                elif 'invalid-input-response' in error_codes:
                    return False, "Invalid CAPTCHA response. Please try again."
                elif 'missing-input-response' in error_codes:
                    return False, "Please complete the CAPTCHA verification."
                elif 'invalid-input-secret' in error_codes:
                    return False, "CAPTCHA configuration error. Please contact support."
                elif 'missing-input-secret' in error_codes:
                    return False, "CAPTCHA configuration error. Please contact support."
                else:
                    return False, f"CAPTCHA verification failed: {', '.join(error_codes)}"
                    
        except requests.exceptions.Timeout:
            return False, "CAPTCHA verification timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return False, "CAPTCHA verification service unavailable. Please try again."
        except Exception as e:
            return False, "CAPTCHA verification failed. Please try again."
    
    @staticmethod
    def is_captcha_required(endpoint=None):
        """
        Determine if CAPTCHA is required for specific endpoints
        Can be customized based on your security requirements
        
        Args:
            endpoint: The endpoint name to check
            
        Returns:
            bool: True if CAPTCHA is required, False otherwise
        """
        # Define endpoints that require CAPTCHA verification
        captcha_required_endpoints = [
            'auth.login',      # Protect login from brute force
            'auth.signup',     # Prevent automated registrations
            # 'quiz.submit_answer'  # Uncomment to protect quiz submissions
        ]
        
        if endpoint:
            return endpoint in captcha_required_endpoints
        
        # Default to requiring CAPTCHA if no specific endpoint provided
        return True
    
    @staticmethod
    def is_captcha_enabled():
        """
        Check if CAPTCHA is properly configured and enabled
        
        Returns:
            bool: True if CAPTCHA is enabled and configured
        """
        # First check if CAPTCHA is explicitly enabled
        captcha_enabled = current_app.config.get('RECAPTCHA_ENABLED', False)
        if not captcha_enabled:
            return False
            
        # Then check if keys are configured
        public_key = current_app.config.get('RECAPTCHA_PUBLIC_KEY')
        private_key = current_app.config.get('RECAPTCHA_PRIVATE_KEY')
        
        return bool(public_key and private_key)
