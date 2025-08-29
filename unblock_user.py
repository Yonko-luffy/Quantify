# unblock_user.py - Utility to unblock rate limited users for testing
import sys
from app import app
from models import db, RateLimit

def unblock_user(identifier=None):
    """Clear rate limits for a specific user or all users"""
    with app.app_context():
        if identifier:
            # Clear specific user/IP
            deleted_username = RateLimit.query.filter_by(identifier=identifier, identifier_type='username').delete()
            deleted_ip = RateLimit.query.filter_by(identifier=identifier, identifier_type='ip').delete()
            db.session.commit()
            
            print(f"✅ Cleared rate limits for '{identifier}':")
            print(f"   - Username records: {deleted_username}")
            print(f"   - IP records: {deleted_ip}")
            
        else:
            # Clear all rate limits
            total_deleted = RateLimit.query.delete()
            db.session.commit()
            
            print(f"✅ Cleared ALL rate limits: {total_deleted} records deleted")
            
        print("🎉 You are now unblocked and can login again!")

def show_current_blocks():
    """Show all current rate limit blocks"""
    with app.app_context():
        blocked_records = RateLimit.query.filter(RateLimit.blocked_until.isnot(None)).all()
        
        if not blocked_records:
            print("✅ No users are currently blocked")
            return
            
        print("🔒 Currently blocked users/IPs:")
        for record in blocked_records:
            time_left = None
            if record.blocked_until:
                from datetime import datetime
                time_left = record.blocked_until - datetime.utcnow()
                minutes_left = int(time_left.total_seconds() / 60) + 1
            
            print(f"   - {record.identifier_type}: {record.identifier}")
            print(f"     Endpoint: {record.endpoint}")
            print(f"     Attempts: {record.attempt_count}")
            print(f"     Blocked until: {record.blocked_until}")
            if time_left and time_left.total_seconds() > 0:
                print(f"     Time remaining: ~{minutes_left} minutes")
            print()

if __name__ == "__main__":
    print("=== Rate Limit Management Tool ===\n")
    
    # Show current status
    show_current_blocks()
    
    # If arguments provided, unblock specific user
    if len(sys.argv) > 1:
        identifier = sys.argv[1]
        unblock_user(identifier)
    else:
        # Ask what to do
        print("Options:")
        print("1. Clear ALL rate limits")
        print("2. Clear specific user/IP")
        print("3. Show status only")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            confirm = input("Are you sure you want to clear ALL rate limits? (y/N): ").strip().lower()
            if confirm == 'y':
                unblock_user()
            else:
                print("❌ Operation cancelled")
        elif choice == "2":
            identifier = input("Enter username or IP to unblock: ").strip()
            if identifier:
                unblock_user(identifier)
            else:
                print("❌ No identifier provided")
        elif choice == "3":
            print("✅ Status shown above")
        else:
            print("❌ Invalid choice")
