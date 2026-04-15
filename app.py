import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Employee Attrition Dashboard", layout="wide")

st.title("Employee Attrition Dashboard")
st.write("Upload your HR attrition CSV file to explore turnover patterns, hotspots, and workforce risks.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

@st.cache_data
def load_data(file):
    return pd.read_csv(r"C:\Users\ilakk\Desktop\cognify tech\unified mentor\Palo Alto Networks.csv")

def clean_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    if "Attrition" in df.columns and df["Attrition"].dtype == "object":
        df["Attrition_Flag"] = df["Attrition"].map({"Yes": 1, "No": 0})
    elif "Attrition" in df.columns:
        df["Attrition_Flag"] = df["Attrition"]
    else:
        st.error("Attrition column not found in dataset.")
        st.stop()

    if "BusinessTravel" in df.columns:
        df["BusinessTravel"] = df["BusinessTravel"].replace({
            "Travel_Rarely": "Travel Rarely",
            "Travel_Frequently": "Travel Frequently",
            "Non-Travel": "Non-Travel",
            "Non-travel": "Non-Travel"
        })

    if "YearsAtCompany" in df.columns:
        df["TenureBucket"] = pd.cut(
            df["YearsAtCompany"],
            bins=[-1, 2, 5, 10, 20, 100],
            labels=["0-2 Years", "3-5 Years", "6-10 Years", "11-20 Years", "20+ Years"]
        )

    if "Age" in df.columns:
        df["AgeGroup"] = pd.cut(
            df["Age"],
            bins=[17, 25, 35, 45, 55, 100],
            labels=["18-25", "26-35", "36-45", "46-55", "56+"]
        )

    if "YearsSinceLastPromotion" in df.columns:
        df["PromotionStatus"] = pd.cut(
            df["YearsSinceLastPromotion"],
            bins=[-1, 1, 3, 100],
            labels=["Recently Promoted", "Moderate Gap", "Stagnated"]
        )

    return df

def attrition_summary(df):
    total = len(df)
    exited = int(df["Attrition_Flag"].sum())
    retained = total - exited
    rate = round((exited / total) * 100, 2) if total > 0 else 0
    return total, exited, retained, rate

def group_attrition(df, group_col):
    g = (
        df.groupby(group_col, dropna=False)
        .agg(TotalEmployees=("Attrition_Flag", "count"),
             ExitedEmployees=("Attrition_Flag", "sum"))
        .reset_index()
    )
    g["AttritionRate"] = round((g["ExitedEmployees"] / g["TotalEmployees"]) * 100, 2)
    return g.sort_values("AttritionRate", ascending=False)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    df = clean_data(df)

    st.success(f"Dataset loaded successfully: {df.shape[0]} rows and {df.shape[1]} columns")

    total, exited, retained, rate = attrition_summary(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", total)
    c2.metric("Exited Employees", exited)
    c3.metric("Retained Employees", retained)
    c4.metric("Attrition Rate (%)", rate)

    st.divider()

    filter_cols = st.columns(4)

    dep_options = sorted(df["Department"].dropna().unique()) if "Department" in df.columns else []
    role_options = sorted(df["JobRole"].dropna().unique()) if "JobRole" in df.columns else []
    ot_options = sorted(df["OverTime"].dropna().unique()) if "OverTime" in df.columns else []
    travel_options = sorted(df["BusinessTravel"].dropna().unique()) if "BusinessTravel" in df.columns else []

    selected_dept = filter_cols[0].multiselect("Department", dep_options, default=dep_options)
    selected_role = filter_cols[1].multiselect("Job Role", role_options, default=role_options)
    selected_ot = filter_cols[2].multiselect("OverTime", ot_options, default=ot_options)
    selected_travel = filter_cols[3].multiselect("Business Travel", travel_options, default=travel_options)

    min_years = int(df["YearsAtCompany"].min()) if "YearsAtCompany" in df.columns else 0
    max_years = int(df["YearsAtCompany"].max()) if "YearsAtCompany" in df.columns else 0

    if "YearsAtCompany" in df.columns:
        tenure_range = st.slider("Years at Company", min_years, max_years, (min_years, max_years))
    else:
        tenure_range = (0, 0)

    filtered_df = df.copy()

    if "Department" in df.columns and len(selected_dept) > 0:
        filtered_df = filtered_df[filtered_df["Department"].isin(selected_dept)]
    if "JobRole" in df.columns and len(selected_role) > 0:
        filtered_df = filtered_df[filtered_df["JobRole"].isin(selected_role)]
    if "OverTime" in df.columns and len(selected_ot) > 0:
        filtered_df = filtered_df[filtered_df["OverTime"].isin(selected_ot)]
    if "BusinessTravel" in df.columns and len(selected_travel) > 0:
        filtered_df = filtered_df[filtered_df["BusinessTravel"].isin(selected_travel)]
    if "YearsAtCompany" in df.columns:
        filtered_df = filtered_df[
            filtered_df["YearsAtCompany"].between(tenure_range[0], tenure_range[1])
        ]

    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df.head(20), use_container_width=True)

    st.divider()

    left, right = st.columns(2)

    if "Department" in filtered_df.columns:
        dept_attr = group_attrition(filtered_df, "Department")
        fig_dept = px.bar(
            dept_attr,
            x="Department",
            y="AttritionRate",
            color="AttritionRate",
            text="AttritionRate",
            title="Attrition Rate by Department"
        )
        left.plotly_chart(fig_dept, use_container_width=True)

    if "JobRole" in filtered_df.columns:
        role_attr = group_attrition(filtered_df, "JobRole")
        fig_role = px.bar(
            role_attr.head(10),
            x="JobRole",
            y="AttritionRate",
            color="AttritionRate",
            text="AttritionRate",
            title="Top Job Roles by Attrition Rate"
        )
        fig_role.update_layout(xaxis_tickangle=-45)
        right.plotly_chart(fig_role, use_container_width=True)

    if "TenureBucket" in filtered_df.columns:
        tenure_attr = group_attrition(filtered_df, "TenureBucket")
        fig_tenure = px.bar(
            tenure_attr,
            x="TenureBucket",
            y="AttritionRate",
            color="AttritionRate",
            text="AttritionRate",
            title="Attrition Rate by Tenure Bucket"
        )
        st.plotly_chart(fig_tenure, use_container_width=True)

    col_a, col_b = st.columns(2)

    if "OverTime" in filtered_df.columns:
        ot_attr = group_attrition(filtered_df, "OverTime")
        fig_ot = px.pie(
            ot_attr,
            names="OverTime",
            values="ExitedEmployees",
            title="Exited Employees by Overtime"
        )
        col_a.plotly_chart(fig_ot, use_container_width=True)

    if "BusinessTravel" in filtered_df.columns:
        travel_attr = group_attrition(filtered_df, "BusinessTravel")
        fig_travel = px.bar(
            travel_attr,
            x="BusinessTravel",
            y="AttritionRate",
            color="AttritionRate",
            text="AttritionRate",
            title="Attrition Rate by Business Travel"
        )
        col_b.plotly_chart(fig_travel, use_container_width=True)

    if "Department" in filtered_df.columns and "JobRole" in filtered_df.columns:
        st.subheader("Department vs Job Role Heatmap")
        heatmap_df = filtered_df.pivot_table(
            index="Department",
            columns="JobRole",
            values="Attrition_Flag",
            aggfunc="mean"
        ) * 100

        heatmap_fig = px.imshow(
            heatmap_df,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Reds",
            title="Attrition Rate Heatmap (%)"
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)

    st.divider()
    st.subheader("Key Observations")

    insights = []
    if "TenureBucket" in filtered_df.columns:
        top_tenure = group_attrition(filtered_df, "TenureBucket").head(1)
        if not top_tenure.empty:
            insights.append(f"Highest attrition tenure band: {top_tenure.iloc[0, 0]}.")

    if "OverTime" in filtered_df.columns:
        ot_rate = group_attrition(filtered_df, "OverTime")
        insights.append("Overtime is a key workload variable worth monitoring for retention risk.")

    if "JobRole" in filtered_df.columns:
        top_role = group_attrition(filtered_df, "JobRole").head(1)
        if not top_role.empty:
            insights.append(f"Highest-risk role in the filtered data: {top_role.iloc[0, 0]}.")

    if "BusinessTravel" in filtered_df.columns:
        insights.append("Business travel frequency can be used to test mobility-related turnover pressure.")

    for item in insights:
        st.write(f"- {item}")

else:
    st.info("Upload your HR attrition CSV file to begin.")