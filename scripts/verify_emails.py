import re

emails = [
    {
        "company": "Discover Dollar Inc",
        "role": "AI Engineer Intern (Agentic AI & LLMs)",
        "subject": "AI Engineer Intern – Agentic AI & RAG Pipelines | Nitin Chander",
        "body": """Hi Discover Dollar Team,

I saw your AI Engineer Intern opening and love your focus on agentic AI for revenue recovery. As a CS student at MAIT experienced in building end-to-end LLM systems, I'd love to contribute.

At IDEMIA, I engineered Python data pipelines and RAG-enabled workflows. Recently, I built an AI Travel Concierge using LangChain, ChromaDB, and Gemini API for multi-turn semantic reasoning, plus an end-to-end fraud detection pipeline tracked via MLflow.

Could we schedule a quick 10-minute chat to discuss how my backend and agentic AI experience can support your team?"""
    },
    {
        "company": "Venxr",
        "role": "Generative AI Engineering Intern",
        "subject": "GenAI Intern – Conversational RAG & Multi-Turn Agents | Nitin Chander",
        "body": """Hi Venxr Team,

I've been following AdsGPT and find your conversational ad automation impressive. Given my hands-on background in generative AI and backend engineering, I'm eager to contribute to your engineering team.

I recently developed an AI Travel Concierge utilizing LangChain, ChromaDB vector search, and Gemini API with conversational memory for multi-turn interactions. At IDEMIA, I engineered NLP pipelines and structured datasets using Python and SQL. My stack combines prompt engineering, FastAPI, and vector retrieval.

I would welcome a brief 10-minute call to explore how my RAG skill set aligns with Venxr's roadmap."""
    },
    {
        "company": "CredHive",
        "role": "Software Engineer Intern (AI Systems)",
        "subject": "Software Engineer Intern – AI Risk & Python Backend | Nitin Chander",
        "body": """Hi CredHive Team,

CredHive's AI-driven approach to revolutionizing credit risk assessment immediately caught my attention. Based in Delhi at MAIT and experienced in Python backend and ML systems, I would love to contribute to your engineering team.

I recently architected an End-to-End Fraud Detection System using Scikit-learn, XGBoost, and FastAPI, tracking models via MLflow. Previously at Paytm, I engineered scalable backend REST services in Python and SQL for core financial workflows.

I’d love to connect for 10 minutes to discuss how my backend rigor and machine learning background can deliver immediate value to CredHive."""
    },
    {
        "company": "The SmartBridge",
        "role": "AI Engineer Intern",
        "subject": "AI Engineer Intern – Python & GenAI Architecture | Nitin Chander",
        "body": """Hi The SmartBridge Team,

I am writing to express my strong interest in the AI Engineer Intern position in Noida. Having built scalable backend architectures and AI platforms, your experiential AI learning mission strongly resonates with me.

I built LearnForge, a modular learning platform with Flask and PostgreSQL featuring JWT authentication and progress tracking. Additionally, I've implemented RAG applications using LangChain and ChromaDB, and engineered data ingestion pipelines during my internship at IDEMIA.

I would appreciate the chance to discuss how my hands-on Python and GenAI experience can support The SmartBridge’s upcoming initiatives in a brief chat."""
    },
    {
        "company": "Lexsi Labs / AryaXAI",
        "role": "AI Agent Engineer Intern",
        "subject": "AI Agent Engineer Intern – Autonomous Agents & RAG | Nitin Chander",
        "body": """Hi Lexsi Labs Team,

Your focus on interpretable and reliable autonomous AI agents aligns directly with my engineering passion. As a CS student at MAIT specializing in LLM systems, I am excited to apply for the AI Agent Engineer Internship.

I built an AI assistant featuring LangChain, ChromaDB semantic search, and multi-turn conversational memory powered by the Gemini API. During my internship at IDEMIA, I deployed NLP and RAG backend workflows. I'm proficient in Python, vector embeddings, and evaluation benchmarks.

Could we connect for a brief 10-minute discussion on how I can assist in deploying your agent architectures?"""
    },
    {
        "company": "Digitap.ai",
        "role": "Python Development Intern",
        "subject": "Python Development Intern – High-Performance APIs & SQL | Nitin Chander",
        "body": """Hi Digitap Team,

Digitap's high-throughput digital intelligence and alternative data infrastructure is remarkable. Having developed scalable backend services and automated data workflows, I am eager to contribute as a Python Development Intern.

During my internship at Paytm, I engineered scalable Python REST APIs and optimized database interactions for core workflows. At NTPC, I improved query performance through index restructuring and automated data tasks. My stack centers on Python, FastAPI, Flask, PostgreSQL, and SQLAlchemy.

I would love a quick 10-minute call to share how my backend engineering experience and data pipeline skills can support Digitap’s API infrastructure."""
    },
    {
        "company": "The Affordable Organic Store",
        "role": "Full Stack AI Engineer – AI Agents Intern",
        "subject": "AI Agents Intern – Conversational Workflows & APIs | Nitin Chander",
        "body": """Hi TAOS Team,

I noticed your opening for the AI Agents Internship and love how you deploy conversational AI to automate e-commerce workflows. With practical experience building agentic RAG systems and Python backends, I am keen to help.

I built a conversational assistant utilizing LangChain, ChromaDB vector retrieval, and Gemini API to handle complex, multi-turn dialogues. Complementing this, I have engineered production backends with Flask and FastAPI, including modular authentication and data management.

I would love to hop on a short 10-minute call to demonstrate how my AI agent and Python experience can benefit your automation team."""
    },
    {
        "company": "Dimakh Consultants",
        "role": "AI/ML Intern",
        "subject": "AI/ML Intern – Python Pipelines & Model Deployment | Nitin Chander",
        "body": """Hi Dimakh Consultants Team,

I am writing to express my enthusiasm for the AI/ML Intern position. With proven experience engineering Python data pipelines, developing ML models, and deploying REST APIs, I am ready to make an immediate impact.

At IDEMIA, I developed Python modules for AI data ingestion and implemented NLP workflows. In my personal projects, I designed an end-to-end fraud detection pipeline comparing XGBoost and Random Forest, deploying the winning model via FastAPI with MLflow.

I would welcome a brief 10-minute chat to discuss how my machine learning and backend skills align with your deliverables."""
    },
    {
        "company": "Crossing Infotech",
        "role": "Python Developer Intern",
        "subject": "Python Developer Intern – Clean Architecture & SQL | Nitin Chander",
        "body": """Hi Crossing Infotech Team,

I am writing to apply for the Python Developer Intern role. Having completed internships at Paytm, IDEMIA, and NTPC, I have built a solid foundation in Python programming, SQL databases, and Git collaboration workflows.

At Paytm, I engineered scalable backend REST services, while at NTPC I optimized complex database queries and automated backend data processing routines. I build maintainable code using Python, PostgreSQL, and FastAPI, adhering to clean architecture principles.

I would be thrilled to connect for a quick 10-minute conversation to learn more about your engineering goals and discuss how I can contribute."""
    },
    {
        "company": "Training Basket",
        "role": "ML Intern",
        "subject": "ML Intern – Data Preprocessing & Model Evaluation | Nitin Chander",
        "body": """Hi Training Basket Team,

I am excited to apply for the ML Intern role in Noida. As a Computer Science student at MAIT with hands-on experience in feature engineering, model evaluation, and Python automation, I am eager to contribute.

I built an End-to-End Fraud Detection System where I handled class imbalance, evaluated XGBoost and Random Forest models across Precision-Recall and ROC-AUC metrics, and tracked experiments with MLflow. At IDEMIA, I processed datasets using Pandas and NumPy.

Could we schedule a short 10-minute conversation to discuss how my machine learning skills can add value?"""
    }
]

for i, e in enumerate(emails):
    words = re.findall(r'\b\w+\b', e['body'])
    print(f"Email {i+1} ({e['company']}): {len(words)} words")
