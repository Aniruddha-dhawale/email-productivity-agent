import os
import time
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

class LLMEngine:
    # Initializes the LLMEngine
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')


    # helper method to execute LLM API calls
    def _call_llm_with_retry(self, prompt, retries=3):
        base_delay = 2
        
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str:
                    if attempt < retries - 1:
                        sleep_time = base_delay * (2 ** attempt) 
                        time.sleep(sleep_time)
                        continue
                return None
        return None
    

    # to categorize an email
    def categorize_only(self, email_body, sender, subject, cat_prompt):
        prompt = f"""
        {cat_prompt}
        
        Email Data:
        From: {sender}
        Subject: {subject}
        Body: {email_body[:1000]} 
        
        Output: Return ONLY the category name. No formatting.
        """
        result = self._call_llm_with_retry(prompt)
        return result if result else "Uncategorised"
    

    # consolidated API call
    def generate_all_insights(self, email_body, sender, subject, prompts):
        combined_prompt = f"""
        You are an intelligent email assistant. Process this email and return a JSON object.
        
        1. CATEGORIZATION RULE: {prompts['categorize']}
        2. EXTRACTION RULE: {prompts['extract']}
        3. DRAFT RULE: {prompts['reply']}
        
        EMAIL CONTEXT:
        From: {sender}
        Subject: {subject}
        Body: {email_body}
        
        OUTPUT FORMAT:
        You must return valid JSON with these exact keys:
        {{
            "category": "Category Name",
            "action_items": "Bulleted list of items",
            "draft_reply": "The email draft"
        }}
        """
        
        raw_response = self._call_llm_with_retry(combined_prompt)
        
        if not raw_response:
            return "Error", "API Error", "Could not process."

        try:
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            return data.get("category", "Uncategorized"), data.get("action_items", "None"), data.get("draft_reply", "")
        except json.JSONDecodeError:
            return "Parsing Error", raw_response, "Error parsing AI response."
        
    # agent logic
    def chat_with_inbox(self, user_query, context):
        prompt = f"""
        System: You are a helpful assistant having access to an email inbox summary.
        Context: {context}
        User Question: {user_query}
        Answer:
        """
        return self._call_llm_with_retry(prompt) or "I'm having trouble connecting right now."
    
    # Extracts action items specifically
    def extract_only(self, email_body, sender, subject, act_prompt):
        prompt = f"{act_prompt}\n\n---\n\nEmail Data:\nFrom: {sender}\nSubject: {subject}\nBody: {email_body}"
        return self._call_llm_with_retry(prompt)

    # only draft
    def draft_only(self, email_body, sender, subject, rep_prompt):
        prompt = f"{rep_prompt}\n\n---\n\nEmail Data:\nFrom: {sender}\nSubject: {subject}\nBody: {email_body}"
        return self._call_llm_with_retry(prompt)
    
    # refine logic
    def refine_reply(self, current_draft, feedback):
        prompt = f"""
        ORIGINAL DRAFT:
        {current_draft}
        
        USER FEEDBACK:
        {feedback}
        
        TASK:
        Rewrite the draft to satisfy the feedback. Keep the same tone unless asked to change.
        Return ONLY the new draft text.
        """
        return self._call_llm_with_retry(prompt)
    
    