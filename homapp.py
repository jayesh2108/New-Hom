import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Masaba 2026 AEO Insights", layout="wide", page_icon="🎨")

st.title("🎨 House of Masaba: 2026 Buying Intent Analyzer")
st.markdown("Track visibility for **High-Intent** luxury shoppers across 2026's core ethnic categories.")

# --- 2. SIDEBAR SETUP ---
with st.sidebar:
    st.header("⚙️ 2026 Market Context")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    
    brand_name = st.text_input("Brand Name", value="House of Masaba")
    brand_domain = st.text_input("Brand Domain", value="houseofmasaba.com")
    
    # Category Input Mode
    input_mode = st.radio("Category Selection Mode", ["Prefilled Categories", "Manual Entry"])
    
    # 2026 High-Intent Categories for Masaba
    prefilled_list = (
        "designer sarees, kaftans, pret wear, lehengas, "
        "bridal sarees, bridal lehengas, designer lehengas"
    )
    
    if input_mode == "Manual Entry":
        categories_input = st.text_area("Enter your custom categories (comma separated)", 
                                       placeholder="e.g. resort wear, fusion sets, bridesmaid outfits")
    else:
        categories_input = st.text_area("2026 Core Categories", value=prefilled_list)
    
    num_queries = st.slider("Queries per Category", 1, 4, 2)

    if api_key:
        openai.api_key = api_key

# --- 3. CORE LOGIC FUNCTIONS ---

def discover_buying_prompts(categories, n):
    """Generates short, high-intent transactional queries for 2026."""
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a 2026 India Luxury Search Expert. Market: High-end ethnic wear."},
                {"role": "user", "content": f"""
                Generate {n} short, distinct, high-buying-intent queries for '{cat}'.
                - Max 6 words per query. No long-tail conversational fluff.
                - Use transactional modifiers: 'buy', 'best', 'designer', 'luxury'.
                - Focus on 2026 trends (fusion, pre-draped, structured lehengas).
                - Return ONLY the list.
                """}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_presence(query, brand_name):
    """Stricter 2026 Parser: Only counts if brand is in the numbered Top 10 list."""
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a 2026 AI Shopping Assistant. Provide a numbered list of the Top 10 luxury brands in India for the query. Format: 1. Brand Name - USP."},
                {"role": "user", "content": f"Where can I buy the best {query} in India for 2026?"}
            ]
        )
        list_output = resp.choices[0].message.content.strip()
        
        # Stricter SOV Logic: Prevents false positives from 'Advice' sections
        is_present = "No"
        lines = list_output.splitlines()
        for line in lines:
            if re.match(r'^\d+\.', line) and brand_name.lower().split()[0] in line.lower():
                is_present = "Yes"
                break
                
        return {"Query": query, "Brand Present": is_present, "AI Top 10 List": list_output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Top 10 List": str(e)}

# --- 4. EXECUTION ENGINE ---

if st.button("🚀 Run 2026 Buying Intent Scan"):
    if not api_key:
        st.error("❌ Please enter your OpenAI API Key.")
    elif not categories_input:
        st.error("❌ Please provide categories to analyze.")
    else:
        with st.status("Analyzing 2026 Luxury Landscape...", expanded=True) as status:
            st.write("📈 Discovering transactional shopping queries...")
            queries = discover_buying_prompts(categories_input, num_queries)
            
            results = []
            bar = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Testing Presence for: **{q}**")
                res = check_presence(q, brand_name)
                results.append(res)
                bar.progress((i + 1) / len(queries))
            
            st.session_state['masaba_results_2026'] = pd.DataFrame(results)
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

# --- 5. RESULTS DISPLAY ---

if 'masaba_results_2026' in st.session_state and st.session_state['masaba_results_2026'] is not None:
    df = st.session_state['masaba_results_2026']
    
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        sov = (df[df['Brand Present'] == "Yes"].shape[0] / len(df)) * 100
        st.metric("Buyer Intent Share of Voice (SOV)", f"{sov:.1f}%")
        
    with col2:
        fig = px.pie(df, names="Brand Present", title="2026 Visibility Breakdown",
                     color="Brand Present", color_discrete_map={"Yes":"#D4AF37", "No":"#2C3E50"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 2026 Market Intelligence Table")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download 2026 Report", data=csv, file_name="masaba_2026_intent.csv")
else:
    st.info("💡 Select your mode and categories, then click the button above.")