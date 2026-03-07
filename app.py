import streamlit as st
import pandas as pd
from PIL import Image
from database import (
    init_db, get_all_strategies, add_strategy, 
    get_strategy_examples, add_strategy_example, delete_strategy_example,
    get_all_trades, add_trade, delete_trade
)
from utils import inject_custom_css, save_uploaded_file, save_pil_image
from streamlit_paste_button import paste_image_button
import os

# Page config
st.set_page_config(
    page_title="AlphaTracer Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize database and apply global CSS
init_db()
inject_custom_css()

def main():
    st.title("⚡ AlphaTracer Terminal")
    st.markdown("---")
    
    # -------------------------------------------------------------
    # SECTION 1: Strategy Selector & Builder
    # -------------------------------------------------------------
    strats_df = get_all_strategies()
    strategy_options = {row['id']: row['name'] for index, row in strats_df.iterrows()}
    
    col_strat_select, col_strat_new = st.columns([2, 1])
    
    with col_strat_select:
        st.subheader("1. Active Strategy")
        if not strategy_options:
            st.warning("No strategies found. Please create one to begin logging trades.")
            active_strategy_id = None
            active_strategy_name = None
        else:
            # Determine the currently active strategy via session state or default to the first one
            if 'active_strat_id' not in st.session_state or st.session_state['active_strat_id'] not in strategy_options:
                st.session_state['active_strat_id'] = list(strategy_options.keys())[0]
                
            active_strategy_id = st.session_state['active_strat_id']
            # Find the display name for the selector
            current_name_index = list(strategy_options.values()).index(strategy_options[active_strategy_id])
            
            selected_strat_name = st.selectbox(
                "Select a Strategy to focus on:", 
                list(strategy_options.values()),
                index=current_name_index
            )
            
            # Update session state ID based on selection
            active_strategy_id = next(id for id, name in strategy_options.items() if name == selected_strat_name)
            active_strategy_name = selected_strat_name
            st.session_state['active_strat_id'] = active_strategy_id
            
            # Show strategy details
            active_row = strats_df[strats_df['id'] == active_strategy_id].iloc[0]
            with st.expander("View Strategy Rules", expanded=False):
                st.write(f"**Description:** {active_row['description']}")
                st.write(f"**Entry Rules:** {active_row['entry_rules']}")
                st.write(f"**Exit Rules:** {active_row['exit_rules']}")
                st.write(f"**Risk Management:** {active_row['risk_management']}")

    with col_strat_new:
        st.subheader("Define New Strategy")
        with st.expander("➕ Create Strategy"):
            with st.form("new_strategy_form", clear_on_submit=True):
                strat_name = st.text_input("Name (e.g., ORB, S/R Flip)")
                strat_desc = st.text_area("High-Level Description")
                entry_rules = st.text_area("Entry Criteria", height=100)
                exit_rules = st.text_area("Exit Criteria", height=100)
                risk_mgt = st.text_area("Risk Management")
                
                if st.form_submit_button("Save Strategy"):
                    if not strat_name:
                        st.error("Strategy Name is required!")
                    else:
                        success = add_strategy(strat_name, strat_desc, entry_rules, exit_rules, risk_mgt)
                        if success:
                            st.success(f"'{strat_name}' created!")
                            st.rerun()
                        else:
                            st.error("Name might already exist.")

    st.markdown("---")
    
    # -------------------------------------------------------------
    # ONLY LOAD SECTIONS 2 AND 3 IF A STRATEGY IS SELECTED
    # -------------------------------------------------------------
    if active_strategy_id is not None:
        
        # -------------------------------------------------------------
        # SECTION 2: Trade Action Panel
        # -------------------------------------------------------------
        st.subheader(f"2. Log Activity for '{active_strategy_name}'")
        
        tab_log_trade, tab_log_proof = st.tabs(["📊 Log Live Trade", "🖼️ Add Visual Proof (Testing)"])
        
        # 2A: LOG LIVE TRADE
        with tab_log_trade:
            with st.form(f"trade_form_{active_strategy_id}", clear_on_submit=True):
                col_form1, col_form2 = st.columns([1, 1])
                
                with col_form1:
                    symbol = st.text_input("Symbol / Ticker")
                    direction = st.selectbox("Direction", ["Long", "Short"])
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1: entry_date = st.date_input("Entry Date")
                    with sub_col2: exit_date = st.date_input("Exit Date")
                    pnl = st.number_input("PnL ($)", value=0.0, step=10.0)
                    
                with col_form2:
                    st.markdown("Upload or paste the chart screenshot.")
                    uploaded_trade_img = st.file_uploader("Choose Chart Screenshot", type=['png', 'jpg', 'jpeg'], key="trade_uploader")
                    st.markdown("**OR** Paste from Clipboard:")
                    paste_trade_result = paste_image_button("📋 Paste Image", background_color="#161b22", hover_background_color="#30363D", key="trade_paste")
                    notes = st.text_area("Trade Notes / Lessons Learned", height=100)
                    
                if st.form_submit_button("Log Trade"):
                    if not symbol:
                        st.error("Symbol is required!")
                    else:
                        image_path = None
                        if uploaded_trade_img is not None:
                            image_path = save_uploaded_file(uploaded_trade_img, prefix=f"trade_{symbol}")
                        elif paste_trade_result.image_data is not None:
                            image_path = save_pil_image(paste_trade_result.image_data, prefix=f"trade_{symbol}")
                            
                        add_trade(symbol, str(entry_date), str(exit_date) if exit_date else None, 
                                  direction, active_strategy_id, pnl, image_path, notes)
                        st.success(f"Logged trade for {symbol}!")
                        st.rerun()
                        
        # 2B: ADD VISUAL PROOF (TESTING/GALLERY)
        with tab_log_proof:
            with st.form(f"proof_form_{active_strategy_id}", clear_on_submit=True):
                st.markdown("Upload a historical chart proving this strategy works (or fails).")
                proof_img = st.file_uploader("Upload Testing Screenshot", type=['png', 'jpg', 'jpeg'], key="proof_uploader")
                st.markdown("**OR** Paste from Clipboard:")
                paste_proof_result = paste_image_button("📋 Paste Image", background_color="#161b22", hover_background_color="#30363D", key="proof_paste")
                proof_comment = st.text_area("Commentary (Why does this setup work or fail?)", height=100)
                
                if st.form_submit_button("Add to Strategy Proof"):
                    saved_path = None
                    if proof_img is not None:
                        saved_path = save_uploaded_file(proof_img, prefix=f"strat_{active_strategy_id}_proof")
                    elif paste_proof_result.image_data is not None:
                        saved_path = save_pil_image(paste_proof_result.image_data, prefix=f"strat_{active_strategy_id}_proof")
                    else:
                        st.error("Please provide an image.")
                        
                    if saved_path is not None:
                        add_strategy_example(active_strategy_id, saved_path, proof_comment)
                        st.success("Proof added!")
                        st.rerun()
                        
        st.markdown("---")
        
        # -------------------------------------------------------------
        # SECTION 3: Unified Visual Gallery
        # -------------------------------------------------------------
        st.subheader(f"3. Intelligence Gallery: '{active_strategy_name}'")
        
        # Fetch data only for the active strategy
        all_trades_df = get_all_trades()
        strat_trades_df = all_trades_df[all_trades_df['strategy_id'] == active_strategy_id] if not all_trades_df.empty else pd.DataFrame()
        strat_proofs_df = get_strategy_examples(active_strategy_id)
        
        tab_view_trades, tab_view_proofs = st.tabs(["Live Trades", "Visual Proofs"])
        
        # 3A: VIEW LIVE TRADES
        with tab_view_trades:
            if strat_trades_df.empty:
                st.info("No live trades logged for this strategy.")
            else:
                total_pnl = strat_trades_df['pnl'].sum()
                num_trades = len(strat_trades_df)
                win_rate = (len(strat_trades_df[strat_trades_df['pnl'] > 0]) / num_trades * 100) if num_trades > 0 else 0
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                col_stat1.metric("Strategy PnL", f"${total_pnl:.2f}")
                col_stat2.metric("Win Rate", f"{win_rate:.1f}%")
                col_stat3.metric("Trades", num_trades)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                cols_per_row = 3
                for i in range(0, len(strat_trades_df), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < len(strat_trades_df):
                            trade = strat_trades_df.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    st.markdown(f"**{trade['direction']} {trade['symbol']}**")
                                    pnl_color = "green" if trade['pnl'] >= 0 else "red"
                                    st.markdown(f"PnL: <span style='color:{pnl_color}; font-weight:bold;'>${trade['pnl']}</span> | Date: {trade['entry_date']}", unsafe_allow_html=True)
                                    
                                    if pd.notna(trade['image_path']) and os.path.exists(trade['image_path']):
                                        try:
                                            st.image(Image.open(trade['image_path']), use_container_width=True)
                                        except Exception as e:
                                            st.error("Image load error.")
                                            
                                    with st.expander("Notes"):
                                        st.write(trade['notes'])
                                        
                                    if st.button(f"🗑️ Delete", key=f"del_t_{trade['id']}"):
                                        delete_trade(trade['id'])
                                        st.rerun()
                                        
        # 3B: VIEW PROOFS (TESTING GALLERY)
        with tab_view_proofs:
            if strat_proofs_df.empty:
                st.info("No visual proofs added for this strategy.")
            else:
                st.write(f"**Total Gathered Proofs:** {len(strat_proofs_df)}")
                
                cols_per_row = 3
                for i in range(0, len(strat_proofs_df), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < len(strat_proofs_df):
                            proof = strat_proofs_df.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    if pd.notna(proof['image_path']) and os.path.exists(proof['image_path']):
                                        try:
                                            st.image(Image.open(proof['image_path']), use_container_width=True)
                                        except Exception as e:
                                            st.error("Image load error.")
                                    st.write(proof['comment'])
                                    if st.button(f"🗑️ Delete", key=f"del_p_{proof['id']}"):
                                        delete_strategy_example(proof['id'])
                                        st.rerun()

if __name__ == "__main__":
    main()
