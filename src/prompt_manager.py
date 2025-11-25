from src.db_manager import get_prompt, save_prompt


# Manage the retrieval and updates of system prompts
class PromptManager:
    @staticmethod
    def get_categorization_prompt():
        default = """
        You are an email organizer. 
        Classify the following email into one of these categories: [Work, Personal, Newsletter, Finance, Spam, Urgent].
        Return ONLY the category name.
        """
        return get_prompt("categorize", default)

    @staticmethod
    def get_extraction_prompt():
        default = """
        Identify any specific tasks, deadlines, or requests in the email.
        Return them as a bulleted list. If none, write 'No action items'.
        """
        return get_prompt("extract", default)

    @staticmethod
    def get_reply_prompt():
        default = """
        Draft a professional, concise reply to this email. 
        If it is work-related, be formal. If personal, be casual.
        """
        return get_prompt("reply", default)

    @staticmethod
    def update_prompts(cat_prompt, ext_prompt, rep_prompt):
        save_prompt("categorize", cat_prompt)
        save_prompt("extract", ext_prompt)
        save_prompt("reply", rep_prompt)
        return True