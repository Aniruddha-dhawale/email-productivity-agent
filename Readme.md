# AI-Powered Email Productivity Agent

A prompt-driven, full-stack intelligent email assistant designed to categorize, manage, and automate inbox workflows using Generative AI.

**WEBSITE URL:** https://smart-email-agent.streamlit.app/
**DEMO VIDEO:** https://drive.google.com/file/d/1QjMmb7gs7oK18SxnHyOrZkLZjwTrXOGA/view?usp=sharing
---

## Overview

The **AI Email Productivity Agent** helps solve email overload by transforming a static inbox into an intelligent workspace.  
Unlike standard clients, the system uses a configurable **Brain** (system prompts) to:

- Analyze incoming messages  
- Extract actionable tasks  
- Draft context-aware replies  
- Organize your inbox dynamically  

It includes a **Stealth Calendar System**, a **RAG-powered Inbox Chat**, and a **Latency-Optimized Backend** capable of performing complex multi-step reasoning in a **single API call**.

---

## Key Features

### 1. Prompt-Driven Architecture
Fully customizable behavior through user-defined prompts:

- **Categorization Rules:** e.g., `High Priority`, `News`, `Finance`
- **Action Extraction Logic:** define what counts as a “task”
- **Persona / Tone:** Professional, Gen Z, Humorous, Direct, etc.

---

### 2. Intelligent Batch Processing
- **Auto-Tagging:** Lightweight model to categorize unread emails in bulk  
- **Dynamic Filters:** Sidebar categories adapt automatically to user-defined rules

---

### 3. Optimized Single-Shot Inference
- **Consolidated Backend:** Categorization + extraction + drafting → **1 structured JSON call**  
- **Performance:** ~65% latency reduction & lower Gemini API quota consumption

---

### 4. Stealth Calendar Integration
- **Silent AI Extraction:** “Add to Calendar” processes date/time deadlines automatically  
- **Shadow Storage:** Tasks stored in hidden `calendar_summary` column  
- Avoids overwriting user-created `action_items` while powering dashboards

---

### 5. Inbox Chat (RAG)
Ask questions like:

- “Do I have unpaid invoices?”  
- “What emails did Sarah send yesterday?”

Uses Retrieval-Augmented Generation over your local SQLite inbox data.

---

## Technical Architecture

### 1. Frontend Layer (`app.py`)
- **Framework:** Streamlit  
- **State Management:** `st.session_state`  
- **UI Components:**  
  - Sidebar (config + batch tools)  
  - Split inbox/detail view  
  - Dashboard with deadlines

---

### 2. Intelligence Layer (`src/llm_engine.py`)
- **Model:** Google Gemini 2.5 Flash  
- **Resilience:** Exponential Backoff for handling HTTP 429 errors  
- **Core Methods:**  
  - `generate_all_insights()`  
  - `categorize_only()`  
  - `extract_only()`  
  - `draft_only()`

---

### 3. Data Layer (`src/db_manager.py`)
- **Database:** SQLite (`mock_inbox.db`)  
- **Tables:**  
  - `emails`: metadata, body, AI tags, drafts, shadow calendar  
  - `prompts`: user-configurable system prompts  
- **Shadow Columns:** e.g., `calendar_summary` for Stealth Calendar tasks

---

## Installation & Setup

### **Prerequisites**
- Python **3.9+**  
- Google **Gemini API Key**

---

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/email-productivity-agent.git
cd email-agent
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Configure Environment Create a  `.env` file in the root directory:**
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

### **4. Initialize Database Run the setup script to generate the mock inbox and apply the schema:**
```bash
python setup_data.py
```

### **5. Run the Application**
```bash
streamlit run app.py
```

## Usage Guide

### **1. The Inbox Workflow**
- **View:** The main screen shows your inbox. Unread emails are highlighted.
- **Filter:** Use the checkboxes on the left to filter by category (e.g., "Urgent").
- **Read:** Click an email to open the Detail View.

### **2. Processing Emails**
- **Auto-Tag:** Click "Auto-Tag New Emails" in the sidebar to batch categorize everything.
- **One-Click Analysis:** Inside an email, use the Analyze & Draft buttons to run the full AI pipeline.
- **Manual Control:** Use "Extract Actions" or "Draft Reply" for granular control.
- **Refinement:** Use the refine tool to refine the drafts on the spot, based on live feedback.

### **3. The Stealth Calendar**
- **Add Event:** Click "Add to Calendar" inside any email.
- **Behavior:** This silently extracts tasks and adds them to the "Approaching Deadlines" dashboard (top right) and the "Weekly Planner" tab.
- **Verification:** Switch to the "Calendar" tab to see your week mapped out automatically.

### **4. Configuring the "Brain"**
- Expand the **"Agent Configuration"** section in the sidebar.
- Edit the **Categorization Rules**. For example, add `[Project X]` to the text to automatically create a new filter checkbox for "Project X".
- Customize the format to display the **action items** (bullets/JSON format).
- Change the **Reply Tone** to "casual" or "Formal" to see how the drafts adapt.


## 📂 File Structure

```plaintext
email-agent/
├── app.py                 # Main Application Entry Point (UI)
├── setup_data.py          # Database Seeder & Reset Utility
├── requirements.txt       # Python Dependencies
├── .env                   # API Credentials (Ignored by Git)
│
├── src/
│   ├── __init__.py
│   ├── db_manager.py      # SQLite CRUD Operations
│   ├── llm_engine.py      # Gemini Integration & Logic
│   └── prompt_manager.py  # Prompt Injection Handler
│
└── data/
    └── mock_inbox.db
```

## **Future Enhancements**
- OAuth Email Integration (Gmail/Outlook)
- Multi-user workspace support
- Realtime WebSocket notifications
- Advanced priority scoring using ML models





