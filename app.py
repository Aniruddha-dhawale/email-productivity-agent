from datetime import datetime, timedelta
import re
import streamlit as st
import pandas as pd
from src.db_manager import (
    fetch_emails, get_email_by_id, update_email_ai_data,
    get_all_emails_for_chat, mark_as_read  
)
from src.prompt_manager import PromptManager
from src.llm_engine import LLMEngine
from setup_data import reset_and_seed_db
from src.db_manager import schedule_with_shadow_summary


# Page Config
st.set_page_config(page_title="AI Email Agent", layout="wide")

st.markdown("""
<style>
    div.stButton > button {
        text-align: left;
        justify-content: flex-start;
    }
    button[data-baseweb="tab"] div p {
        font-size: 20px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize LLM Engine
llm = LLMEngine()


# TOP DASHBOARD SECTION 
col_header, col_dashboard = st.columns([2, 3])

with col_header:
    st.title("Email Productivity Agent")
    st.caption("By Aniruddha Dhawale")

with col_dashboard:
    df_all = fetch_emails()
    if 'is_scheduled' not in df_all.columns: df_all['is_scheduled'] = 0
    if 'calendar_summary' not in df_all.columns: df_all['calendar_summary'] = None
        
    df_actions = df_all[df_all['is_scheduled'] == 1].copy()

    if not df_actions.empty:
        df_actions['is_urgent'] = df_actions['category'].apply(lambda x: 1 if x == 'Urgent' else 0)
        df_actions = df_actions.sort_values(by=['is_urgent', 'received_at'], ascending=[False, False])

        with st.container(border=True):
            st.markdown("##### Approaching Deadlines")

            for i, (index, row) in enumerate(df_actions.head(5).iterrows()):
                raw_text = row['calendar_summary'] if row['calendar_summary'] else row['action_items']
                
                if raw_text:
                    snippet = raw_text.split('\n')[0].replace('* ', '').strip()[:40]
                else:
                    snippet = "Processing..."

                st.markdown(f"**{i+1}. {row['sender']}:** {snippet}...")
    else:

        with st.container(border=True):
            st.markdown("##### No Pending Actions")
            st.caption("Process emails to extract to-do lists.")



# Session State Setup 

if 'page_view' not in st.session_state:
    st.session_state.page_view = 'list'

if 'selected_email_id' not in st.session_state:
    st.session_state.selected_email_id = None


# SIDEBAR: DATA SOURCE
st.sidebar.header("Data Source")
data_source = st.sidebar.selectbox(
    "Select Inbox Type",
    ["Mock Inbox (SQLite)", "Connect Real Email (IMAP)"],
)

if data_source == "Connect Real Email (IMAP)":
    st.sidebar.info("Enter credentials to sync.")
    email_user = st.sidebar.text_input("Email Address")
    email_pass = st.sidebar.text_input("App Password", type="password")
    if st.sidebar.button("Sync Emails"):
        st.sidebar.warning("Live connection disabled for this demo. Please use Mock Inbox.")
       
else:
    st.sidebar.caption("Using local simulation database.")

    if st.sidebar.button("Generate/Reset Mock Inbox"):
        with st.spinner("Generating mock data"):
            reset_and_seed_db()
            st.session_state.selected_email_id = None
            st.session_state.page_view = 'list'
            st.cache_data.clear() 
            st.sidebar.success("Inbox Generated")
            st.rerun() 

st.sidebar.markdown("---")

# Sidebar: The Brain Configuration
st.sidebar.header("Agent Configuration")

with st.sidebar.expander("Edit Prompts", expanded=False):
    st.info("Edit these prompts to change response behaviour.")
    current_cat_prompt = PromptManager.get_categorization_prompt()
    current_act_prompt = PromptManager.get_extraction_prompt()
    current_rep_prompt = PromptManager.get_reply_prompt()
    new_cat_prompt = st.text_area("Categorization Rules", value=current_cat_prompt, height=100)
    new_act_prompt = st.text_area("Action Extraction Rules", value=current_act_prompt, height=100)
    new_rep_prompt = st.text_area("Reply Tone/Persona", value=current_rep_prompt, height=100)

    if st.button("Save Prompts"):
        PromptManager.update_prompts(new_cat_prompt, new_act_prompt, new_rep_prompt)
        st.sidebar.success("Prompts updated")



# Sidebar: Inbox Tools
st.sidebar.markdown("---")
st.sidebar.header("Inbox Tools")
if st.sidebar.button("Auto-Tag New Emails"):
    df_all = fetch_emails()
    df_new = df_all[df_all['category'].isnull() | (df_all['category'] == "")]

    if df_new.empty:
        st.sidebar.success("All emails are already tagged!")

    else:
        progress_bar = st.sidebar.progress(0)
        total = len(df_new)

        for i, (index, row) in enumerate(df_new.iterrows()):
            cat = llm.categorize_only(
                row['body'],
                row['sender'],
                row['subject'],
                new_cat_prompt
            )
            update_email_ai_data(row['id'], cat, row['action_items'], row['draft_reply'])
            progress_bar.progress((i + 1) / total)

        st.sidebar.success(f"Tagged {total} emails!")
        st.rerun()

# Main Interface

tab1, tab2, tab3 = st.tabs(["[Inbox]", "[Chat with Inbox]", "[Calendar]"])

# LIST VIEW 
with tab1:
    if st.session_state.page_view == 'list':
        col_filter, col_content = st.columns([1, 5])

        with col_filter:
            st.subheader("Folders")
        # Dynamic Category Extraction 
            match = re.search(r"\[(.*?)\]", new_cat_prompt)

            if match:
                categories = [c.strip() for c in match.group(1).split(',')]
            else:
            # Fallback defaults
                categories = ["Work", "Personal", "Urgent", "Finance", "Spam"]

            if "filter_inbox" not in st.session_state:
                st.session_state.filter_inbox = True 

            for cat in categories:
                if f"filter_{cat}" not in st.session_state:
                    st.session_state[f"filter_{cat}"] = False

            def on_cat_change():
                st.session_state.filter_inbox = False

            def on_inbox_change():
                if st.session_state.filter_inbox:
                    for c in categories:
                        st.session_state[f"filter_{c}"] = False

            show_all = st.checkbox("Inbox", key="filter_inbox", on_change=on_inbox_change)

            st.markdown("---")
            st.caption("Categories")

            selected_filters = []
            for cat in categories:
                is_checked = st.checkbox(cat, key=f"filter_{cat}", on_change=on_cat_change)
                if is_checked:
                    selected_filters.append(cat)



        with col_content:
            st.subheader("Inbox")

            df_emails = fetch_emails()

            if not show_all:
                if selected_filters:
                    df_emails = df_emails[df_emails['category'].isin(selected_filters)]

                else:
                    df_emails = df_emails.iloc[0:0]

            if not df_emails.empty:
                for index, row in df_emails.iterrows():

                    # READ/UNREAD LOGIC 
                    is_unread = (row['is_read'] == 0)
                    btn_type = "primary" if is_unread else "secondary"
                    category_label = row['category'] if row['category'] else "New"

                    email_time = row['received_at']
                    try:
                        dt_obj = datetime.strptime(email_time, "%Y-%m-%d %H:%M")
                        now = datetime.now()
    
                        if dt_obj.date() == now.date():
                            time_val = dt_obj.strftime("%H:%M")
                        else:
                            time_val = dt_obj.strftime("%b %d")
                    except:
                        time_val = email_time
                    
                    btn_label = f"[{time_val}] | {row['sender']} - {row['subject']} | [{category_label.upper()}] "
                    
                   
                
                    if st.button(btn_label, key=row['id'], use_container_width=True, type=btn_type):
                        mark_as_read(row['id'])
                        st.session_state.selected_email_id = row['id']
                        st.session_state.page_view = 'detail'
                        st.rerun()

            else:
                if not show_all and not selected_filters:
                    st.info("Select 'Inbox' or a Category to view emails.")
                else:
                    st.write("No emails found.")



    # DETAIL VIEW
    elif st.session_state.page_view == 'detail':
        if st.button("<- Back to Inbox"):
            st.session_state.page_view = 'list'
            st.rerun()
           
        if 'selected_email_id' in st.session_state:
            e_id = st.session_state.selected_email_id
            email_data = get_email_by_id(e_id)
           
            if email_data:
                email_sub, c_cal_btn = st.columns([4, 1])
                with email_sub:
                    subject_text = email_data['subject']
                    if email_data['category']:
                        st.markdown(f"### {subject_text} `{email_data['category']}`")
                    else:
                        st.subheader(subject_text)

                is_scheduled = email_data.get('is_scheduled', 0)             
                with c_cal_btn:
                    if not is_scheduled:
                        if st.button("Add to Calendar", use_container_width=True):
                            with st.spinner("Analyzing & Scheduling"):
                                hidden_actions = llm.extract_only(
                                    email_data['body'], 
                                    email_data['sender'], 
                                    email_data['subject'], 
                                    new_act_prompt
                                )
                                schedule_with_shadow_summary(e_id, hidden_actions)
                                
                                st.toast("Added to Calendar (Background Processed)")
                                st.rerun()
                    else:
                        st.success("Event is on Calendar")

                st.markdown(f"###### From: {email_data['sender']} | {email_data['received_at']}")

                st.markdown("###### Body:")

                with st.container(border=True, height=150):
                    st.markdown(email_data['body'])
                
                # action items and draft reply
                has_category = email_data['category'] and email_data['category'].strip() != ""
                has_actions = email_data['action_items'] and email_data['action_items'].strip() != ""
                has_draft = email_data['draft_reply'] and email_data['draft_reply'].strip() != ""

                col_tools, col_display = st.columns([1, 2])
                
                with col_tools:
                    st.caption("Actions")              
                    # EXTRACT ACTIONS
                    if not has_actions:
                        if st.button("Extract Action Items", use_container_width=True):
                            with st.spinner("Extracting tasks"):
                                # Call the specific extract method
                                actions = llm.extract_only(
                                    email_data['body'], 
                                    email_data['sender'], 
                                    email_data['subject'], 
                                    new_act_prompt
                                )
                                # Update DB
                                update_email_ai_data(e_id, email_data['category'], actions, email_data['draft_reply'])
                                st.rerun()
                    else:
                        st.success("Actions Extracted")


                    # DRAFT REPLY 
                    st.caption("Replies")
                    if not has_draft:
                        if st.button("Draft Reply", use_container_width=True):
                            with st.spinner("Drafting response"):
                                # Call the specific draft method
                                reply = llm.draft_only(
                                    email_data['body'], 
                                    email_data['sender'], 
                                    email_data['subject'], 
                                    new_rep_prompt
                                )
                                # Update DB 
                                update_email_ai_data(e_id, email_data['category'], email_data['action_items'], reply)
                                st.rerun()
                    else:
                        st.success("Reply Drafted")

                    # Reset Button
                    if has_actions or has_draft:
                        st.markdown("---")
                        if st.button("Reset Generated Data", use_container_width=True):
                             update_email_ai_data(e_id, email_data['category'], None, None)
                             st.rerun()

                with col_display:
                    # Display Actions
                    if has_actions:
                        st.warning(f"**Action Items:**\n{email_data['action_items']}")
                    
                    # Display Draft with Refinement Loop
                    if has_draft:
                        st.write("### Draft Reply")

                        draft_box = st.text_area("Edit Draft", value=email_data['draft_reply'], height=250)
                        
                        st.write("Refinement")
                        c_ref_input, c_ref_btn = st.columns([3, 1])
                        
                        with c_ref_input:
                            refine_feedback = st.text_input(
                                "Feedback", 
                                placeholder="Ex: Make it shorter, add a meeting link...", 
                                label_visibility="collapsed"
                            )
                            
                        with c_ref_btn:
                            if st.button("Refine", use_container_width=True):
                                if refine_feedback:
                                    with st.spinner("Rewriting..."):
                                        new_draft = llm.refine_reply(email_data['draft_reply'], refine_feedback)
                                        update_email_ai_data(e_id, email_data['category'], email_data['action_items'], new_draft)
                                        st.rerun()

                        st.markdown("---")
                        col_send, col_dummy = st.columns([1, 3])
                        with col_send:
                            if st.button("Send Email"):
                                st.success(f"Email sent to {email_data['sender']} (Simulated)")



with tab2:
    st.subheader("Ask questions about your emails")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Do I have any deadlines today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Scanning inbox"):
                inbox_context = get_all_emails_for_chat()
                response = llm.chat_with_inbox(prompt, inbox_context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})



# CALENDAR TAB 
with tab3:
    st.subheader("Weekly Task Planner")

    # find day of week from text
    def get_target_date(text):
        if not text: return None
        text = text.lower()
        today = datetime.now()
        
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        found_day = None
        for day, num in days.items():
            if day in text:
                found_day = num
                break
        
        if found_day is not None:
            current_weekday = today.weekday()
            days_ahead = found_day - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            if days_ahead == 0 and "today" in text: 
                days_ahead = 0
            return today + timedelta(days=days_ahead)
        
        if "tomorrow" in text:
            return today + timedelta(days=1)
        if "today" in text:
            return today
            
        return None

    df_all = fetch_emails()
    if 'is_scheduled' not in df_all.columns: df_all['is_scheduled'] = 0
    if 'calendar_summary' not in df_all.columns: df_all['calendar_summary'] = None
        
    df_tasks = df_all[df_all['is_scheduled'] == 1].copy()
    
    cols = st.columns(7)
    today = datetime.now()
    
    for i in range(7):
        current_date = today + timedelta(days=i)
        date_str = current_date.strftime("%a %d") 
        
        with cols[i]:
            st.markdown(f"##### {date_str}")
            st.markdown("---")
            
            has_tasks = False
            
            if not df_tasks.empty:
                for index, row in df_tasks.iterrows():
                    # if action item text matches this day
                    text_source = row['calendar_summary'] if row['calendar_summary'] else row['action_items']
                    target = get_target_date(text_source)
                    
                    is_match = False
                    if target:
                        if target.date() == current_date.date():
                            is_match = True
                    elif i == 0: 
                        is_match = True
                        
                    if is_match:
                        has_tasks = True
                        priority_color = "red" if row['category'] == "Urgent" else "gray"
                        
                        with st.container(border=True):
                            st.markdown(f"**:{priority_color}[{row['sender']}]**")
                            st.caption(f"{row['subject'][:20]}...")
                            raw_text = row['calendar_summary'] if row.get('calendar_summary') else row['action_items']
                            
                            if raw_text:
                                clean_task = raw_text.split('\n')[0].replace('* ', '').strip()
                                st.write(f"{clean_task[:40]}...")
                            else:
                                st.caption("No details generated.")
            
            if not has_tasks:
                st.caption("No tasks")