# utils/flash_helper.py - Consistent Flash Message Helper
from flask import flash, redirect, url_for, render_template

class FlashHelper:
    """Helper class for consistent flash messaging and error handling"""
    
    @staticmethod
    def flash_and_redirect(message, category, endpoint, **kwargs):
        """Flash a message and redirect to an endpoint"""
        flash(message, category)
        return redirect(url_for(endpoint, **kwargs))
    
    @staticmethod
    def flash_and_render(message, category, template, **kwargs):
        """Flash a message and render a template"""
        flash(message, category)
        return render_template(template, **kwargs)
    
    @staticmethod
    def error_and_redirect(message, endpoint, **kwargs):
        """Flash an error message and redirect"""
        return FlashHelper.flash_and_redirect(message, "danger", endpoint, **kwargs)
    
    @staticmethod
    def success_and_redirect(message, endpoint, **kwargs):
        """Flash a success message and redirect"""
        return FlashHelper.flash_and_redirect(message, "success", endpoint, **kwargs)
    
    @staticmethod
    def error_and_render(message, template, **kwargs):
        """Flash an error message and render template"""
        return FlashHelper.flash_and_render(message, "danger", template, **kwargs)
    
    @staticmethod
    def info_and_redirect(message, endpoint, **kwargs):
        """Flash an info message and redirect"""
        return FlashHelper.flash_and_redirect(message, "info", endpoint, **kwargs)
