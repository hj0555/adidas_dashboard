import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.graph_objects as go

st.set_page_config(page_title="Adidas US Sales Dashboard", layout="wide")
st.title("👟 Adidas US Sales Data Dashboard")

# 데이터 불러오기 및 전처리
data = pd.read_csv("https://raw.githubusercontent.com/myoh0623/dataset/refs/heads/main/adidas_us_sales_datasets.csv")
data.columns = data.columns.str.strip()
for col in ["Price per Unit", "Total Sales", "Operating Profit"]:
    data[col] = data[col].replace('[\\$,]', '', regex=True).astype(float)
data["Units Sold"] = data["Units Sold"].replace('[,]', '', regex=True).astype(int)
data["Operating Margin"] = data["Operating Margin"].replace('[\\%,]', '', regex=True).astype(float)
data["Invoice Date"] = pd.to_datetime(data["Invoice Date"], errors="coerce")
data = data.dropna(subset=["Invoice Date"])

# 파생 변수 생성
data["Profit Rate"] = data["Operating Margin"] * 0.01
data["Year"] = data["Invoice Date"].dt.year
data["Month"] = data["Invoice Date"].dt.month

# 사이드바 필터 구현
st.sidebar.header("Filter Options")
region = st.sidebar.multiselect("Region", options=sorted(data["Region"].dropna().unique()), default=list(data["Region"].dropna().unique()))
retailer = st.sidebar.multiselect("Retailer", options=sorted(data["Retailer"].dropna().unique()), default=list(data["Retailer"].dropna().unique()))
product = st.sidebar.multiselect("Product", options=sorted(data["Product"].dropna().unique()), default=list(data["Product"].dropna().unique()))
sales_method = st.sidebar.multiselect("Sales Method", options=sorted(data["Sales Method"].dropna().unique()), default=list(data["Sales Method"].dropna().unique()))

filtered = data[
    data["Region"].isin(region) &
    data["Retailer"].isin(retailer) &
    data["Product"].isin(product) &
    data["Sales Method"].isin(sales_method)
]

# 주요 지표 요약 표시
st.markdown("## 📈 주요 지표")
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 매출액 ($)", f"{filtered['Total Sales'].sum():,.0f}")
k2.metric("총 판매수량", f"{filtered['Units Sold'].sum():,}")
k3.metric("평균 단가 ($)", f"{filtered['Price per Unit'].mean():.2f}")
k4.metric("평균 마진율 (%)", f"{filtered['Operating Margin'].mean():.2f}")

# 탭(Tab) 레이아웃 구성
tab1, tab2, tab3 = st.tabs(["트렌드 및 분포", "소매점/제품", "심화 분석"])

# 트렌드 및 분포 시각화
with tab1:
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("#### 월별 판매 트렌드")
        monthly = filtered.groupby([filtered["Invoice Date"].dt.to_period("M")]).agg({
            "Units Sold": "sum",
            "Total Sales": "sum"
        }).reset_index()
        monthly["Invoice Date"] = monthly["Invoice Date"].dt.to_timestamp()
        st.line_chart(
            monthly.set_index("Invoice Date")[["Units Sold", "Total Sales"]],
            use_container_width=True
        )
    with c2:
        st.markdown("#### 판매방법 비율")
        method_counts = filtered["Sales Method"].value_counts()
        pie_fig = go.Figure(
            data=[go.Pie(
                labels=method_counts.index,
                values=method_counts.values,
                hole=0.3
            )]
        )
        pie_fig.update_layout(title_text="Sales Method Share")
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("#### 제품-지역별 판매 히트맵")
    import plotly.express as px
    heatmap_data = pd.pivot_table(
        filtered,
        index="Product",
        columns="Region",
        values="Units Sold",
        aggfunc="sum"
    ).fillna(0)
    if not heatmap_data.empty:
        heatmap_fig = px.imshow(
            heatmap_data.values,
            labels=dict(x="Region", y="Product", color="Units Sold"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale="YlGnBu",
            text_auto=True,
            aspect="auto",
            title="Units Sold by Product and Region"
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("No data to display for heatmap.")

# 소매점/제품 분석
with tab2:
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 소매점별 판매수량")
        retail_sales = filtered.groupby("Retailer").agg({"Units Sold":"sum"}).sort_values("Units Sold", ascending=False)
        st.bar_chart(retail_sales, use_container_width=True)
    with c4:
        st.markdown("#### 소매점별 매출액")
        retail_sales2 = filtered.groupby("Retailer").agg({"Total Sales":"sum"}).sort_values("Total Sales", ascending=False)
        st.bar_chart(retail_sales2, use_container_width=True)

    st.markdown("#### 제품별 판매수량 TOP")
    prod_sales = filtered.groupby("Product").agg({"Units Sold":"sum"}).sort_values("Units Sold", ascending=False)
    st.bar_chart(prod_sales, use_container_width=True)

    st.markdown("#### 월별-제품별 판매 피벗테이블")
    pivot = pd.pivot_table(
        filtered,
        index=filtered["Invoice Date"].dt.to_period("M"),
        columns="Product",
        values="Units Sold",
        aggfunc="sum"
    ).fillna(0)
    st.dataframe(pivot.astype(int))

# 심화 분석
with tab3:
    c5, c6 = st.columns(2)
    with c5:
        st.markdown("#### 판매방법별 평균 마진율")
        method_stats = filtered.groupby("Sales Method").agg({
            "Profit Rate":"mean"
        }).sort_values("Profit Rate", ascending=False)
        st.bar_chart(method_stats, use_container_width=True)
    with c6:
        st.markdown("#### 판매방법별 평균 단가")
        method_stats2 = filtered.groupby("Sales Method").agg({
            "Price per Unit":"mean"
        }).sort_values("Price per Unit", ascending=False)
        st.bar_chart(method_stats2, use_container_width=True)

    st.markdown("#### 단가-판매수량 산점도")
    import plotly.express as px
    if not filtered.empty:
        scatter_fig = px.scatter(
            filtered,
            x="Price per Unit",
            y="Units Sold",
            title="Price per Unit vs Units Sold",
            opacity=0.5,
            color="Sales Method",
            height=300
        )
        st.plotly_chart(scatter_fig, use_container_width=True)
    else:
        st.info("No data to display for scatter plot.")

    with st.expander("데이터 미리보기"):
        st.dataframe(filtered.head(20))
