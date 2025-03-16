import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from components.header import render_header
from components.sidebar import render_sidebar
import markdown
import os
from datetime import datetime

def get_saved_report_list():
    """Get list of saved securities reports."""
    reports_dir = os.path.join("data", "securities_reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)
        return []
    
    reports = []
    for file in os.listdir(reports_dir):
        if file.endswith('.json'):
            reports.append(file.replace('.json', ''))
    
    return sorted(reports, reverse=True)  # Most recent first

def save_report(report_data, name=None):
    """Save a securities report for future reference."""
    reports_dir = os.path.join("data", "securities_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate report name if not provided
    if not name:
        name = f"securities_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save report data
    with open(os.path.join(reports_dir, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
    
    return name

def securities_page():
    """Render the securities analysis page."""
    render_header("ניתוח ניירות ערך", "ניתוח מקיף של ניירות ערך לפי ISIN")
    sidebar_state = render_sidebar()
    
    # Main content
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("ניתוח ניירות ערך לפי ISIN")
    
    # Create tabs for different workflows
    main_tabs = st.tabs(["ניתוח חדש", "דוחות שמורים", "תוצאות"])
    
    with main_tabs[0]:  # New Analysis tab
        # File upload for bank reports with multi-file support
        uploaded_files = st.file_uploader(
            "העלה דוחות בנק (PDF, Excel, CSV)", 
            type=["pdf", "xlsx", "xls", "csv", "json"], 
            accept_multiple_files=True,
            help="ניתן להעלות מספר קבצים במקביל, כולל דוחות מבנקים שונים"
        )
        
        # Show upload feedback 
        if uploaded_files:
            st.success(f"הועלו {len(uploaded_files)} קבצים")
            
            # Process button
            if st.button("עבד קבצים", type="primary"):
                with st.spinner("מעבד קבצים..."):
                    # Process each file (placeholder for now)
                    all_securities = []
                    
                    for uploaded_file in uploaded_files:
                        try:
                            if uploaded_file.name.endswith(('.csv')):
                                data = pd.read_csv(uploaded_file)
                                securities_data = data.to_dict('records')
                            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                                data = pd.read_excel(uploaded_file)
                                securities_data = data.to_dict('records')
                            elif uploaded_file.name.endswith('.json'):
                                securities_data = json.load(uploaded_file)
                            else:
                                # For PDFs, we would need more complex processing
                                st.warning(f"Processing {uploaded_file.name}... PDF processing not implemented yet.")
                                continue
                                
                            # Add source bank information based on filename
                            bank_name = uploaded_file.name.split('.')[0]
                            for item in securities_data:
                                if "bank" not in item:
                                    item["bank"] = bank_name
                                                        
                            all_securities.extend(securities_data)
                            
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    
                    if all_securities:
                        st.session_state.securities_data = all_securities
                        st.success(f"Processed {len(all_securities)} security records from {len(uploaded_files)} files")
        
        # Email connection
        with st.expander("חיבור אימייל לקבלה אוטומטית של דוחות"):
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("כתובת אימייל", key="email_input")
            with col2:
                email_provider = st.selectbox("ספק", ["Gmail", "Outlook", "Yahoo", "אחר"])
            
            password = st.text_input("סיסמה לחשבון", type="password")
            
            adv_col1, adv_col2 = st.columns(2)
            with adv_col1:
                folder = st.text_input("תיקיית דואר לסריקה", value="INBOX")
            with adv_col2:
                search_term = st.text_input("מונח חיפוש", value="דוח השקעות")
                
            if st.button("התחבר וסרוק אימייל"):
                with st.spinner("מתחבר לאימייל..."):
                    # This would be actual email connection code
                    st.info("יכולת חיבור לאימייל תהיה זמינה בגרסה הבאה של המערכת.")
                
        # Manual entry section
        with st.expander("הזנה ידנית של נתוני ניירות ערך"):
            # Create form for manual entry
            with st.form("securities_form"):
                col1, col2 = st.columns(2)
                with col1:
                    security_name = st.text_input("שם נייר הערך")
                    isin = st.text_input("ISIN")
                    bank = st.text_input("בנק / חשבון")
                
                with col2:
                    price = st.number_input("מחיר", min_value=0.0, format="%.2f")
                    quantity = st.number_input("כמות", min_value=0)
                    market_value = st.number_input("שווי שוק", min_value=0.0, format="%.2f")
                
                submitted = st.form_submit_button("הוסף נייר ערך")
                
                if submitted and isin:
                    if 'securities_data' not in st.session_state:
                        st.session_state.securities_data = []
                    
                    # Add new security
                    st.session_state.securities_data.append({
                        'security_name': security_name,
                        'isin': isin,
                        'price': price,
                        'quantity': quantity,
                        'bank': bank,
                        'market_value': market_value if market_value > 0 else price * quantity
                    })
                    
                    st.success(f"נייר הערך {security_name} נוסף בהצלחה!")
        
        # Sample data section
        if st.button("טען נתוני דוגמה"):
            # Enhanced sample data
            st.session_state.securities_data = [
                {
                    "security_name": "Apple Inc.", 
                    "isin": "US0378331005", 
                    "price": 150.82, 
                    "quantity": 50, 
                    "bank": "Bank A", 
                    "market_value": 7541.00
                },
                {
                    "security_name": "Microsoft Corp.", 
                    "isin": "US5949181045", 
                    "price": 290.35, 
                    "quantity": 30, 
                    "bank": "Bank A", 
                    "market_value": 8710.50
                },
                {
                    "security_name": "Apple Inc.", 
                    "isin": "US0378331005", 
                    "price": 151.20, 
                    "quantity": 25, 
                    "bank": "Bank B", 
                    "market_value": 3780.00
                },
                {
                    "security_name": "Amazon.com Inc.", 
                    "isin": "US0231351067", 
                    "price": 128.55, 
                    "quantity": 40, 
                    "bank": "Bank B", 
                    "market_value": 5142.00
                },
                {
                    "security_name": "Tesla Inc.", 
                    "isin": "US88160R1014", 
                    "price": 235.45, 
                    "quantity": 15, 
                    "bank": "Bank A", 
                    "market_value": 3531.75
                },
                {
                    "security_name": "Meta Platforms Inc.", 
                    "isin": "US30303M1027", 
                    "price": 320.12, 
                    "quantity": 12, 
                    "bank": "Bank C", 
                    "market_value": 3841.44
                },
                {
                    "security_name": "Tesla Inc.", 
                    "isin": "US88160R1014", 
                    "price": 236.10, 
                    "quantity": 10, 
                    "bank": "Bank C", 
                    "market_value": 2361.00
                }
            ]
            st.success("נטענו נתוני דוגמה")
    
    with main_tabs[1]:  # Saved Reports tab
        saved_reports = get_saved_report_list()
        
        if not saved_reports:
            st.info("אין דוחות שמורים. הפק דוח חדש כדי לשמור אותו.")
        else:
            selected_report = st.selectbox("בחר דוח שמור", saved_reports)
            
            if selected_report and st.button("טען דוח"):
                try:
                    # Load saved report
                    report_path = os.path.join("data", "securities_reports", f"{selected_report}.json")
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                        
                    # Set to session state
                    st.session_state.securities_analysis = report_data
                    
                    # Extract securities data if available
                    if "securities_data" in report_data:
                        st.session_state.securities_data = report_data["securities_data"]
                    
                    st.success(f"הדוח '{selected_report}' נטען בהצלחה")
                except Exception as e:
                    st.error(f"שגיאה בטעינת הדוח: {str(e)}")
    
    with main_tabs[2]:  # Results tab
        if 'securities_data' in st.session_state and st.session_state.securities_data:
            # Display the loaded securities data
            st.subheader("נתוני ניירות ערך")
            
            df = pd.DataFrame(st.session_state.securities_data)
            
            # Add filtering options
            col1, col2 = st.columns(2)
            with col1:
                if 'bank' in df.columns:
                    banks = ['הכל'] + sorted(df['bank'].unique().tolist())
                    bank_filter = st.selectbox("סינון לפי בנק", banks)
                    
                    if bank_filter != 'הכל':
                        df = df[df['bank'] == bank_filter]
            
            with col2:
                if 'isin' in df.columns:
                    isins = ['הכל'] + sorted(df['isin'].unique().tolist())
                    isin_filter = st.selectbox("סינון לפי ISIN", isins)
                    
                    if isin_filter != 'הכל':
                        df = df[df['isin'] == isin_filter]
            
            # Display filtered dataframe
            st.dataframe(df, use_container_width=True)
            
            # Analysis options
            st.subheader("אפשרויות ניתוח")
            
            analysis_col1, analysis_col2 = st.columns(2)
            with analysis_col1:
                analysis_type = st.selectbox("סוג ניתוח", [
                    "ניתוח מאוחד לפי ISIN",
                    "ניתוח השוואתי בין בנקים",
                    "ניתוח ביצועים",
                    "זיהוי פערי מחירים"
                ])
            
            with analysis_col2:
                if "ביצועים" in analysis_type:
                    time_period = st.selectbox("תקופת זמן", [
                        "שבועי", "חודשי", "רבעוני", "שנתי"
                    ])
            
            # Run analysis if we have the agent runner
            if 'agent_runner' in st.session_state and st.session_state.agent_runner:
                if st.button("נתח ניירות ערך", type="primary"):
                    with st.spinner("מנתח..."):
                        try:
                            # Run analysis
                            securities_analysis = st.session_state.agent_runner.analyze_securities(
                                st.session_state.securities_data
                            )
                            
                            if securities_analysis:
                                # Add original data for reference
                                securities_analysis["securities_data"] = st.session_state.securities_data
                                
                                # Store analysis in session
                                st.session_state.securities_analysis = securities_analysis
                                
                                # Save the report
                                report_name = save_report(securities_analysis)
                                
                                # Display basic analysis results
                                st.success(f"ניתוח הושלם: {securities_analysis['total_isins']} ניירות ערך, "
                                        f"סך שווי התיק: ${securities_analysis['total_portfolio_value']:,.2f}")
                                
                                # Switch to results tab
                                st.experimental_rerun()
                            else:
                                st.error("לא התקבלו תוצאות ניתוח")
                        except Exception as e:
                            st.error(f"שגיאה בניתוח: {str(e)}")
            else:
                st.warning("נדרש מפתח API של Gemini כדי לנתח ניירות ערך. הזן את המפתח בסרגל הצד.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show analysis results if available
    if 'securities_analysis' in st.session_state and st.session_state.securities_analysis:
        st.markdown('<div class="startup-card">', unsafe_allow_html=True)
        st.subheader("תוצאות ניתוח")
        
        # Create tabs for different views
        analysis_tabs = st.tabs(["סיכום", "הבדלי מחירים", "ניירות ערך לפי שווי", "התפלגות", "דוח מלא"])
        
        analysis = st.session_state.securities_analysis
        
        with analysis_tabs[0]:  # Summary tab
            # Display summary metrics in a better layout
            col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
            
            with col1:
                st.metric(
                    "סך שווי התיק", 
                    f"${analysis['total_portfolio_value']:,.2f}", 
                    delta=None
                )
            
            with col2:
                st.metric(
                    "מספר ניירות ערך", 
                    analysis['total_isins'],
                    delta=None
                )
            
            with col3:
                # Count unique banks
                all_banks = set()
                for isin, data in analysis['securities'].items():
                    all_banks.update(data['banks'])
                
                st.metric(
                    "מספר בנקים/חשבונות", 
                    len(all_banks),
                    delta=None
                )
            
            with col4:
                discrepancies = len([data for isin, data in analysis['securities'].items() 
                                if data.get('price_discrepancies', False)])
                
                st.metric(
                    "הבדלי מחירים",
                    f"{discrepancies} ניירות ערך",
                    delta=f"{(discrepancies / analysis['total_isins'] * 100):.1f}%" if analysis['total_isins'] > 0 else None,
                    delta_color="inverse"
                )
            
            # Summary table of securities
            st.subheader("סיכום ניירות ערך")
            summary_data = []
            
            for isin, data in analysis['securities'].items():
                summary_data.append({
                    "ISIN": isin,
                    "שם נייר": data['security_name'],
                    "שווי כולל ($)": f"${data['total_value']:,.2f}",
                    "בנקים/חשבונות": ", ".join(data['banks']),
                    "הבדלי מחירים": "✓" if data.get('price_discrepancies', False) else "✗"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Holdings distribution pie chart
            st.subheader("התפלגות החזקות לפי נייר ערך")
            
            fig = px.pie(
                values=[data['total_value'] for isin, data in analysis['securities'].items()],
                names=[data['security_name'] for isin, data in analysis['securities'].items()],
                hole=0.4,
                labels={"names": "נייר ערך", "values": "שווי ($)"}
            )
            
            fig.update_layout(
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with analysis_tabs[1]:  # Price Discrepancies tab
            # Show price discrepancies
            discrepancies = {isin: data for isin, data in analysis['securities'].items() 
                           if data.get('price_discrepancies', False)}
            
            if discrepancies:
                st.write("ניירות ערך עם הבדלי מחירים בין חשבונות:")
                
                # Create a table for all discrepancies
                discrepancy_data = []
                
                for isin, data in discrepancies.items():
                    discrepancy_data.append({
                        "ISIN": isin,
                        "שם נייר": data['security_name'],
                        "מחיר מינימלי": f"${data['min_price']:.2f}",
                        "מחיר מקסימלי": f"${data['max_price']:.2f}",
                        "פער מחירים": f"{data['price_difference_pct']:.2f}%",
                        "בנקים/חשבונות": ", ".join(data['banks'])
                    })
                
                discrepancy_df = pd.DataFrame(discrepancy_data)
                st.dataframe(discrepancy_df, use_container_width=True)
                
                # Individual details in expanders
                for isin, data in discrepancies.items():
                    with st.expander(f"{data['security_name']} ({isin})"):
                        discrepancy_col1, discrepancy_col2 = st.columns(2)
                        
                        with discrepancy_col1:
                            st.markdown(f"**פער מחירים**: {data['price_difference_pct']:.2f}%")
                            st.markdown(f"**מחיר מינימלי**: ${data['min_price']:.2f}")
                            st.markdown(f"**מחיר מקסימלי**: ${data['max_price']:.2f}")
                        
                        with discrepancy_col2:
                            st.markdown(f"**שווי כולל**: ${data['total_value']:,.2f}")
                            st.markdown(f"**בנקים/חשבונות**: {', '.join(data['banks'])}")
                        
                        # Show all holdings
                        st.subheader("פירוט החזקות")
                        holdings_df = pd.DataFrame(data['holdings'])
                        st.dataframe(holdings_df, use_container_width=True)
                        
                        # Price comparison chart
                        holdings_df_for_chart = pd.DataFrame([
                            {"bank": h.get('bank', 'Unknown'), "price": h.get('price', 0)} 
                            for h in data['holdings']
                        ])
                        
                        fig = px.bar(
                            holdings_df_for_chart,
                            x="bank",
                            y="price",
                            title=f"השוואת מחירים: {data['security_name']}",
                            labels={"bank": "בנק/חשבון", "price": "מחיר ($)"}
                        )
                        
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("לא נמצאו הבדלי מחירים בין החשבונות השונים")
        
        with analysis_tabs[2]:  # Securities by Value tab
            # Show securities sorted by value
            sorted_securities = sorted(
                analysis['securities'].items(), 
                key=lambda x: x[1]['total_value'], 
                reverse=True
            )
            
            # Convert to DataFrame for easier display
            securities_list = []
            for isin, data in sorted_securities:
                securities_list.append({
                    'ISIN': isin,
                    'שם נייר': data['security_name'],
                    'שווי כולל': data['total_value'],
                    'בנקים/חשבונות': ", ".join(data['banks'])
                })
            
            securities_df = pd.DataFrame(securities_list)
            
            # Display formatted dataframe
            st.dataframe(
                securities_df.style.format({
                    'שווי כולל': "${:,.2f}".format
                }),
                use_container_width=True
            )
            
            # Create horizontal bar chart
            fig = go.Figure(go.Bar(
                x=[data['total_value'] for isin, data in sorted_securities],
                y=[data['security_name'] for isin, data in sorted_securities],
                orientation='h',
                marker_color='royalblue'
            ))
            
            fig.update_layout(
                title="ניירות ערך לפי שווי",
                xaxis_title="שווי ($)",
                yaxis_title="נייר ערך",
                height=400 + len(sorted_securities) * 25,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with analysis_tabs[3]:  # Distribution tab
            # Distribution by Bank
            st.subheader("התפלגות החזקות לפי בנק/חשבון")
            
            # Prepare data
            bank_totals = {}
            
            for isin, data in analysis['securities'].items():
                for holding in data['holdings']:
                    bank = holding.get('bank', 'Unknown')
                    market_value = holding.get('market_value', 0)
                    
                    if bank not in bank_totals:
                        bank_totals[bank] = 0
                    
                    bank_totals[bank] += market_value
            
            # Create pie chart for bank distribution
            bank_fig = px.pie(
                values=list(bank_totals.values()),
                names=list(bank_totals.keys()),
                hole=0.4,
                labels={"names": "בנק/חשבון", "values": "שווי ($)"}
            )
            
            bank_fig.update_layout(
                height=450,
                title="התפלגות השקעות לפי בנק/חשבון"
            )
            
            st.plotly_chart(bank_fig, use_container_width=True)
            
            # Create bank comparison bar chart
            st.subheader("השוואת החזקות בין בנקים/חשבונות")
            
            # Prepare data for stacked bar chart
            bank_security_data = []
            
            for isin, data in sorted_securities:
                for holding in data['holdings']:
                    bank_security_data.append({
                        'בנק/חשבון': holding.get('bank', 'Unknown'),
                        'נייר ערך': data['security_name'],
                        'שווי': holding.get('market_value', 0)
                    })
            
            if bank_security_data:
                bank_security_df = pd.DataFrame(bank_security_data)
                
                # Create stacked bar chart
                fig = px.bar(
                    bank_security_df,
                    x='בנק/חשבון',
                    y='שווי',
                    color='נייר ערך',
                    labels={'שווי': 'שווי ($)'},
                    height=500
                )
                
                fig.update_layout(
                    barmode='stack',
                    xaxis={'categoryorder': 'total descending'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with analysis_tabs[4]:  # Full Report tab
            # Generate and display full report
            if st.button("צור דוח מלא", type="primary"):
                with st.spinner("מכין דוח..."):
                    try:
                        report = st.session_state.agent_runner.generate_securities_report(
                            st.session_state.securities_analysis
                        )
                        
                        if report:
                            st.markdown(report, unsafe_allow_html=True)
                            
                            # Offer download options
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="הורד את הדוח כקובץ markdown",
                                    data=report,
                                    file_name="securities_analysis_report.md",
                                    mime="text/markdown"
                                )
                            
                            with col2:
                                st.download_button(
                                    label="הורד כ-HTML",
                                    data=markdown.markdown(report),
                                    file_name="securities_analysis_report.html",
                                    mime="text/html"
                                )
                        else:
                            st.error("לא הצלחנו ליצור דוח")
                    except Exception as e:
                        st.error(f"שגיאה בהכנת הדוח: {str(e)}")
            
            # View previous reports
            with st.expander("צפייה בדוחות קודמים"):
                saved_reports = get_saved_report_list()
                if saved_reports:
                    report_to_view = st.selectbox("בחר דוח לצפייה", saved_reports)
                    
                    if report_to_view and st.button("הצג דוח"):
                        try:
                            report_path = os.path.join("data", "securities_reports", f"{report_to_view}.json")
                            with open(report_path, "r", encoding="utf-8") as f:
                                report_data = json.load(f)
                            
                            if "report_text" in report_data:
                                st.markdown(report_data["report_text"], unsafe_allow_html=True)
                            else:
                                # Generate report from the data
                                report = st.session_state.agent_runner.generate_securities_report(report_data)
                                st.markdown(report, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"שגיאה בטעינת הדוח: {str(e)}")
                else:
                    st.info("אין דוחות שמורים. צור דוח חדש כדי לשמור אותו.")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    securities_page()
