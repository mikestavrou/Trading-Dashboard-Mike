import streamlit as st
import pandas as pd
from PIL import Image
import os
from database import (
    init_db, get_all_strategies, add_strategy, 
    get_strategy_examples, add_strategy_example, delete_strategy_example,
    get_all_trades, add_trade, delete_trade, delete_strategy,
    get_daily_limit, set_daily_limit
)
from utils import (
    inject_custom_css, save_uploaded_file, save_pil_image, 
    save_audio_file, extract_ticker_from_image, 
    get_market_condition
)
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
    # =====================================================
    # PRE-TRADE CHECK  (hidden behind a toggle button)
    # =====================================================
    all_trades_df = get_all_trades()
    strats_df = get_all_strategies()

    # ── Page title ──────────────────────────────────────────
    st.markdown("""
        <div style='text-align:center;padding:18px 0 10px 0;'>
            <div style='font-size:13px;font-weight:700;letter-spacing:4px;
                        color:#475569;text-transform:uppercase;margin-bottom:4px;'>Mike's</div>
            <div style='font-size:38px;font-weight:900;letter-spacing:3px;
                        color:#e2e8f0;line-height:1;'>TRADING JOURNAL</div>
            <div style='width:60px;height:2px;background:linear-gradient(90deg,transparent,#22c55e,transparent);
                        margin:10px auto 0 auto;'></div>
        </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # SCROLLABLE CALENDAR BAR
    # =====================================================
    import calendar as _cal
    from datetime import date as _date, timedelta as _td

    _today = _date.today()
    _year, _month = _today.year, _today.month
    _days_in_month = _cal.monthrange(_year, _month)[1]
    _day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    # Build per-day lookup from trades
    _daily = {}
    if not all_trades_df.empty and 'entry_date' in all_trades_df.columns:
        for _, tr in all_trades_df.iterrows():
            d = str(tr.get('entry_date', ''))[:10]
            if d.startswith(f"{_year}-{_month:02d}"):
                if d not in _daily:
                    _daily[d] = {'count': 0, 'pnl': 0.0}
                _daily[d]['count'] += 1
                _daily[d]['pnl'] += float(tr.get('pnl', 0) or 0)

    # Build day cards HTML
    _cards = []
    for day_num in range(1, _days_in_month + 1):
        _d = _date(_year, _month, day_num)
        _key = _d.strftime('%Y-%m-%d')
        _is_today = (_d == _today)
        _dow = _day_names[_d.weekday()]
        _info = _daily.get(_key, None)

        _pnl_str = ""
        _trades_str = ""
        _pnl_color = "#64748b"
        if _info:
            _pnl = _info['pnl']
            _pnl_color = "#4ade80" if _pnl >= 0 else "#f87171"
            _pnl_str = f"<div style='color:{_pnl_color};font-size:{'12px' if _is_today else '10px'};font-weight:700;margin-top:2px;'>{'+'if _pnl>=0 else ''}${_pnl:.0f}</div>"
            _trades_str = f"<div style='color:#94a3b8;font-size:{'10px' if _is_today else '9px'};'>{_info['count']} trade{'s' if _info['count']!=1 else ''}</div>"
        else:
            _trades_str = f"<div style='color:#334155;font-size:{'10px' if _is_today else '9px'};'>—</div>"

        if _is_today:
            _card = (
                f"<div id='cal-today' style='flex:0 0 auto;display:flex;flex-direction:column;"
                f"align-items:center;justify-content:center;"
                f"width:120px;min-height:140px;border-radius:16px;"
                f"background:rgba(56,189,248,0.12);border:1.5px solid #38bdf8;"
                f"box-shadow:0 0 18px rgba(56,189,248,0.28);padding:14px 8px;margin:0 6px;'>"
                f"<div style='color:#7dd3fc;font-size:11px;font-weight:700;letter-spacing:1.2px;margin-bottom:4px;'>{_dow}</div>"
                f"<div style='color:#e2e8f0;font-size:48px;font-weight:800;line-height:1;'>{day_num}</div>"
                f"{_trades_str}{_pnl_str}</div>"
            )
        else:
            _future = _d > _today
            _bg = "rgba(15,23,42,0.4)" if not _future else "rgba(15,23,42,0.2)"
            _border = "rgba(255,255,255,0.05)"
            _num_color = "#94a3b8" if not _future else "#334155"
            _card = (
                f"<div style='flex:0 0 auto;display:flex;flex-direction:column;"
                f"align-items:center;justify-content:center;"
                f"width:64px;min-height:80px;border-radius:10px;"
                f"background:{_bg};border:1px solid {_border};"
                f"padding:6px 4px;margin:0 3px;'>"
                f"<div style='color:#475569;font-size:9px;font-weight:600;letter-spacing:0.8px;margin-bottom:1px;'>{_dow}</div>"
                f"<div style='color:{_num_color};font-size:24px;font-weight:700;line-height:1;'>{day_num}</div>"
                f"{_trades_str}{_pnl_str}</div>"
            )
        _cards.append(_card)

    _month_name = _today.strftime('%B %Y')
    _cards_html = "".join(_cards)

    st.markdown(f"""
        <div style="margin-bottom:18px;">
            <div style="color:#475569;font-size:11px;font-weight:700;letter-spacing:1.5px;
                        text-transform:uppercase;margin-bottom:8px;padding-left:2px;">
                {_month_name}
            </div>
            <div id="cal-scroll" style="display:flex;flex-direction:row;overflow-x:auto;
                        padding:8px 4px 12px 4px;gap:0px;
                        scrollbar-width:thin;scrollbar-color:#1e293b transparent;">
                {_cards_html}
            </div>
        </div>
        <script>
            (function() {{
                var el = document.getElementById('cal-today');
                if (el) {{
                    el.scrollIntoView({{behavior:'smooth', block:'nearest', inline:'center'}});
                }}
            }})();
        </script>
        <style>
            #cal-scroll::-webkit-scrollbar {{ height: 3px; }}
            #cal-scroll::-webkit-scrollbar-track {{ background: transparent; }}
            #cal-scroll::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 99px; }}
        </style>
    """, unsafe_allow_html=True)


    # ── DAILY LOSS LIMIT — set once per day from the calendar, then locked ──
    from datetime import datetime as _dt
    _today_str = _dt.now().date().strftime('%Y-%m-%d')
    _locked_limit = get_daily_limit(_today_str)  # None if not set yet
    # Always ensure session key exists so downstream code never gets a KeyError
    st.session_state.setdefault('max_daily_loss', _locked_limit if _locked_limit else 10.0)

    # Real market data — cached per session, refreshed on "Refresh" button
    if 'gk_vol' not in st.session_state:
        with st.spinner("Fetching live market data…"):
            vol_ok, grad_ok, gk_vol, gk_avg, gk_grad, api_err = get_market_condition()
        st.session_state['gk_vol']      = gk_vol
        st.session_state['gk_avg_vol']  = gk_avg
        st.session_state['gk_grad']     = gk_grad
        st.session_state['gk_api_err']  = api_err
        st.session_state['gk_vol_ok']   = vol_ok
        st.session_state['gk_grad_ok']  = grad_ok

    gk_vol       = st.session_state['gk_vol']
    gk_avg       = st.session_state['gk_avg_vol']
    gk_grad      = st.session_state['gk_grad']
    api_err      = st.session_state.get('gk_api_err', '')
    auto_vol_pass  = st.session_state.get('gk_vol_ok', False)
    # Grad: -1 means no Dune key — treat as not-configured (fail but soft)
    auto_grad_pass = st.session_state.get('gk_grad_ok', False)

    from datetime import datetime
    today_str = datetime.now().date().strftime('%Y-%m-%d')
    if not all_trades_df.empty:
        today_trades = all_trades_df[all_trades_df['entry_date'] == today_str]
        daily_pnl = today_trades['pnl'].sum() if not today_trades.empty else 0.0
    else:
        daily_pnl = 0.0
    max_daily_loss = st.session_state['max_daily_loss']
    daily_loss_ok = daily_pnl > -max_daily_loss

    # Session state for manual checks
    for key in ['pf_strategy', 'pf_setup', 'pf_rug']:
        if key not in st.session_state:
            st.session_state[key] = False if key != 'pf_strategy' else None

    # ─── TOGGLE BUTTON ───────────────────────────────────
    strat_chosen = st.session_state['pf_strategy'] is not None
    quick_passes = sum([auto_vol_pass, auto_grad_pass, daily_loss_ok,
                        strat_chosen, st.session_state['pf_setup'],
                        st.session_state['pf_rug']])
    all_pass = quick_passes == 6

    pill_color = "#22c55e" if all_pass else ("#f59e0b" if quick_passes >= 3 else "#ef4444")
    pill_text  = "ALL CLEAR" if all_pass else f"{quick_passes}/6"

    st.markdown(f"""
        <style>
        input[type="checkbox"] {{ width: 22px !important; height: 22px !important; cursor: pointer; }}
        div[data-testid="stCheckbox"] label p {{ font-size: 16px !important; }}
        </style>
    """, unsafe_allow_html=True)

    sub_label = "ALL CLEAR ✓" if all_pass else f"{quick_passes}/6 CHECKS PASSED"
    sub_color = '#4ade80' if all_pass else '#94a3b8'
    pf_open = st.session_state.get('pf_open', False)

    # ── TRADE button via stylable_container ──────────────────────────────────
    # stylable_container scopes CSS to ONLY this container — no other buttons affected
    from streamlit_extras.stylable_container import stylable_container

    with stylable_container(
        key="trade_btn_container",
        css_styles=f"""
            button {{
                background: linear-gradient(135deg, rgba(15,23,42,0.97) 0%, rgba(5,46,22,0.7) 100%) !important;
                border: 2px solid rgba(34,197,94,0.55) !important;
                border-radius: 20px !important;
                min-height: 155px !important;
                width: 100% !important;
                padding: 28px 0 20px 0 !important;
                box-shadow: 0 0 40px rgba(34,197,94,0.12), inset 0 0 50px rgba(34,197,94,0.04) !important;
                transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
                outline: none !important;
            }}
            button:hover {{
                background: linear-gradient(135deg, rgba(15,23,42,0.97) 0%, rgba(5,46,22,0.7) 100%) !important;
                box-shadow: 0 0 70px rgba(34,197,94,0.35), inset 0 0 50px rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.85) !important;
            }}
            button:active, button:focus, button:focus-visible {{
                background: linear-gradient(135deg, rgba(15,23,42,0.97) 0%, rgba(5,46,22,0.7) 100%) !important;
                box-shadow: 0 0 25px rgba(34,197,94,0.15) !important;
                border-color: rgba(34,197,94,0.6) !important;
                outline: none !important;
            }}
            button p {{
                font-size: 13px !important;
                font-weight: 600 !important;
                letter-spacing: 3px !important;
                color: {sub_color} !important;
                white-space: pre-line !important;
                line-height: 2 !important;
                margin: 0 !important;
                text-transform: uppercase !important;
            }}
            button p::first-line {{
                font-size: 50px !important;
                font-weight: 900 !important;
                letter-spacing: 10px !important;
                color: #22c55e !important;
                text-shadow: 0 0 30px rgba(34,197,94,0.6), 0 0 60px rgba(34,197,94,0.3) !important;
                font-family: 'Space Grotesk', sans-serif !important;
                line-height: 1.1 !important;
            }}
        """,
    ):
        if st.button(f"TRADE\n{sub_label}", key="preflight_toggle", use_container_width=True):
            st.session_state['pf_open'] = not pf_open
            st.rerun()

    pf_open = st.session_state.get('pf_open', False)

    # ─── CHECKLIST PANEL (only shown when open) ──────────
    if pf_open:
        with st.container():
            st.markdown("<br>", unsafe_allow_html=True)

            # ── Daily Loss Limit (set once, locked for the day) ──
            if _locked_limit is None:
                st.markdown("""
                    <div style='background:rgba(15,23,42,0.7);border:1px solid rgba(251,191,36,0.3);
                                border-radius:12px;padding:14px 18px;margin-bottom:12px;
                                display:flex;align-items:center;gap:12px;flex-wrap:wrap;'>
                        <div style='color:#fbbf24;font-size:13px;font-weight:700;letter-spacing:0.5px;flex:1 1 180px;'>
                            SET TODAY'S LOSS LIMIT
                        </div>
                        <div style='color:#64748b;font-size:12px;flex:2 1 240px;'>
                            Once confirmed, it cannot be changed for the rest of the day.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                _lcol, _bcol = st.columns([3, 1])
                with _lcol:
                    _input_limit = st.number_input(
                        "Max daily loss ($)", min_value=0.0, value=0.0,
                        step=5.0, key="daily_limit_input", label_visibility="collapsed"
                    )
                with _bcol:
                    if st.button("Lock it in", key="lock_limit_btn", use_container_width=True):
                        set_daily_limit(_today_str, _input_limit)
                        st.session_state['max_daily_loss'] = _input_limit
                        st.rerun()
            else:
                st.session_state['max_daily_loss'] = _locked_limit
                st.markdown(f"""
                    <div style='background:rgba(15,23,42,0.5);border:1px solid rgba(34,197,94,0.25);
                                border-radius:12px;padding:12px 18px;margin-bottom:12px;
                                display:flex;align-items:center;justify-content:space-between;'>
                        <div>
                            <div style='color:#94a3b8;font-size:11px;font-weight:600;letter-spacing:1px;'>TODAY'S LOSS LIMIT</div>
                            <div style='color:#4ade80;font-size:22px;font-weight:800;margin-top:2px;'>${_locked_limit:.0f}</div>
                        </div>
                        <div style='background:rgba(34,197,94,0.12);color:#4ade80;font-size:11px;
                                    font-weight:700;letter-spacing:1.2px;padding:5px 12px;
                                    border-radius:20px;border:1px solid rgba(34,197,94,0.3);'>LOCKED</div>
                    </div>
                """, unsafe_allow_html=True)

            # Progress bar
            pct = quick_passes / 6
            bar_color = "#22c55e" if all_pass else ("#f59e0b" if pct >= 0.5 else "#ef4444")
            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:#64748b; font-size:13px;">Progress</span>
                    <span style="color:{bar_color}; font-weight:700; font-size:13px;">{quick_passes}/6 passed</span>
                </div>
                <div style="background:rgba(255,255,255,0.06); border-radius:999px; height:8px; overflow:hidden; margin-bottom:20px;">
                    <div style="background:{bar_color}; width:{pct*100:.0f}%; height:100%; border-radius:999px; box-shadow:0 0 8px {bar_color};"></div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

            # --- Row 1: Automatic Checks ---
            st.markdown("<div style='color:#cbd5e1; font-size:14px; font-weight:800; letter-spacing:1px; margin-bottom:12px;'>AUTOMATIC CHECKS</div>", unsafe_allow_html=True)
            cols_auto = st.columns(3)
            
            st.markdown("""
            <style>
                /* Base cube styling */
                .cube-base {
                    border-radius: 16px;
                    padding: 24px;
                    min-height: 160px;
                    width: 100%;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    position: relative;
                }
                
                /* Container to hold left/right perfectly centered */
                .cube-content-wrapper {
                    display: flex;
                    flex-direction: row;
                    justify-content: space-between;
                    align-items: center;
                    width: 100%;
                    height: 100%;
                }
                
                /* Left side textual content */
                .cube-left-block {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                    text-align: left;
                    justify-content: center;
                    width: 65%;
                    height: 100%;
                }
                
                /* Right side interactive/badge content */
                .cube-right-block {
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    width: 35%;
                    height: 100%;
                }
                
                .cube-title-row {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 8px;
                }
                
                .cube-icon { font-size: 42px; line-height: 1; }
                .cube-title { color: #f8fafc; font-size: 24px; font-weight: 800; letter-spacing: 0.5px; line-height: 1.1; margin: 0; padding: 0;}
                .cube-detail { color: #94a3b8; font-size: 16px; line-height: 1.4; font-weight: 600; margin: 0; padding: 0;}
                
                /* Manual Cube Form Overrides */
                div[data-testid="stCheckbox"] {
                    transform: scale(2.5);
                    transform-origin: center right;
                    display: flex;
                    justify-content: flex-end;
                }
            </style>
            """, unsafe_allow_html=True)

            def auto_cube(col, label, pass_cond, detail, icon):
                c = "#22c55e" if pass_cond else "#ef4444"
                bg = "rgba(34,197,94,0.06)" if pass_cond else "rgba(239,68,68,0.06)"
                badge_lbl = "PASS" if pass_cond else "FAIL"
                badge_bg = f"rgba({34 if pass_cond else 239},{197 if pass_cond else 68},{94 if pass_cond else 68},0.15)"
                
                with col:
                    st.markdown(f"""
                        <div class="cube-base" style="background:{bg}; border:1px solid {c}44;">
                            <div class="cube-content-wrapper">
                                <div class="cube-left-block">
                                    <div class="cube-title-row">
                                        <div class="cube-icon">{icon}</div>
                                        <div class="cube-title">{label}</div>
                                    </div>
                                    <div class="cube-detail">{detail}</div>
                                </div>
                                <div class="cube-right-block">
                                    <div style="background:{badge_bg}; color:{c}; font-size:16px; font-weight:900; letter-spacing:1.5px; padding:12px 20px; border-radius:24px; text-align:center;">{badge_lbl}</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            auto_cube(cols_auto[0], "Volume", auto_vol_pass, f"${gk_vol}M/hr<br>Avg: ${gk_avg}M", "📊")
            
            if gk_grad == -2.0:
                with cols_auto[1]:
                    st.markdown(f"""
                        <div class="cube-base" style="background:rgba(96,165,250,0.06); border:1px solid #60a5fa44;">
                            <div class="cube-content-wrapper">
                                <div class="cube-left-block">
                                    <div class="cube-title-row">
                                        <div class="cube-icon">🎓</div>
                                        <div class="cube-title">Pump Grad</div>
                                    </div>
                                    <div class="cube-detail">Querying Dune...<br>Refresh ~90s</div>
                                </div>
                                <div class="cube-right-block">
                                    <div style="background:rgba(96,165,250,0.15); color:#60a5fa; font-size:14px; font-weight:900; letter-spacing:1px; padding:12px 16px; border-radius:24px; text-align:center;">LOADING</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                auto_cube(cols_auto[1], "Pump Grad", auto_grad_pass, f"Rate: {gk_grad}%<br>Req: >1.2%", "🎓")
                
            daily_loss_ok_now = daily_pnl > -st.session_state['max_daily_loss']
            auto_cube(cols_auto[2], "Daily Loss", daily_loss_ok_now, f"PnL: ${daily_pnl:.0f}<br>Limit: -${st.session_state['max_daily_loss']:.0f}", "🛡️")

            st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)

            # --- Row 2: Manual Checks ---
            st.markdown("<div style='color:#cbd5e1; font-size:14px; font-weight:800; letter-spacing:1px; margin-bottom:12px;'>MANUAL CHECKS</div>", unsafe_allow_html=True)
            cols_manual = st.columns(3)
            
            strat_names = strats_df['name'].tolist() if not strats_df.empty else []
            strat_options = ["— Select —"] + strat_names
            saved = st.session_state.get('pf_strategy')
            sel_index = 0
            if saved and saved in strat_options:
                sel_index = strat_options.index(saved)
            strat_chosen = sel_index > 0
            
            from streamlit_extras.stylable_container import stylable_container

            # Strategy Cube
            with cols_manual[0]:
                c = "#22c55e" if strat_chosen else "#ef4444"
                bg = "rgba(34,197,94,0.06)" if strat_chosen else "rgba(239,68,68,0.06)"
                with stylable_container(
                    key="mcube_strat",
                    css_styles=f"""
                        {{
                            background: {bg}; border: 1px solid {c}44; border-radius: 16px; padding: 24px; min-height: 160px; width: 100%;
                            display: grid; grid-template-columns: 1fr auto; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                        }}
                    """
                ):
                    st.markdown("""
                        <div class="cube-left-block">
                            <div class="cube-title-row"><div class="cube-icon">🎯</div><div class="cube-title">Strategy</div></div>
                            <div class="cube-detail">Select edge</div>
                        </div>
                    """, unsafe_allow_html=True)
                    sel = st.selectbox("Strat", strat_options, index=sel_index, key="pf_strategy_sel", label_visibility="collapsed")
                    st.session_state['pf_strategy'] = sel if sel != "— Select —" else None

            chk_reset = st.session_state.get('ptc_reset_count', 0)
            
            # Clean Setup Cube
            with cols_manual[1]:
                c = "#22c55e" if st.session_state['pf_setup'] else "#ef4444"
                bg = "rgba(34,197,94,0.06)" if st.session_state['pf_setup'] else "rgba(239,68,68,0.06)"
                with stylable_container(
                    key="mcube_setup",
                    css_styles=f"""
                        {{
                            background: {bg}; border: 1px solid {c}44; border-radius: 16px; padding: 24px; min-height: 160px; width: 100%;
                            display: grid; grid-template-columns: 1fr auto; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                        }}
                    """
                ):
                    st.markdown("""
                        <div class="cube-left-block">
                            <div class="cube-title-row"><div class="cube-icon">🧠</div><div class="cube-title">Clean Setup</div></div>
                            <div class="cube-detail">No FOMO</div>
                        </div>
                    """, unsafe_allow_html=True)
                    c5 = st.checkbox("Confirm Setup", value=st.session_state['pf_setup'], key=f"chk_setup_{chk_reset}", label_visibility="collapsed")
                    st.session_state['pf_setup'] = c5

            # Rugcheck Cube
            with cols_manual[2]:
                c = "#22c55e" if st.session_state['pf_rug'] else "#ef4444"
                bg = "rgba(34,197,94,0.06)" if st.session_state['pf_rug'] else "rgba(239,68,68,0.06)"
                with stylable_container(
                    key="mcube_rug",
                    css_styles=f"""
                        {{
                            background: {bg}; border: 1px solid {c}44; border-radius: 16px; padding: 24px; min-height: 160px; width: 100%;
                            display: grid; grid-template-columns: 1fr auto; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                        }}
                    """
                ):
                    st.markdown("""
                        <div class="cube-left-block">
                            <div class="cube-title-row"><div class="cube-icon">🔍</div><div class="cube-title">Rugcheck</div></div>
                            <div class="cube-detail">Token clean</div>
                        </div>
                    """, unsafe_allow_html=True)
                    c6 = st.checkbox("Confirm Rugcheck", value=st.session_state['pf_rug'], key=f"chk_rug_{chk_reset}", label_visibility="collapsed")
                    st.session_state['pf_rug'] = c6

            st.markdown("<br>", unsafe_allow_html=True)


            # Recalculate after widget interactions
            all_pass_final = all([auto_vol_pass, auto_grad_pass, daily_loss_ok_now,
                                  strat_chosen, st.session_state['pf_setup'],
                                  st.session_state['pf_rug']])

            if all_pass_final:
                st.markdown("""
                    <div style="background:linear-gradient(135deg,rgba(34,197,94,0.12),rgba(21,128,61,0.2));
                         border:1px solid #22c55e66; border-radius:14px; padding:22px 24px;
                         text-align:center; margin-top:8px;">
                        <div style="color:#4ade80; font-size:20px; font-weight:800;
                                    letter-spacing:2.5px; margin-bottom:6px;">CLEAR TO TRADE</div>
                        <div style="color:#86efac; font-size:13px;">All 6 checkpoints passed</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                fails = []
                for lbl, passing in [
                    ("Solana Volume", auto_vol_pass),
                    ("Pump.fun Graduation Rate", auto_grad_pass),
                    ("Daily Loss Limit", daily_loss_ok_now),
                    ("Strategy Selected", strat_chosen),
                    ("Clean Setup", st.session_state['pf_setup']),
                    ("Rugcheck Done", st.session_state['pf_rug']),
                ]:
                    if not passing:
                        fails.append(f"<span style='display:inline-block;background:rgba(239,68,68,0.12);"
                                     f"color:#fca5a5;font-size:12px;padding:3px 10px;border-radius:20px;"
                                     f"border:1px solid #ef444444;margin:3px 4px;'>{lbl}</span>")
                st.markdown(f"""
                    <div style="background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(185,28,28,0.18));
                         border:1px solid #ef444466; border-radius:14px; padding:22px 24px;
                         text-align:center; margin-top:8px;">
                        <div style="color:#f87171; font-size:20px; font-weight:800;
                                    letter-spacing:2.5px; margin-bottom:10px;">NOT READY</div>
                        <div style="line-height:2.2;">{"".join(fails)}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button("Refresh Market Data", use_container_width=True):
                    for k in ['gk_vol', 'gk_avg_vol', 'gk_grad',
                              'gk_api_err', 'gk_vol_ok', 'gk_grad_ok']:
                        st.session_state.pop(k, None)
                    st.rerun()
            with col_r2:
                if st.button("Reset All Checks", use_container_width=True):
                    st.session_state['pf_setup'] = False
                    st.session_state['pf_rug'] = False
                    st.session_state['pf_strategy'] = None
                    st.rerun()

            # ─── LOG TRADE (Full Gallery-style form) ──────────
            st.markdown("---")
            st.subheader("📝 Log This Trade")

            # Resolve strategy id from selection
            ptc_strategy_id = None
            if strat_chosen and not strats_df.empty:
                matched = strats_df[strats_df['name'] == st.session_state.get('pf_strategy')]
                if not matched.empty:
                    ptc_strategy_id = int(matched.iloc[0]['id'])

            ptc_reset = st.session_state.get('ptc_reset_count', 0)
            col_form1, col_form2 = st.columns([1, 1])

            with col_form1:
                sym_key = f"ptc_sym_{ptc_reset}"
                default_sym = st.session_state.get('ptc_ocr_symbol', '')
                ptc_symbol   = st.text_input("Symbol / Ticker", value=default_sym, key=sym_key)
                ptc_direction = st.selectbox("Direction", ["Long", "Short"], key=f"ptc_dir_{ptc_reset}")
                sub1, sub2 = st.columns(2)
                with sub1: ptc_entry = st.date_input("Entry Date", key=f"ptc_entry_{ptc_reset}")
                with sub2: ptc_exit  = st.date_input("Exit Date (Optional)", value=None, key=f"ptc_exit_{ptc_reset}")
                ptc_pnl = st.number_input("PnL ($)", value=0.0, step=10.0, key=f"ptc_pnl_{ptc_reset}")

            with col_form2:
                st.markdown("Paste the chart screenshot:")
                # Key includes ptc_reset so the paste button clears its own image_data on submit
                paste_ptc = paste_image_button("Paste Image", background_color="#161b22",
                                               hover_background_color="#30363D", key=f"ptc_paste_{ptc_reset}")
                if paste_ptc.image_data is not None:
                    st.session_state['ptc_img'] = paste_ptc.image_data

                cached_ptc = st.session_state.get('ptc_img')
                if cached_ptc is not None:
                    st.image(cached_ptc, caption="Chart Preview", use_container_width=True)
                    img_hash = hash(cached_ptc.tobytes()[:5000])
                    if st.session_state.get('ptc_last_hash') != img_hash:
                        st.session_state['ptc_last_hash'] = img_hash
                        with st.spinner("Scanning chart for ticker..."):
                            extracted = extract_ticker_from_image(cached_ptc, debug=False)
                            if extracted:
                                st.session_state['ptc_ocr_symbol'] = extracted
                                st.session_state['ptc_reset_count'] = ptc_reset + 1
                            st.rerun()

                ptc_notes = st.text_area("Notes / Lessons Learned",
                                         value=st.session_state.get('ptc_notes_val', ''),
                                         height=100, key=f"ptc_notes_{ptc_reset}")
                st.write("Voice Note (Optional):")
                ptc_audio = audio_recorder(text="Click to record", recording_color="#ef4444",
                                           neutral_color="#3b82f6", icon_name="microphone",
                                           icon_size="2x", key=f"ptc_audio_{ptc_reset}")

            if st.button("Submit Trade", key=f"ptc_submit_{ptc_reset}", use_container_width=True):
                if not ptc_symbol:
                    st.error("Symbol is required.")
                else:
                    img_path = save_pil_image(cached_ptc, prefix=f"trade_{ptc_symbol}") if cached_ptc else None
                    audio_path = save_audio_file(ptc_audio, prefix=ptc_symbol) if ptc_audio else None
                    add_trade(ptc_symbol, str(ptc_entry),
                              str(ptc_exit) if ptc_exit else None,
                              ptc_direction, ptc_strategy_id, ptc_pnl,
                              img_path, ptc_notes, audio_path)
                    st.success(f"✅ Trade logged: {ptc_direction} {ptc_symbol} · ${ptc_pnl:.2f} under '{sel if strat_chosen else 'No Strategy'}'")
                    # Reset form fields
                    st.session_state['ptc_ocr_symbol'] = ''
                    st.session_state['ptc_reset_count'] = ptc_reset + 1
                    st.session_state['ptc_last_hash'] = None
                    st.session_state['ptc_img'] = None
                    # Also reset the manual checkboxes so you're clean for the next trade
                    st.session_state['pf_setup'] = False
                    st.session_state['pf_rug'] = False
                    st.rerun()

    st.markdown("---")

    st.markdown("---")

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
