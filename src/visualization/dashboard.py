"""
The Beacon: Predictive Rhetoric Dashboard
Streamlit-based visualization of moral foundation trends and rhetoric spikes.
Includes Pharos predictive mode for escalation alerts.
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
import pandas as pd
import numpy as np
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px

DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")
SIGNALS_PATH = os.path.normpath("D:/mcp_servers/storage/compiled_signals.json")

class RhetoricAnalyzer:
    """Analyzes rhetoric trends and patterns."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_sentiment_timeline(self, days: int = 30) -> pd.DataFrame:
        """Gets sentiment data over time."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = f"""
                SELECT timestamp, compound, neg, neu, pos, source_file
                FROM sentiment_logs
                WHERE timestamp >= datetime('now', '-{days} days')
                ORDER BY timestamp ASC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date
            
            return df
        except Exception as e:
            st.error(f"Error loading timeline: {e}")
            return pd.DataFrame()
    
    def calculate_moving_average(self, series: pd.Series, window: int = 7) -> pd.Series:
        """Calculates moving average."""
        return series.rolling(window=window, min_periods=1).mean()
    
    def detect_rhetoric_spikes(self, df: pd.DataFrame, threshold: float = 1.5) -> list:
        """Detects significant sentiment spikes."""
        spikes = []
        
        if len(df) < 2:
            return spikes
        
        mean_compound = df['compound'].mean()
        std_compound = df['compound'].std()
        
        for idx, row in df.iterrows():
            z_score = abs((row['compound'] - mean_compound) / (std_compound + 0.001))
            
            if z_score > threshold:
                spikes.append({
                    'date': row['timestamp'],
                    'compound': row['compound'],
                    'z_score': z_score,
                    'source': row['source_file'],
                    'severity': 'high' if z_score > 2.5 else 'medium'
                })
        
        return sorted(spikes, key=lambda x: x['z_score'], reverse=True)
    
    def analyze_moral_foundations(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyzes moral foundation distribution."""
        try:
            with open(SIGNALS_PATH, 'r') as f:
                signals = json.load(f)
        except:
            signals = {}
        
        # Map signals to foundation intensity
        foundations = {
            'Care/Harm': {'terms': ['suffer', 'hurt', 'pain', 'victim', 'cruel'], 'intensity': 0},
            'Fairness/Cheating': {'terms': ['fair', 'unfair', 'just', 'cheat', 'dishonest'], 'intensity': 0},
            'Loyalty/Betrayal': {'terms': ['loyal', 'betray', 'traitor', 'ally', 'enemy'], 'intensity': 0},
            'Authority/Subversion': {'terms': ['rule', 'law', 'respect', 'rebel', 'authority'], 'intensity': 0},
            'Sanctity/Degradation': {'terms': ['pure', 'degraded', 'sacred', 'corrupt', 'contaminate'], 'intensity': 0},
            'Liberty/Oppression': {'terms': ['freedom', 'liberty', 'oppression', 'chains', 'dominate'], 'intensity': 0},
        }
        
        for foundation, data in foundations.items():
            total_intensity = 0
            for term in data['terms']:
                if term in signals:
                    total_intensity += abs(signals[term])
            foundations[foundation]['intensity'] = total_intensity / len(data['terms'])
        
        return {k: v['intensity'] for k, v in foundations.items()}
    
    def predict_escalation(self, df: pd.DataFrame, window: int = 7) -> Dict[str, Any]:
        """Predicts whether negative sentiment is escalating."""
        if len(df) < window * 2:
            return {'status': 'insufficient_data'}
        
        recent = df.tail(window)['compound'].values
        previous = df.iloc[-window*2:-window]['compound'].values
        
        recent_mean = np.mean(recent)
        previous_mean = np.mean(previous)
        
        trend_direction = 'escalating' if recent_mean < previous_mean else 'deescalating'
        trend_strength = abs(recent_mean - previous_mean)
        
        return {
            'trend': trend_direction,
            'strength': round(trend_strength, 4),
            'recent_mean': round(recent_mean, 4),
            'previous_mean': round(previous_mean, 4),
            'alert': 'escalation_detected' if trend_strength > 0.2 and trend_direction == 'escalating' else 'normal'
        }


def main():
    """Main Streamlit dashboard."""
    st.set_page_config(page_title="🔭 Beacon - Rhetoric Dashboard", layout="wide")
    
    st.title("🔭 Beacon: Predictive Rhetoric Dashboard")
    st.markdown("Real-time visualization of moral foundation trends and rhetoric escalation alerts.")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Dashboard Controls")
        
        days_back = st.slider("Temporal Window (days)", 7, 365, 30)
        threshold = st.slider("Spike Detection Threshold (σ)", 0.5, 3.0, 1.5)
        analysis_mode = st.radio("Analysis Mode", ["Trends", "Pharos (Predictive)", "Foundations", "Alerts"])
    
    analyzer = RhetoricAnalyzer(DB_PATH)
    
    # Load data
    df = analyzer.get_sentiment_timeline(days_back)
    
    if df.empty:
        st.warning("No data available for selected period.")
        return
    
    # 1. TRENDS TAB
    if analysis_mode == "Trends":
        st.header("📊 Sentiment Timeline & Heat Map")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Calculate moving averages
            df['ma7'] = analyzer.calculate_moving_average(df['compound'], 7)
            df['ma30'] = analyzer.calculate_moving_average(df['compound'], 30)
            
            # Plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'], y=df['compound'],
                mode='markers', name='Daily Sentiment',
                marker=dict(size=8, color=df['compound'], colorscale='RdYlGn_r', showscale=True),
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Compound: %{y:.3f}<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'], y=df['ma7'],
                mode='lines', name='7-Day MA',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'], y=df['ma30'],
                mode='lines', name='30-Day MA',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="Sentiment Trend Over Time",
                xaxis_title="Date",
                yaxis_title="Sentiment (Compound)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("Current Sentiment", f"{df['compound'].iloc[-1]:.3f}")
            st.metric("7-Day Average", f"{df['compound'].tail(7).mean():.3f}")
            st.metric("Trend", "📈 Improving" if df['compound'].tail(7).mean() > df['compound'].iloc[-14:-7].mean() else "📉 Declining")
        
        # Spike detection
        spikes = analyzer.detect_rhetoric_spikes(df, threshold)
        
        if spikes:
            st.subheader("🚨 Detected Rhetoric Spikes")
            spike_df = pd.DataFrame(spikes)
            st.dataframe(spike_df[['date', 'compound', 'z_score', 'severity']].head(10))
    
    # 2. PHAROS (PREDICTIVE) TAB
    elif analysis_mode == "Pharos (Predictive)":
        st.header("🔮 Pharos: Predictive Escalation Mode")
        
        # Escalation prediction
        prediction = analyzer.predict_escalation(df, window=7)
        
        if prediction['status'] != 'insufficient_data':
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Trend Direction", prediction['trend'].upper())
            
            with col2:
                st.metric("Trend Strength", f"{prediction['strength']:.4f}")
            
            with col3:
                st.metric("Recent (7d) Mean", f"{prediction['recent_mean']:.4f}")
            
            with col4:
                alert_color = "🔴" if prediction['alert'] == 'escalation_detected' else "🟢"
                st.metric("Alert Status", f"{alert_color} {prediction['alert'].upper()}")
            
            # Projection
            if len(df) > 14:
                recent_trend = df.tail(14)['compound'].values
                future_steps = 7
                projected = []
                
                for i in range(future_steps):
                    # Simple linear extrapolation
                    slope = (recent_trend[-1] - recent_trend[0]) / len(recent_trend)
                    projected.append(recent_trend[-1] + slope * (i + 1))
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df['timestamp'].tail(14), y=recent_trend,
                    mode='lines+markers', name='Historical (14d)',
                    line=dict(color='blue')
                ))
                
                future_dates = [df['timestamp'].iloc[-1] + timedelta(days=i+1) for i in range(future_steps)]
                fig.add_trace(go.Scatter(
                    x=future_dates, y=projected,
                    mode='lines+markers', name='Projected (7d)',
                    line=dict(color='red', dash='dash')
                ))
                
                fig.update_layout(
                    title="Sentiment Projection (Linear)",
                    xaxis_title="Date",
                    yaxis_title="Sentiment",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need at least 14 days of data for predictions.")
    
    # 3. MORAL FOUNDATIONS TAB
    elif analysis_mode == "Foundations":
        st.header("⚖️ Moral Foundation Analysis")
        
        foundations = analyzer.analyze_moral_foundations(df)
        
        # Radar chart
        fig = go.Figure(data=go.Scatterpolar(
            r=list(foundations.values()),
            theta=list(foundations.keys()),
            fill='toself',
            name='Foundation Intensity'
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title="Moral Foundation Distribution",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Foundation details
        st.subheader("Foundation Details")
        for foundation, intensity in sorted(foundations.items(), key=lambda x: x[1], reverse=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{foundation}**")
            with col2:
                st.metric("Intensity", f"{intensity:.3f}")
    
    # 4. ALERTS TAB
    elif analysis_mode == "Alerts":
        st.header("🚨 Escalation Alerts & Monitoring")
        
        prediction = analyzer.predict_escalation(df, window=7)
        spikes = analyzer.detect_rhetoric_spikes(df, threshold)
        
        alert_level = "🔴 CRITICAL" if prediction.get('alert') == 'escalation_detected' else "🟢 NORMAL"
        st.warning(f"Current Alert Level: {alert_level}")
        
        if prediction['alert'] == 'escalation_detected':
            st.error(f"""
            **Escalation Detected!**
            - Trend: {prediction['trend']}
            - Strength: {prediction['strength']:.4f}
            - Recent sentiment mean: {prediction['recent_mean']:.4f}
            - Dehumanizing rhetoric may be increasing
            """)
        
        if spikes:
            st.subheader("🔥 High-Intensity Rhetoric Events")
            for i, spike in enumerate(spikes[:5]):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Event {i+1}**")
                with col2:
                    st.write(f"Z-Score: {spike['z_score']:.2f}")
                with col3:
                    st.write(f"Severity: {spike['severity'].upper()}")
                st.caption(f"Source: {spike['source']}")
                st.divider()
    
    # Footer
    st.markdown("---")
    st.caption("🔭 Beacon Dashboard | SimpleMem Rhetoric Monitoring | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
