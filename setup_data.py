import os
import sys
from src.db_manager import init_db, get_connection, save_prompt

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

def reset_and_seed_db():
    print("Initializing Database")
    init_db()

    # Clear existing data 
    conn = get_connection()
    conn.execute("DELETE FROM emails")
    conn.commit()
    
    # Mock Emails
    mock_emails = [
    ("recruiter@techcorp.com", "Interview Invitation: Senior ML Engineer", "Hi, we were impressed by your resume. Are you available for a generic system design round this Tuesday at 10 AM? Please confirm by EOD.", "2025-11-23 09:00"),
    ("newsletter@dailyml.com", "The State of LLMs in 2025", "Here are the top 5 papers you need to read this week regarding attention mechanisms...", "2025-11-17 08:30"),
    ("boss@startup.io", "URGENT: Server Down", "The production server is throwing 500 errors. I need you to look at the logs immediately. The clients are waiting.", "2025-11-23 13:15"),
    ("mom@gmail.com", "Dinner plans?", "Are you coming over this weekend? Dad is making lasagna.", "2025-11-16 18:00"),
    ("billing@aws.com", "Invoice Available", "Your AWS bill for October is ready. Total amount: $45.20. Payment is due by the 25th.", "2025-11-02 12:00"),
    ("colleague@startup.io", "Code Review Request", "Hey, I pushed the new feature branch. Can you review the PR by tomorrow afternoon?", "2025-11-23 18:00"),
    ("spam@lottery.com", "YOU WON $1,000,000!", "Click here to claim your prize now!!!", "2025-11-15 03:00"),
    ("hr@startup.io", "Open Enrollment: Health Insurance", "Hi Team, just a reminder that open enrollment for health benefits closes this Friday. Please log in to the portal to make your selections.", "2025-11-19 09:00"),
    ("notifications@jira.com", "Ticket Assigned: FIX-402", "You have been assigned a new ticket: 'Login button misalignment on mobile'. Priority: Low.", "2025-11-23 10:30"),
    ("marketing@tool.io", "Black Friday Deal: 50% Off Pro", "Don't miss out on our biggest sale of the year. Upgrade your workspace today.", "2025-11-19 11:00"),
    ("client@bigclient.com", "Feedback on Q4 Report", "Thanks for the report. We have a few questions about slide 14. Can we hop on a quick call tomorrow?", "2025-11-19 13:15"),
    ("noreply@bank.com", "Transaction Alert: Large Purchase", "A transaction of $1,200 was made on your card ending in 4421. If this wasn't you, reply immediately.", "2025-11-22 14:00"),
    ("gym@fitness.com", "Membership Renewal Failed", "We tried to process your monthly fee but the payment failed. Please update your card details.", "2025-11-19 15:45"),
    ("friend@gmail.com", "Movie night?", "Hey! Are you free to catch the new Dune movie this Saturday? Let me know so I can book tickets.", "2025-11-23 16:30"),
    ("newsletter@pythonweekly.com", "Python 3.14 Released", "The latest version of Python is out. Check out the new JIT compiler features that speed up loops by 20%.", "2025-11-20 08:00"),
    ("recruiter@competitor.com", "Opportunity at AI Labs", "Hello, I saw your LinkedIn profile and think you'd be a great fit for our Lead Engineer role. Open to a chat?", "2025-11-20 09:30"),
    ("admin@rental.com", "Lease Renewal Notice", "Your apartment lease is up for renewal in 60 days. Please let us know if you intend to stay.", "2025-11-20 10:00"),
    ("security@github.com", "New Login Detected", "We detected a login to your GitHub account from a new device in London, UK. Was this you?", "2025-11-22 11:20"),
    ("billing@netflix.com", "Your payment was successful", "Thanks for sticking with us! Your monthly subscription of $15.99 has been paid.", "2025-11-20 12:00"),
    ("boss@startup.io", "Quick Sync", "Can you stay 15 mins late today? I want to discuss the roadmap for Q1.", "2025-11-24 08:00"),
    ("support@uber.com", "Your ride receipt", "Thanks for riding with Uber. Total: $24.50. Rate your driver!", "2025-11-20 18:45"),
]

    print(f"Inserting {len(mock_emails)} mock emails...")
    c = conn.cursor()
    for email in mock_emails:
        c.execute("INSERT INTO emails (sender, subject, body, received_at) VALUES (?, ?, ?, ?)", email)
    conn.commit()
    conn.close()

    # Set Default Prompts
    print("Injecting Default Prompts")
    default_categorize = """
    You are an email organizer. 
    Classify the following email into one of these categories: [Work, Personal, Newsletter, Finance, Spam, Urgent].
    Return ONLY the category name.
    """

    default_action = """
    Identify any specific tasks, deadlines, or requests in the email.
    Return them as a bulleted list. If none, write 'No action items'.
    """

    default_reply = """
    Draft a professional, concise reply to this email. 
    If it is work-related, be formal. If personal, be casual.
    """

    save_prompt("categorize", default_categorize)
    save_prompt("extract", default_action)
    save_prompt("reply", default_reply)

    print("Database seeded successfully. File location: data/mock_inbox.db")

if __name__ == "__main__":
    reset_and_seed_db()