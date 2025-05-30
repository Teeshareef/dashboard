import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Dashboard layout
st.set_page_config(layout="wide", page_title="Student Dashboard")
st.title("Student Performance Dashboard")

# Load data
@st.cache_data
def load_data():
    profiles = pd.read_csv("student_profiles.csv")
    assignments = pd.read_csv("student_assignments.csv")
    attendance = pd.read_csv("student_attendance.csv")
    remarks = pd.read_csv("student_remarks.csv")
    scores = pd.read_csv("student_scores.csv")
    summary = pd.read_csv("student_summary.csv")
    
    # Convert dates to datetime
    assignments['Deadline'] = pd.to_datetime(assignments['Deadline'])
    attendance['Date'] = pd.to_datetime(attendance['Date'])
    remarks['Date'] = pd.to_datetime(remarks['Date'])
    
    return profiles, assignments, attendance, remarks, scores, summary

profiles, assignments, attendance, remarks, scores, summary = load_data()


# Sidebar filters
st.sidebar.header("Filters")
selected_class = st.sidebar.selectbox("Select Class", ["All"] + list(summary['Class'].unique()))
selected_section = st.sidebar.selectbox("Select Section", ["All"] + list(summary['Section'].unique()))
selected_gender = st.sidebar.selectbox("Select Gender", ["All"] + list(summary['Gender'].unique()))

# Apply filters
if selected_class != "All":
    summary = summary[summary['Class'] == selected_class]
if selected_section != "All":
    summary = summary[summary['Section'] == selected_section]
if selected_gender != "All":
    summary = summary[summary['Gender'] == selected_gender]

# Overview metrics
st.header("Overview Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", len(summary))
col2.metric("Average Score", f"{summary['Average Score'].mean():.1f}")
col3.metric("Average Attendance", f"{summary['Attendance Rate'].mean()*100:.1f}%")
col4.metric("Average Submission Rate", f"{summary['Submission Rate'].mean()*100:.1f}%")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Performance", "Attendance", "Assignments", "Remarks"])

