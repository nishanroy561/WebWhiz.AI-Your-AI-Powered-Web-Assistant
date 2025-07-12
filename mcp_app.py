from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import asyncio
from langchain_ollama import OllamaLLM
import streamlit as st
import nest_asyncio

nest_asyncio.apply()

######################################
# Settings
######################################

llm = OllamaLLM(model="gemma3")
BRD_API_KEY = os.environ.get('BRD_API_KEY')

mcp = MultiServerMCPClient({
    "brd_mcp": {
        "command": "node",
        "args": ["../.npm/_npx/a50edfa03303c0a4/node_modules/@brightdata/mcp/server.js"],
        "transport": "stdio",
        "env": {
            "API_TOKEN": BRD_API_KEY,
        }
    }
})

######################################
# Functions
######################################

async def mcp_tools():
    tools = await mcp.get_tools()
    return tools

async def handle_prompt(tools, url, user_prompt):
    scraper = None

    if "linkedin.com/in/" in url:
        scraper = next((t for t in tools if "linkedin" in t.name.lower() and "person_profile" in t.name.lower()), None)
    elif "linkedin.com/company/" in url:
        scraper = next((t for t in tools if "linkedin" in t.name.lower() and "company_profile" in t.name.lower()), None)
    elif "linkedin.com/jobs/" in url:
        scraper = next((t for t in tools if "linkedin" in t.name.lower() and "job_listings" in t.name.lower()), None)
    elif "linkedin.com/feed/update" in url:
        scraper = next((t for t in tools if "linkedin" in t.name.lower() and "posts" in t.name.lower()), None)
    elif "linkedin.com/search/results/people" in url:
        scraper = next((t for t in tools if "linkedin" in t.name.lower() and "people_search" in t.name.lower()), None)
    elif "github.com" in url and "/blob/" in url:
        scraper = next((t for t in tools if "github" in t.name.lower() and "repository_file" in t.name.lower()), None)
    else:
        scraper = next((t for t in tools if "scrape" in t.name.lower() and "browser" in t.name.lower()), None)

    if not scraper:
        st.error("❌ No suitable scraper tool found.")
        return "Tool not found."

    tool_input = {"url": url}

    if "people_search" in scraper.name:
        first_name = st.text_input("First Name:")
        last_name = st.text_input("Last Name:")
        if not first_name or not last_name:
            st.warning("Please enter both first and last name.")
            return "Missing name fields."
        tool_input["first_name"] = first_name
        tool_input["last_name"] = last_name

    result = await scraper.ainvoke(tool_input)

    full_prompt = (
        "Context (scraped data):\n\n"
        + result.strip()
        + "\n\nQuestion:\n\n"
        + user_prompt
    )

    response = llm.invoke(full_prompt)
    return response

######################################
# UI: Page & Styles
######################################

st.set_page_config(page_title="🤖 WebWhiz.AI", layout="centered")

# 🌟 CSS
st.markdown("""
<style>
body {
    background: linear-gradient(to right, #141e30, #243b55);
    color: #f0f0f0;
}
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}
h1, h4, p {
    text-align: center;
    color: #ffffff;
}
.big-card {
    background: rgba(255, 255, 255, 0.05);
    padding: 2rem;
    margin-top: 1.5rem;
    border-radius: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}
input, textarea {
    background-color: rgba(255,255,255,0.1) !important;
    border: 1px solid #888 !important;
    color: #fff !important;
    border-radius: 10px !important;
    padding: 10px !important;
    font-size: 16px !important;
}
div.stButton > button {
    background: linear-gradient(to right, #00c6ff, #0072ff);
    border: none;
    border-radius: 12px;
    color: white;
    padding: 12px 30px;
    font-size: 16px;
    font-weight: 600;
    transition: 0.3s ease;
}
div.stButton > button:hover {
    background: linear-gradient(to right, #0072ff, #00c6ff);
    transform: scale(1.03);
}
.response-box {
    background-color: rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    border-left: 5px solid #00c6ff;
    border-radius: 12px;
    margin-top: 2rem;
}
.tip-box {
    background-color: rgba(255,255,255,0.08);
    padding: 1rem;
    border-left: 4px solid #00c6ff;
    border-radius: 10px;
    margin-top: 1.5rem;
    font-size: 0.9rem;
    color: #ddd;
}
</style>
""", unsafe_allow_html=True)

# 🔱 Header
st.image("https://cdn-icons-png.flaticon.com/512/4712/4712007.png", width=80)
st.markdown("""
<h1>WebWhiz.AI</h1>
<h4>Your AI-Powered Web Assistant</h4>
<p style='color:#ccc;'>Scrape any public LinkedIn, GitHub or general page. Ask insightful questions and get answers instantly.</p>
""", unsafe_allow_html=True)

# 🔍 Input Section
with st.container():
    st.markdown('<div class="big-card">', unsafe_allow_html=True)

    url = st.text_input("🔗 Paste a URL (e.g. LinkedIn profile, GitHub file, or news page)", placeholder="https://linkedin.com/in/elonmusk")
    user_prompt = st.text_area("💬 What do you want to know from the page?", placeholder="Summarize the work experience of this person.")
    submit = st.button("🚀 Ask WebWhiz", use_container_width=True)

    st.markdown("""
        <div class="tip-box">
        💡 <strong>Examples:</strong><br>
        • URL: https://linkedin.com/in/sundarpichai<br>
        • Question: What companies has this person worked at?<br><br>
        • URL: https://github.com/username/project/blob/main/main.py<br>
        • Question: What does this Python function do?
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# 🛠 Tool loading
tools = asyncio.run(mcp_tools())

# 💬 Submit logic
if submit:
    if not url or not user_prompt:
        st.warning("Please fill in both URL and question.")
    else:
        with st.spinner("🔍 Scraping the page and thinking..."):
            response = asyncio.run(handle_prompt(tools, url, user_prompt))
            st.markdown('<div class="response-box">', unsafe_allow_html=True)
            st.markdown("### 🧠 WebWhiz Answer:")
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)

# 📌 Footer
st.markdown("""
---
<div style="text-align: center; font-size: 0.9em; color: gray;">
    Built with ❤️ using LangChain, Ollama, and Streamlit • WebWhiz.AI © 2025
</div>
""", unsafe_allow_html=True)
