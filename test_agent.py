import sys
from src.llm_engine import LLMEngine
from src.db_manager import fetch_emails, get_all_emails_for_chat
from src.prompt_manager import PromptManager

def test_connection():
    # Checks LLM API connectivity
    print("\n1. Testing LLM Connection")
    llm = LLMEngine()
    response = llm._call_llm("Reply with only the word 'Pong'", "Ping")
    print(f"Sent: Ping\nReceived: {response}")
    if "Pong" in response:
        print("Connection Successful")
    else:
        print("Connection Failed. Check API Key.")

def test_extraction():
    # Tests the Categorize, Extract, and Draft pipeline
    print("\n 2. Testing Categorization & Extraction")
    llm = LLMEngine()
    
    # Sample email data
    sample_body = "Please submit the expense report by Friday 5 PM. It is urgent."
    sample_sender = "Boss"
    sample_subject = "Expenses"
    
    print(f"Simulating Email: '{sample_body}'")
    
    # Load prompts
    prompts = {
        'categorize': PromptManager.get_categorization_prompt(),
        'extract': PromptManager.get_extraction_prompt(),
        'reply': PromptManager.get_reply_prompt()
    }
    
    # Process email
    cat, act, rep = llm.process_email(sample_body, sample_sender, sample_subject, prompts)
    
    print(f"\n[Category]: {cat}")
    print(f"[Actions]:\n{act}")
    print(f"[Draft]:\n{rep}")

def test_chat_rag():
    # Tests RAG logic for chat
    print("\n 3. Testing Chat (RAG) Logic")
    llm = LLMEngine()
    
    try:
        context = get_all_emails_for_chat()
        if len(context) < 20:
            print("DB seems empty. Run setup_data.py first.")
            return
            
        query = "Do I have any urgent work?"
        print(f"Context Length: {len(context)} chars")
        print(f"Query: {query}")
        
        response = llm.chat_with_inbox(query, context)
        print(f"\n[Agent Response]: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Main CLI loop
    while True:
        print("\n=== Agent Test CLI ===")
        print("1. Test API Connection")
        print("2. Test Email Processing")
        print("3. Test Chat Logic")
        print("4. Exit")
        choice = input("Select option: ")
        
        if choice == '1': test_connection()
        elif choice == '2': test_extraction()
        elif choice == '3': test_chat_rag()
        elif choice == '4': sys.exit()
        else: print("Invalid choice")

if __name__ == "__main__":
    main()