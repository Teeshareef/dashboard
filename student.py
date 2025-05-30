import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Dashboard layout - must be first Streamlit command
st.set_page_config(layout="wide", page_title="Student Dashboard")
st.title("Student Performance Dashboard")

# Load data with better error handling
@st.cache_data
def load_data():
    try:
        profiles = pd.read_csv("student_profiles.csv")
        assignments = pd.read_csv("student_assignments.csv")
        attendance = pd.read_csv("student_attendance.csv")
        remarks = pd.read_csv("student_remarks.csv")
        scores = pd.read_csv("student_scores.csv")
        summary = pd.read_csv("student_summary.csv")
        
        # Convert dates to datetime with error handling
        assignments['Deadline'] = pd.to_datetime(assignments['Deadline'], errors='coerce')
        attendance['Date'] = pd.to_datetime(attendance['Date'], errors='coerce')
        remarks['Date'] = pd.to_datetime(remarks['Date'], errors='coerce')
        
        # Ensure ID columns are strings for consistent merging
        for df in [profiles, assignments, attendance, remarks, scores, summary]:
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str)
        
        return profiles, assignments, attendance, remarks, scores, summary
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None, None, None, None

profiles, assignments, attendance, remarks, scores, summary = load_data()

# Check if data loaded successfully
if profiles is None:
    st.stop()

# Sidebar filters with session state to preserve selections
st.sidebar.header("Filters")

# Initialize session state
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = "All"
if 'selected_section' not in st.session_state:
    st.session_state.selected_section = "All"
if 'selected_gender' not in st.session_state:
    st.session_state.selected_gender = "All"

# Update filters with unique values from the data
st.session_state.selected_class = st.sidebar.selectbox(
    "Select Class", 
    ["All"] + sorted(summary['Class'].unique()),
    index=0 if st.session_state.selected_class == "All" else list(summary['Class'].unique()).index(st.session_state.selected_class) + 1
)

# Filter sections based on selected class
available_sections = ["All"]
if st.session_state.selected_class != "All":
    available_sections += sorted(summary[summary['Class'] == st.session_state.selected_class]['Section'].unique())

st.session_state.selected_section = st.sidebar.selectbox(
    "Select Section",
    available_sections,
    index=0 if st.session_state.selected_section == "All" else available_sections.index(st.session_state.selected_section)
)

st.session_state.selected_gender = st.sidebar.selectbox(
    "Select Gender",
    ["All"] + sorted(summary['Gender'].unique()),
    index=0 if st.session_state.selected_gender == "All" else list(summary['Gender'].unique()).index(st.session_state.selected_gender) + 1
)

# Apply filters
filtered_summary = summary.copy()
if st.session_state.selected_class != "All":
    filtered_summary = filtered_summary[filtered_summary['Class'] == st.session_state.selected_class]
if st.session_state.selected_section != "All":
    filtered_summary = filtered_summary[filtered_summary['Section'] == st.session_state.selected_section]
if st.session_state.selected_gender != "All":
    filtered_summary = filtered_summary[filtered_summary['Gender'] == st.session_state.selected_gender]

# Overview metrics with better formatting
st.header("Overview Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", len(filtered_summary))
col2.metric("Average Score", f"{filtered_summary['Average Score'].mean():.1f}" if not filtered_summary.empty else "N/A")
col3.metric("Average Attendance", f"{filtered_summary['Attendance Rate'].mean()*100:.1f}%" if not filtered_summary.empty else "N/A")
col4.metric("Average Submission Rate", f"{filtered_summary['Submission Rate'].mean()*100:.1f}%" if not filtered_summary.empty else "N/A")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Performance", "Attendance", "Assignments", "Remarks"])

