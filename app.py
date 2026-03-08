import streamlit as st
import pandas as pd
from PIL import Image
import os
from database import (
    init_db, get_all_strategies, add_strategy, 
    get_strategy_examples, add_strategy_example, delete_strategy_example,
    get_all_trades, add_trade, delete_trade, delete_strategy
)
from utils import inject_custom_css, save_uploaded_file, save_pil_image, save_audio_file, extract_ticker_from_image
from streamlit_paste_button import paste_image_button
from audio_recorder_streamlit import audio_recorder

# Page config
st.set_page_config(
    page_title="Mike's Trading Journal",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize database and apply global CSS
init_db()
inject_custom_css()

def show_strategies_page():
    # Use HTML for the main title to utilize the new Space Grotesk gradient text styling
    st.markdown("<h1 style='text-align: center;'>Mike's Trading Journal</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    strats_df = get_all_strategies()

    st.subheader("Define New Strategy")
    with st.expander("Create Strategy"):
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

    st.markdown("<h2>Active Strategies</h2>", unsafe_allow_html=True)
    st.write("") # spacing
    if strats_df.empty:
        st.warning("No strategies found. Please create one to begin logging trades.")
    else:
        # Fetch all trades once to calculate metrics for the cards
        all_trades_df = get_all_trades()
        
        # Display strategies as distinct cards
        for _, row in strats_df.iterrows():
            with st.container(border=True):
                cols = st.columns([6, 2])
                with cols[0]:
                    st.markdown(f"### {row['name']}")
                    st.write(f"*{row['description']}*")
                    
                    # Calculate Card Metrics
                    strat_trades = all_trades_df[all_trades_df['strategy_id'] == row['id']] if not all_trades_df.empty else pd.DataFrame()
                    num_trades = len(strat_trades)
                    win_rate = (len(strat_trades[strat_trades['pnl'] > 0]) / num_trades * 100) if num_trades > 0 else 0
                    total_pnl = strat_trades['pnl'].sum() if num_trades > 0 else 0.0
                    
                    pnl_color = "#3fb950" if total_pnl >= 0 else "#f85149"
                    st.markdown(f"**Trades:** {num_trades} &nbsp;&nbsp;|&nbsp;&nbsp; **Win Rate:** {win_rate:.0f}% &nbsp;&nbsp;|&nbsp;&nbsp; **Net PnL:** <span style='color:{pnl_color};'>${total_pnl:.2f}</span>", unsafe_allow_html=True)
                    
                with cols[1]:
                    st.write("") # spacing
                    if st.button("Open Gallery", key=f"open_{row['id']}", use_container_width=True):
                        st.session_state['active_strat_id'] = row['id']
                        st.session_state['page'] = 'gallery'
                        st.session_state['show_log_form'] = False
                        st.rerun()
                
                with st.expander("View Strategy Rules", expanded=False):
                    st.write(f"**Entry Rules:** {row['entry_rules']}")
                    st.write(f"**Exit Rules:** {row['exit_rules']}")
                    st.write(f"**Risk Management:** {row['risk_management']}")
                    st.markdown("---")
                    
                    # Placed inside the expander to prevent accidental clicks
                    col_rule1, col_rule2 = st.columns([4, 1])
                    with col_rule2:
                        if st.button("🗑️ Delete Strategy", key=f"del_strat_{row['id']}", help="Permanently delete this strategy and all its data", type="primary"):
                            delete_strategy(row['id'])
                            st.rerun()

def show_gallery_page():
    active_strategy_id = st.session_state.get('active_strat_id')
    if active_strategy_id is None:
        st.session_state['page'] = 'strategies'
        st.rerun()

    strats_df = get_all_strategies()
    if active_strategy_id not in strats_df['id'].values:
        st.error("Strategy not found.")
        if st.button("Return to Strategies"):
            st.session_state['page'] = 'strategies'
            st.rerun()
        return

    active_row = strats_df[strats_df['id'] == active_strategy_id].iloc[0]
    active_strategy_name = active_row['name']

    # Header section with Back button and Title
    col_back, col_title, col_log = st.columns([1, 7, 2])
    with col_back:
        st.write("") # vertical alignment padding
        if st.button("⬅ Back", use_container_width=True):
            st.session_state['page'] = 'strategies'
            st.rerun()
    with col_title:
        st.markdown(f"<h2>Intelligence Gallery: '{active_strategy_name}'</h2>", unsafe_allow_html=True)
    with col_log:
        st.write("") # vertical alignment padding
        if st.button("➕ Log Activity", use_container_width=True):
            st.session_state['show_log_form'] = not st.session_state.get('show_log_form', False)
            st.rerun()

    st.markdown("---")

    # The Log Activity pop-down form
    if st.session_state.get('show_log_form', False):
        with st.container(border=True):
            st.subheader("Log New Activity")
            tab_log_trade, tab_log_proof = st.tabs(["Log Live Trade", "Add Visual Proof (Testing)"])
            
            # 2A: LOG LIVE TRADE
            with tab_log_trade:
                reset_key = st.session_state.get('form_reset_count', 0)
                col_form1, col_form2 = st.columns([1, 1])
                
                with col_form1:
                    symbol_key = f"trade_sym_{reset_key}"
                    default_sym = st.session_state.get('ocr_extracted_symbol', '')
                    symbol = st.text_input("Symbol / Ticker", value=default_sym, key=symbol_key)
                    direction = st.selectbox("Direction", ["Long", "Short"], key=f"trade_dir_{reset_key}")
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1: entry_date = st.date_input("Entry Date", key=f"trade_entry_{reset_key}")
                    with sub_col2: exit_date = st.date_input("Exit Date (Optional)", value=None, key=f"trade_exit_{reset_key}")
                    pnl = st.number_input("PnL ($)", value=0.0, step=10.0, key=f"trade_pnl_{reset_key}")
                    
                with col_form2:
                    st.markdown("Paste the chart screenshot from your clipboard:")
                    paste_trade_result = paste_image_button("Paste Image", background_color="#161b22", hover_background_color="#30363D", key="trade_paste")
                    
                    # Local Free OCR Extraction Logic & Visual Preview
                    if paste_trade_result.image_data is not None:
                        st.session_state['current_trade_image'] = paste_trade_result.image_data
                        
                    cached_img = st.session_state.get('current_trade_image')
                    if cached_img is not None:
                        st.image(cached_img, caption="Pasted Chart Preview", use_container_width=True)
                        
                        img_hash = hash(cached_img.tobytes()[:5000]) # Quick hash to detect new pastes
                        if st.session_state.get('last_pasted_hash') != img_hash:
                            st.session_state['last_pasted_hash'] = img_hash
                            with st.spinner("Scanning chart for ticker..."):
                                extracted = extract_ticker_from_image(cached_img, debug=True)
                                if extracted:
                                    st.session_state['ocr_extracted_symbol'] = extracted
                                    st.session_state['form_reset_count'] = reset_key + 1
                                st.rerun()
                    # Debug Output for the user to see what OCR reads
                    # (Removed in production)

                    notes = st.text_area("Trade Notes / Lessons Learned", value=st.session_state.get('trade_notes_val', ''), height=100, key=f"trade_notes_{reset_key}")
                    
                    st.write("Record Voice Notes (Optional):")
                    audio_bytes = audio_recorder(text="Click to record", recording_color="#ef4444", neutral_color="#3b82f6", icon_name="microphone", icon_size="2x", key=f"trade_audio_{reset_key}")
                    
                if st.button("Submit Trade", key=f"submit_trade_{active_strategy_id}_{reset_key}"):
                    if not symbol:
                        st.error("Symbol is required!")
                    else:
                        image_path = None
                        if cached_img is not None:
                            image_path = save_pil_image(cached_img, prefix=f"trade_{symbol}")
                        
                        saved_audio_path = save_audio_file(audio_bytes, prefix=symbol) if audio_bytes else None
                            
                        add_trade(symbol, str(entry_date), str(exit_date) if exit_date else None, 
                                  direction, active_strategy_id, pnl, image_path, notes, saved_audio_path)
                        st.success(f"Logged trade for {symbol}!")
                        
                        # Reset custom variables
                        st.session_state['ocr_extracted_symbol'] = ""
                        st.session_state['form_reset_count'] = reset_key + 1
                        st.session_state['last_pasted_hash'] = None
                        st.session_state['ocr_debug_text'] = None
                        st.session_state['current_trade_image'] = None
                        st.session_state['show_log_form'] = False
                        st.rerun()
                            
            # 2B: ADD VISUAL PROOF (TESTING/GALLERY)
            with tab_log_proof:
                proof_reset_key = st.session_state.get('proof_reset_count', 0)
                st.markdown("Paste a historical chart proving this strategy works (or fails) from your clipboard:")
                paste_proof_result = paste_image_button("Paste Image", background_color="#161b22", hover_background_color="#30363D", key="proof_paste")
                
                if paste_proof_result.image_data is not None:
                    st.session_state['current_proof_image'] = paste_proof_result.image_data
                    
                cached_proof = st.session_state.get('current_proof_image')
                if cached_proof is not None:
                    st.image(cached_proof, caption="Pasted Proof Preview", use_container_width=True)
                    
                proof_comment = st.text_area("Commentary (Why does this setup work or fail?)", height=100, key=f"proof_comment_{proof_reset_key}")

                st.write("Record Voice Commentary (Optional):")
                proof_audio_bytes = audio_recorder(text="Click to record", recording_color="#ef4444", neutral_color="#3b82f6", icon_name="microphone", icon_size="2x", key=f"proof_audio_{proof_reset_key}")
                
                if st.button("Add Visual Proof", key=f"submit_proof_{active_strategy_id}_{proof_reset_key}"):
                    image_path = None
                    if cached_proof is not None:
                        image_path = save_pil_image(cached_proof, prefix="proof")
                    
                    saved_proof_audio = save_audio_file(proof_audio_bytes, prefix="proof") if proof_audio_bytes else None

                    add_strategy_example(active_strategy_id, image_path, proof_comment, saved_proof_audio)
                    st.success("Successfully added visual proof!")
                    st.session_state['current_proof_image'] = None
                    st.session_state['proof_reset_count'] = proof_reset_key + 1
                    st.session_state['show_log_form'] = False
                    st.rerun()
        st.markdown("---")
        
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
            
            with st.container():
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                col_stat1.metric("Strategy PnL", f"${total_pnl:.2f}")
                col_stat2.metric("Win Rate", f"{win_rate:.1f}%")
                col_stat3.metric("Trades", num_trades)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Massive 1-column layout for Trades
            for _, trade in strat_trades_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{trade['direction']} {trade['symbol']}**")
                    pnl_color = "green" if trade['pnl'] >= 0 else "red"
                    st.markdown(f"PnL: <span style='color:{pnl_color}; font-weight:bold;'>${trade['pnl']}</span> | Date: {trade['entry_date']}", unsafe_allow_html=True)
                    
                    if pd.notna(trade['image_path']) and os.path.exists(trade['image_path']):
                        try:
                            st.image(Image.open(trade['image_path']), use_container_width=True)
                        except Exception as e:
                            st.error("Image load error.")
                            
                    if 'audio_path' in trade and pd.notna(trade['audio_path']) and os.path.exists(trade['audio_path']):
                        st.audio(trade['audio_path'], format='audio/wav')
                            
                    with st.expander("Notes"):
                        st.write(trade['notes'])
                        
                    if st.button(f"Delete", key=f"del_t_{trade['id']}"):
                        delete_trade(trade['id'])
                        st.rerun()
                                    
    # 3B: VIEW PROOFS (TESTING GALLERY)
    with tab_view_proofs:
        if strat_proofs_df.empty:
            st.info("No visual proofs added for this strategy.")
        else:
            st.write(f"**Total Gathered Proofs:** {len(strat_proofs_df)}")
            
            # Massive 1-column layout for Visual Proofs
            for _, proof in strat_proofs_df.iterrows():
                with st.container(border=True):
                    if pd.notna(proof['image_path']) and os.path.exists(proof['image_path']):
                        try:
                            st.image(Image.open(proof['image_path']), use_container_width=True)
                        except Exception as e:
                            st.error("Image load error.")
                            
                    if 'audio_path' in proof and pd.notna(proof['audio_path']) and os.path.exists(proof['audio_path']):
                        st.audio(proof['audio_path'], format='audio/wav')
                            
                    st.write(proof['comment'])
                    if st.button(f"Delete", key=f"del_p_{proof['id']}"):
                        delete_strategy_example(proof['id'])
                        st.rerun()

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'strategies'
        
    if st.session_state['page'] == 'strategies':
        show_strategies_page()
    elif st.session_state['page'] == 'gallery':
        show_gallery_page()

if __name__ == "__main__":
    main()
