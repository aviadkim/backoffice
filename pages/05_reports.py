import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
import pandas as pd
import altair as alt
import markdown

def render_reports_page():
    render_header("דוחות פיננסיים", "יצירה והצגה של דוחות פיננסיים מקיפים")
    sidebar_state = render_sidebar()
    
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("דוחות פיננסיים")
    
    if 'transactions' not in st.session_state or not st.session_state.transactions:
        st.info("אין נתונים פיננסיים זמינים. נא להעלות ולעבד מסמכים תחילה.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Options for report generation
    report_options = st.selectbox(
        "סוג דוח",
        ["סיכום חודשי", "ניתוח קטגוריות", "ניתוח מגמות", "דוח פיננסי מקיף"]
    )
    
    # Check if we have an agent runner
    has_agent = 'agent_runner' in st.session_state and st.session_state.agent_runner
    
    if st.button("צור דוח", type="primary"):
        with st.spinner("מכין את הדוח..."):
            if report_options == "דוח פיננסי מקיף" and has_agent:
                # Generate comprehensive report using agents
                transactions = st.session_state.transactions
                analysis = st.session_state.get('financial_analysis', {})
                
                # Generate advice if we have analysis
                if analysis:
                    advice = st.session_state.agent_runner.get_financial_advice(analysis)
                else:
                    # Generate analysis first
                    analysis = st.session_state.agent_runner.analyze_finances(transactions)
                    st.session_state.financial_analysis = analysis
                    advice = st.session_state.agent_runner.get_financial_advice(analysis)
                
                # Generate report
                report = st.session_state.agent_runner.generate_report(transactions, analysis, advice)
                
                # Render the markdown report
                if report:
                    st.session_state.current_report = report
                    st.success("הדוח נוצר בהצלחה!")
                else:
                    st.error("שגיאה ביצירת הדוח")
            else:
                # Generate basic reports
                transactions_df = pd.DataFrame(st.session_state.transactions)
                
                if report_options == "סיכום חודשי":
                    generate_monthly_summary(transactions_df)
                elif report_options == "ניתוח קטגוריות":
                    generate_category_analysis(transactions_df)
                elif report_options == "ניתוח מגמות":
                    generate_trend_analysis(transactions_df)
    
    # Display current report if available
    if 'current_report' in st.session_state and st.session_state.current_report:
        st.markdown("## תצוגת דוח")
        # Convert markdown to HTML and display
        import markdown
        html = markdown.markdown(st.session_state.current_report)
        st.markdown(html, unsafe_allow_html=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "הורד כקובץ טקסט",
                st.session_state.current_report,
                file_name="financial_report.md",
                mime="text/markdown"
            )
        with col2:
            # Convert to PDF and offer download (simplified for now)
            st.download_button(
                "הורד כ-PDF",
                st.session_state.current_report,
                file_name="financial_report.pdf",
                mime="application/pdf"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

def generate_monthly_summary(transactions_df):
    """Generate a monthly summary report."""
    if 'date' in transactions_df.columns:
        # Convert date to datetime
        transactions_df['date'] = pd.to_datetime(transactions_df['date'], errors='coerce')
        transactions_df['month'] = transactions_df['date'].dt.strftime('%Y-%m')
        
        # Group by month
        monthly = transactions_df.groupby('month').agg({
            'amount': [
                ('income', lambda x: x[x > 0].sum()),
                ('expenses', lambda x: x[x < 0].sum()),
                ('net', 'sum'),
                ('count', 'count')
            ]
        })
        
        # Flatten multi-level columns
        monthly.columns = ['income', 'expenses', 'net', 'count']
        monthly = monthly.reset_index()
        
        # Create report in markdown
        report = "# סיכום חודשי\n\n"
        report += "## הכנסות והוצאות לפי חודש\n\n"
        
        # Create a table
        report += "| חודש | הכנסות | הוצאות | מאזן נטו | מספר עסקאות |\n"
        report += "| ---- | ------- | ------- | -------- | ------------- |\n"
        
        for _, row in monthly.iterrows():
            report += f"| {row['month']} | ₪{row['income']:,.2f} | ₪{abs(row['expenses']):,.2f} | ₪{row['net']:,.2f} | {row['count']} |\n"
        
        # Add some insights
        report += "\n## תובנות\n\n"
        
        # Find best and worst months
        best_month = monthly.loc[monthly['net'].idxmax()]
        worst_month = monthly.loc[monthly['net'].idxmin()]
        
        report += f"- החודש עם המאזן הטוב ביותר: {best_month['month']} (₪{best_month['net']:,.2f})\n"
        report += f"- החודש עם המאזן הנמוך ביותר: {worst_month['month']} (₪{worst_month['net']:,.2f})\n"
        
        # Calculate averages
        avg_income = monthly['income'].mean()
        avg_expenses = monthly['expenses'].mean()
        
        report += f"- הכנסה חודשית ממוצעת: ₪{avg_income:,.2f}\n"
        report += f"- הוצאה חודשית ממוצעת: ₪{abs(avg_expenses):,.2f}\n"
        
        # Save to session state
        st.session_state.current_report = report
        st.success("הדוח נוצר בהצלחה!")
    else:
        st.error("הנתונים חסרים שדה תאריך")

def generate_category_analysis(transactions_df):
    """Generate a category analysis report."""
    if 'category' in transactions_df.columns and 'amount' in transactions_df.columns:
        # Split into income and expenses
        income_df = transactions_df[transactions_df['amount'] > 0]
        expense_df = transactions_df[transactions_df['amount'] < 0]
        
        # Group by category
        income_by_cat = income_df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        expense_by_cat = expense_df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        
        # Calculate percentages
        income_total = income_by_cat['sum'].sum()
        expense_total = expense_by_cat['sum'].sum()
        
        income_by_cat['percentage'] = income_by_cat['sum'] / income_total * 100
        expense_by_cat['percentage'] = expense_by_cat['sum'] / expense_total * 100
        
        # Sort by amount
        income_by_cat = income_by_cat.sort_values('sum', ascending=False)
        expense_by_cat = expense_by_cat.sort_values('sum', ascending=True)  # Expenses are negative
        
        # Create report
        report = "# ניתוח קטגוריות\n\n"
        
        # Expenses section
        report += "## התפלגות הוצאות לפי קטגוריה\n\n"
        report += "| קטגוריה | סכום | אחוז מסך ההוצאות | מספר עסקאות |\n"
        report += "| ------- | ----- | ---------------- | ------------- |\n"
        
        for _, row in expense_by_cat.iterrows():
            report += f"| {row['category']} | ₪{abs(row['sum']):,.2f} | {row['percentage']:.1f}% | {row['count']} |\n"
        
        # Income section
        report += "\n## התפלגות הכנסות לפי קטגוריה\n\n"
        report += "| קטגוריה | סכום | אחוז מסך ההכנסות | מספר עסקאות |\n"
        report += "| ------- | ----- | ---------------- | ------------- |\n"
        
        for _, row in income_by_cat.iterrows():
            report += f"| {row['category']} | ₪{row['sum']:,.2f} | {row['percentage']:.1f}% | {row['count']} |\n"
        
        # Add insights
        report += "\n## תובנות\n\n"
        
        # Top expense category
        top_expense = expense_by_cat.iloc[0]
        report += f"- הקטגוריה עם ההוצאה הגבוהה ביותר: {top_expense['category']} (₪{abs(top_expense['sum']):,.2f}, {top_expense['percentage']:.1f}% מסך ההוצאות)\n"
        
        # Suggest budget based on 50/30/20 rule
        report += "\n## המלצות תקציב\n\n"
        report += "על פי כלל ה-50/30/20 המקובל בניהול תקציב:\n"
        report += "- 50% מההכנסה נטו להוצאות חיוניות (דיור, מזון, תחבורה)\n"
        report += "- 30% לצרכים אישיים (בידור, מסעדות, קניות)\n"
        report += "- 20% לחיסכון והשקעות\n\n"
        
        # Save to session state
        st.session_state.current_report = report
        st.success("הדוח נוצר בהצלחה!")
    else:
        st.error("הנתונים חסרים שדות קטגוריה או סכום")

def generate_trend_analysis(transactions_df):
    """Generate a trend analysis report."""
    if 'date' in transactions_df.columns and 'amount' in transactions_df.columns:
        # Convert date to datetime
        transactions_df['date'] = pd.to_datetime(transactions_df['date'], errors='coerce')
        transactions_df['month'] = transactions_df['date'].dt.strftime('%Y-%m')
        
        # Group by month
        monthly = transactions_df.groupby('month').agg({
            'amount': [
                ('income', lambda x: x[x > 0].sum()),
                ('expenses', lambda x: x[x < 0].sum()),
                ('net', 'sum')
            ]
        })
        
        # Flatten multi-level columns
        monthly.columns = ['income', 'expenses', 'net']
        monthly = monthly.reset_index()
        
        # Calculate cumulative balance
        monthly['cumulative'] = monthly['net'].cumsum()
        
        # Create report
        report = "# ניתוח מגמות\n\n"
        report += "## מגמות הוצאות והכנסות לאורך זמן\n\n"
        
        # Create a trends table
        report += "| חודש | הכנסות | הוצאות | מאזן נטו | מאזן מצטבר |\n"
        report += "| ---- | ------- | ------- | -------- | ------------ |\n"
        
        for _, row in monthly.iterrows():
            report += f"| {row['month']} | ₪{row['income']:,.2f} | ₪{abs(row['expenses']):,.2f} | ₪{row['net']:,.2f} | ₪{row['cumulative']:,.2f} |\n"
        
        # Add insights
        report += "\n## תובנות\n\n"
        
        # Calculate growth rates if we have more than one month
        if len(monthly) > 1:
            # Income growth
            first_income = monthly.iloc[0]['income']
            last_income = monthly.iloc[-1]['income']
            income_growth = ((last_income / first_income) - 1) * 100 if first_income > 0 else 0
            
            # Expense growth
            first_expense = abs(monthly.iloc[0]['expenses'])
            last_expense = abs(monthly.iloc[-1]['expenses'])
            expense_growth = ((last_expense / first_expense) - 1) * 100 if first_expense > 0 else 0
            
            report += f"- שינוי בהכנסות: {income_growth:.1f}% מתחילת התקופה\n"
            report += f"- שינוי בהוצאות: {expense_growth:.1f}% מתחילת התקופה\n"
        
        # Recommendations based on trends
        report += "\n## המלצות\n\n"
        
        if len(monthly) > 1 and monthly['net'].mean() < 0:
            report += "- המאזן החודשי הממוצע שלילי. שקול להפחית הוצאות או להגדיל הכנסות.\n"
        
        if 'cumulative' in monthly and monthly.iloc[-1]['cumulative'] < 0:
            report += "- המאזן המצטבר שלילי. מומלץ לבחון את המצב הפיננסי ולהכין תכנית להחזרת האיזון.\n"
        
        # Save to session state
        st.session_state.current_report = report
        st.success("הדוח נוצר בהצלחה!")
    else:
        st.error("הנתונים חסרים שדה תאריך או סכום")

# Run the app
if __name__ == "__main__":
    render_reports_page()