with tab1:
    st.header("Student Summary")
    
    if filtered_summary.empty:
        st.warning("No students match the selected filters")
    else:
        # Top and bottom performers with better formatting
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Scholars")
            top_performers = filtered_summary.sort_values('Average Score', ascending=False).head(5)
            st.dataframe(
                top_performers[['Name', 'Class', 'Section', 'Average Score']]
                .rename(columns={'Average Score': 'Avg Score'})
                .style.format({'Avg Score': '{:.1f}'}),
                height=200
            )
        
        with col2:
            st.subheader("Students Needing Support")
            bottom_performers = filtered_summary.sort_values('Average Score').head(5)
            st.dataframe(
                bottom_performers[['Name', 'Class', 'Section', 'Average Score']]
                .rename(columns={'Average Score': 'Avg Score'})
                .style.format({'Avg Score': '{:.1f}'}),
                height=200
            )
        
        # Performance distribution with better bins
        st.subheader("Performance Distribution")
        if not filtered_summary.empty:
            fig = px.histogram(
                filtered_summary, 
                x='Average Score', 
                nbins=20,
                title="Distribution of Average Scores",
                labels={'Average Score': 'Average Score (%)'}
            )
            fig.update_layout(yaxis_title="Number of Students")
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation between metrics with better visualization
        st.subheader("Metric Correlations")
        if not filtered_summary.empty:
            fig = px.scatter_matrix(
                filtered_summary,
                dimensions=['Average Score', 'Attendance Rate', 'Submission Rate'],
                color='Class',
                hover_name='Name',
                labels={
                    'Average Score': 'Avg Score',
                    'Attendance Rate': 'Attendance',
                    'Submission Rate': 'Submissions'
                }
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Academic Performance")
    
    if filtered_summary.empty:
        st.warning("No students match the selected filters")
    else:
        # Subject-wise performance with merged data
        st.subheader("Subject-wise Performance")
        merged_scores = pd.merge(scores, filtered_summary[['ID']], on='ID', how='inner')
        if not merged_scores.empty:
            subject_scores = merged_scores.groupby('Subject')['Score'].mean().reset_index()
            fig = px.bar(
                subject_scores, 
                x='Subject', 
                y='Score',
                title="Average Scores by Subject",
                labels={'Score': 'Average Score (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Term-wise performance with better grouping
        st.subheader("Term-wise Performance")
        if not merged_scores.empty:
            term_scores = merged_scores.groupby(['Subject', 'Term'])['Score'].mean().reset_index()
            fig = px.bar(
                term_scores, 
                x='Subject', 
                y='Score', 
                color='Term', 
                barmode='group',
                title="Average Scores by Subject and Term",
                labels={'Score': 'Average Score (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Student selector for individual performance
        selected_student = st.selectbox(
            "Select Student to View Detailed Performance", 
            filtered_summary['Name'].unique()
        )
        
        if selected_student:
            matching_students = filtered_summary[filtered_summary['Name'] == selected_student]
            if matching_students.empty:
                st.warning(f"No student found with the name {selected_student}")
            else:
                 # Handle if multiple students with same name
                if len(matching_students) > 1:
                     # Let user select the correct ID if duplicates exist
                    selected_id = st.selectbox(
                        f"Multiple students named {selected_student} found. Please select ID:",
                        matching_students['ID'].tolist()
                    )
                else:
                    selected_id = matching_students['ID'].values[0]

                # Now filter scores by selected_id
                student_scores = scores[scores['ID'] == selected_id]
                if not student_scores.empty:
                    fig = px.bar(
                        student_scores, 
                        x='Subject', 
                        y='Score', 
                        color='Term',
                        barmode='group', 
                        title=f"{selected_student}'s Performance by Subject",
                        labels={'Score': 'Score (%)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No score data available for {selected_student} (ID: {selected_id})")


with tab3:
    st.header("Attendance Analysis")
    
    if filtered_summary.empty:
        st.warning("No students match the selected filters")
    else:
        # Overall attendance rate with better visualization
        st.subheader("Attendance Rate Distribution")
        if not filtered_summary.empty:
            fig = px.histogram(
                filtered_summary, 
                x='Attendance Rate', 
                nbins=10,
                title="Distribution of Attendance Rates",
                labels={'Attendance Rate': 'Attendance Rate'}
            )
            fig.update_layout(yaxis_title="Number of Students")
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly attendance trend with proper date handling
        st.subheader("Monthly Attendance Trend")
        filtered_attendance = pd.merge(attendance, filtered_summary[['ID']], on='ID', how='inner')
        if not filtered_attendance.empty:
            filtered_attendance['Month'] = filtered_attendance['Date'].dt.strftime('%Y-%m')
            monthly_attendance = filtered_attendance.groupby(['Month', 'Present']).size().unstack().fillna(0)
            monthly_attendance['Attendance Rate'] = monthly_attendance[True] / (monthly_attendance[True] + monthly_attendance[False])
            
            fig = px.line(
                monthly_attendance, 
                x=monthly_attendance.index, 
                y='Attendance Rate',
                title="Monthly Attendance Rate Trend",
                labels={'Attendance Rate': 'Attendance Rate', 'index': 'Month'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Student attendance details
        selected_student_att = st.selectbox(
            "Select Student to View Attendance Details", 
            filtered_summary['Name'].unique()
        )
        
        if selected_student_att:
            student_id_att = filtered_summary[filtered_summary['Name'] == selected_student_att]['ID'].values[0]
            student_attendance = attendance[attendance['ID'] == student_id_att]
            
            if not student_attendance.empty:
                # Calculate present and absent days
                present_days = student_attendance['Present'].sum()
                absent_days = len(student_attendance) - present_days
                
                fig = go.Figure(data=[
                    go.Pie(
                        labels=['Present', 'Absent'], 
                        values=[present_days, absent_days],
                        hole=0.4
                    )
                ])
                fig.update_layout(title=f"{selected_student_att}'s Attendance")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No attendance data available for {selected_student_att}")

with tab4:
    st.header("Assignments Analysis")
    
    if filtered_summary.empty:
        st.warning("No students match the selected filters")
    else:
        # Assignment completion rate by subject with filtered data
        st.subheader("Assignment Completion by Subject")
        filtered_assignments = pd.merge(assignments, filtered_summary[['ID']], on='ID', how='inner')
        if not filtered_assignments.empty:
            completed_assignments = filtered_assignments[filtered_assignments['Submitted'] == True].groupby('Subject').size()
            total_assignments = filtered_assignments.groupby('Subject').size()
            completion_rate = (completed_assignments / total_assignments * 100).reset_index()
            completion_rate.columns = ['Subject', 'Completion Rate']
            
            fig = px.bar(
                completion_rate, 
                x='Subject', 
                y='Completion Rate',
                title="Assignment Completion Rate by Subject",
                labels={'Completion Rate': 'Completion Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Upcoming deadlines with better date formatting
        st.subheader("Upcoming Deadlines")
        if not filtered_assignments.empty:
            upcoming = filtered_assignments[filtered_assignments['Deadline'] >= datetime.now()]
            if not upcoming.empty:
                upcoming_display = upcoming[['Assignment', 'Subject', 'Deadline', 'Submitted', 'Marks']].sort_values('Deadline')
                upcoming_display['Deadline'] = upcoming_display['Deadline'].dt.strftime('%Y-%m-%d')
                st.dataframe(
                    upcoming_display.head(10).style.applymap(
                        lambda x: 'color: green' if x == True else ('color: red' if x == False else ''), 
                        subset=['Submitted']
                    )
                )
            else:
                st.info("No upcoming assignments")
        
        # Student assignment performance
        selected_student_assign = st.selectbox(
            "Select Student to View Assignments", 
            filtered_summary['Name'].unique()
        )
        
        if selected_student_assign:
            student_id_assign = filtered_summary[filtered_summary['Name'] == selected_student_assign]['ID'].values[0]
            student_assignments = assignments[assignments['ID'] == student_id_assign]
            
            if not student_assignments.empty:
                # Submitted vs not submitted
                submitted = student_assignments['Submitted'].sum()
                not_submitted = len(student_assignments) - submitted
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(data=[
                        go.Pie(
                            labels=['Submitted', 'Not Submitted'], 
                            values=[submitted, not_submitted],
                            hole=0.4
                        )
                    ])
                    fig.update_layout(title="Submission Status")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Marks distribution for submitted assignments
                    submitted_marks = student_assignments[student_assignments['Submitted'] == True]
                    if not submitted_marks.empty:
                        fig = px.histogram(
                            submitted_marks, 
                            x='Marks', 
                            nbins=10,
                            title="Marks Distribution for Submitted Assignments",
                            labels={'Marks': 'Marks (%)'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No submitted assignments to show marks distribution")
            else:
                st.warning(f"No assignment data available for {selected_student_assign}")

with tab5:
    st.header("Teacher Remarks")
    
    if filtered_summary.empty:
        st.warning("No students match the selected filters")
    else:
        # Remarks distribution with filtered data
        st.subheader("Remarks Distribution")
        filtered_remarks = pd.merge(remarks, filtered_summary[['ID']], on='ID', how='inner')
        if not filtered_remarks.empty:
            remark_counts = filtered_remarks['Remark'].value_counts().reset_index()
            remark_counts.columns = ['Remark', 'Count']
            
            fig = px.pie(
                remark_counts, 
                values='Count', 
                names='Remark', 
                title="Distribution of Teacher Remarks",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Student remarks with better display
        selected_student_remark = st.selectbox(
            "Select Student to View Remarks", 
            filtered_summary['Name'].unique()
        )
        
        if selected_student_remark:
            student_id_remark = filtered_summary[filtered_summary['Name'] == selected_student_remark]['ID'].values[0]
            student_remarks = remarks[remarks['ID'] == student_id_remark].sort_values('Date', ascending=False)
            
            if not student_remarks.empty:
                student_remarks['Date'] = student_remarks['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(
                    student_remarks[['Date', 'Teacher', 'Remark']]
                    .style.applymap(
                        lambda x: 'color: green' if x == 'Excellent' else (
                            'color: orange' if x == 'Good' else 'color: red'
                        ),
                        subset=['Remark']
                    )
                )
                
                # Remarks over time with better date handling
                st.subheader("Remarks Over Time")
                remark_trend = student_remarks.groupby(['Date', 'Remark']).size().unstack().fillna(0)
                fig = px.line(
                    remark_trend, 
                    x=remark_trend.index, 
                    y=remark_trend.columns,
                    title="Remarks Over Time",
                    labels={'value': 'Number of Remarks', 'variable': 'Remark Type'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No remarks available for {selected_student_remark}")

# Download option with filtered data
st.sidebar.header("Data Export")
if st.sidebar.button("Download Filtered Data"):
    if not filtered_summary.empty:
        csv = filtered_summary.to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_student_summary.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.warning("No data to download with current filters")