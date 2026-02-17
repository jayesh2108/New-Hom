import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Masaba 2026 AEO Insights", layout="wide", page_icon="🎨")

st.title("🎨 House of Masaba: 2026 Buyer Intent Analyzer")
st.markdown("Track visibility for **High-Intent** luxury shoppers in the 2026 Indian market.")

# --- 2. SIDEBAR SETUP ---
with st.sidebar:
    st.header("⚙️ 2026 Search Context")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    
    # 2026 High-Intent Luxury Categories
    masaba_2026_categories = (
        "buy designer sarees, luxury floral co-ords, "
        "quirky bridal lehengas online, pre-draped luxury sarees, "
        "designer resort wear India, luxury fusion pret wear, "
        "gold print anarkali sets, designer fine jewelry"
    )
    
    categories_input = st.text_area("2026 Target Categories", value=masaba_2026_categories)
    num_queries = st.slider("Queries per Category", 2, 4, 2)

    if api_key:
        openai.api_key = api_key

# --- 3. CORE LOGIC FUNCTIONS ---

def discover_buying_prompts(categories, n):
    """Generates short, concise buyer-intent queries for 2026."""
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a 2026 India Luxury Search Expert. Target: High-intent buyers."},
                {"role": "user", "content": f"""
                Generate {n} short, distinct, high-buying-intent queries for '{cat}'.
                - Max 6 words per query.
                - Use modifiers: 'buy', 'best', 'designer', 'luxury', 'online'.
                - Focus on 2026 trends (pre-draped, resort luxe).
                - Return ONLY the list.
                """}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_presence(query):
    """Strict 2026 Parser: Only counts if brand is in the numbered Top 10 list."""
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a 2026 AI Shopping Assistant. Provide a numbered list of the Top 10 luxury buying options in India. Format: 1. Brand Name - USP."},
                {"role": "user", "content": f"Where can I buy the best {query} in India for 2026?"}
            ]
        )
        list_output = resp.choices[0].message.content.strip()
        
        # Stricter SOV Logic: Must be in the numbered list to count as 'Yes'
        is_present = "No"
        lines = list_output.splitlines()
        for line in lines:
            if re.match(r'^\d+\.', line) and "masaba" in line.lower():
                is_present = "Yes"
                break
                
        return {"Query": query, "Brand Present": is_present, "AI Top 10 List": list_output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Top 10 List": str(e)}

# --- 4. EXECUTION ENGINE ---

if st.button("🚀 Analyze 2026 Buyer Intent"):
    if not api_key:
        st.error("❌ Please enter your OpenAI API Key.")
    else:
        with st.status("Analyzing 2026 Luxury Landscape...", expanded=True) as status:
            st.write("📈 Generating 2026 high-intent prompts...")
            queries = discover_buying_prompts(categories_input, num_queries)
            
            results = []
            progress_bar = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Testing Buyer Intent: **{q}**")
                res = check_presence(q)
                results.append(res)
                progress_bar.progress((i + 1) / len(queries))
            
            st.session_state['masaba_2026_df'] = pd.DataFrame(results)
            status.update(label="✅ 2026 Analysis Complete!", state="complete", expanded=False)

# --- 5. RESULTS DISPLAY ---

if 'masaba_2026_df' in st.session_state and st.session_state['masaba_2026_df'] is not None:
    df = st.session_state['masaba_2026_df']
    
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate SOV based only on actual list presence
        sov = (df[df['Brand Present'] == "Yes"].shape[0] / len(df)) * 100
        st.metric("2026 Buyer Intent Share (SOV)", f"{sov:.1f}%")
        
    with col2:
        fig = px.pie(df, names="Brand Present", title="2026 AI Recommendation Breakdown",
                     color="Brand Present", color_discrete_map={"Yes":"#D4AF37", "No":"#2C3E50"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 2026 Market Intelligence Table")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download 2026 Report", data=csv, file_name="masaba_2026_aeo.csv")
else:
    st.info("💡 Adjust your 2026 categories and click the button to start.")