with tab1:
    st.header("Student Summary")
    
    # Top and bottom performers
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Scholars")
        top_performers = summary.sort_values('Average Score', ascending=False).head(5)
        st.dataframe(top_performers[['Name', 'Class', 'Section', 'Average Score']])
    
    with col2:
        st.subheader("Students Needing Support")
        bottom_performers = summary.sort_values('Average Score').head(5)
        st.dataframe(bottom_performers[['Name', 'Class', 'Section', 'Average Score']])
    
    # Performance distribution
    st.subheader("Performance Distribution")
    fig = px.histogram(summary, x='Average core', nbins=20, 
                       title="Distribution of Average Scores")
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation between metrics
    st.subheader("Metric Correlations")
    fig = px.scatter_matrix(summary, dimensions=['Average Score', 'Attendance Rate', 'Submission Rate'],
                           color='Class', hover_name='Name')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Academic Performance")
    
    # Subject-wise performance
    st.subheader("Subject-wise Performance")
    subject_scores = scores.groupby('Subject')['Score'].mean().reset_index()
    fig = px.bar(subject_scores, x='Subject', y='Score', 
                 title="Average Scores by Subject")
    st.plotly_chart(fig, use_container_width=True)
    
    # Term-wise performance
    st.subheader("Term-wise Performance")
    term_scores = scores.groupby(['Subject', 'Term'])['Score'].mean().reset_index()
    fig = px.bar(term_scores, x='Subject', y='Score', color='Term', barmode='group',
                 title="Average Scores by Subject and Term")
    st.plotly_chart(fig, use_container_width=True)
    
    # Student selector for individual performance
    selected_student = st.selectbox("Select Student to View Detailed Performance", 
                                  summary['Name'].unique())
    student_id = summary[summary['Name'] == selected_student]['ID'].values[0]
    student_scores = scores[scores['ID'] == student_id]
    
    fig = px.bar(student_scores, x='Subject', y='Score', color='Term', 
                 barmode='group', title=f"{selected_student}'s Performance by Subject")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Attendance Analysis")
    
    # Overall attendance rate
    st.subheader("Attendance Rate Distribution")
    fig = px.histogram(summary, x='Attendance Rate', nbins=10,
                       title="Distribution of Attendance Rates")
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly attendance trend
    st.subheader("Monthly Attendance Trend")
    attendance['Month'] = attendance['Date'].dt.month_name()
    monthly_attendance = attendance.groupby(['Month', 'Present']).size().unstack().fillna(0)
    monthly_attendance['Attendance Rate'] = monthly_attendance[True] / (monthly_attendance[True] + monthly_attendance[False])
    
    fig = px.line(monthly_attendance, x=monthly_attendance.index, y='Attendance Rate',
                  title="Monthly Attendance Rate Trend")
    st.plotly_chart(fig, use_container_width=True)
    
    # Student attendance details
    selected_student_att = st.selectbox("Select Student to View Attendance Details", 
                                      summary['Name'].unique())
    student_id_att = summary[summary['Name'] == selected_student_att]['ID'].values[0]
    student_attendance = attendance[attendance['ID'] == student_id_att]
    
    # Calculate present and absent days
    present_days = student_attendance['Present'].sum()
    absent_days = len(student_attendance) - present_days
    
    fig = go.Figure(data=[go.Pie(labels=['Present', 'Absent'], 
                          values=[present_days, absent_days])])
    fig.update_layout(title=f"{selected_student_att}'s Attendance")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Assignments Analysis")
    
    # Assignment completion rate by subject
    st.subheader("Assignment Completion by Subject")
    completed_assignments = assignments[assignments['Submitted'] == True].groupby('Subject').size()
    total_assignments = assignments.groupby('Subject').size()
    completion_rate = (completed_assignments / total_assignments * 100).reset_index()
    completion_rate.columns = ['Subject', 'Completion Rate']
    
    fig = px.bar(completion_rate, x='Subject', y='Completion Rate',
                 title="Assignment Completion Rate by Subject")
    st.plotly_chart(fig, use_container_width=True)
    
    # Upcoming deadlines
    st.subheader("Upcoming Deadlines")
    upcoming = assignments[assignments['Deadline'] >= datetime.now()]
    upcoming_display = upcoming[['Assignment', 'Subject', 'Deadline', 'Submitted', 'Marks']].sort_values('Deadline')
    st.dataframe(upcoming.sort_values('Deadline').head(10))
    
    # Student assignment performance
    selected_student_assign = st.selectbox("Select Student to View Assignments", 
                                         summary['Name'].unique())
    student_id_assign = summary[summary['Name'] == selected_student_assign]['ID'].values[0]
    student_assignments = assignments[assignments['ID'] == student_id_assign]
    
    # Submitted vs not submitted
    submitted = student_assignments['Submitted'].sum()
    not_submitted = len(student_assignments) - submitted
    
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(data=[go.Pie(labels=['Submitted', 'Not Submitted'], 
                              values=[submitted, not_submitted])])
        fig.update_layout(title="Submission Status")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Marks distribution for submitted assignments
        submitted_marks = student_assignments[student_assignments['Submitted'] == True]
        if not submitted_marks.empty:
            fig = px.histogram(submitted_marks, x='Marks', nbins=10,
                               title="Marks Distribution for Submitted Assignments")
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Teacher Remarks")
    
    # Remarks distribution
    st.subheader("Remarks Distribution")
    remark_counts = remarks['Remark'].value_counts().reset_index()
    remark_counts.columns = ['Remark', 'Count']
    
    fig = px.pie(remark_counts, values='Count', names='Remark', 
                 title="Distribution of Teacher Remarks")
    st.plotly_chart(fig, use_container_width=True)
    
    # Student remarks
    selected_student_remark = st.selectbox("Select Student to View Remarks", 
                                         summary['Name'].unique())
    student_id_remark = summary[summary['Name'] == selected_student_remark]['ID'].values[0]
    student_remarks = remarks[remarks['ID'] == student_id_remark].sort_values('Date', ascending=False)
    
    st.dataframe(student_remarks)
    
    # Remarks over time
    if not student_remarks.empty:
        remark_trend = student_remarks.groupby(['Date', 'Remark']).size().unstack().fillna(0)
        fig = px.line(remark_trend, x=remark_trend.index, y=remark_trend.columns,
                      title="Remarks Over Time")
        st.plotly_chart(fig, use_container_width=True)

# Download option
st.sidebar.header("Data Export")
if st.sidebar.button("Download Summary Data"):
    csv = summary.to_csv(index=False)
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name="student_summary.csv",
        mime="text/csv"
    )